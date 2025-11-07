from fastapi import APIRouter, Depends, HTTPException, status
from app.core.logging import setup_logger
from app.repositories.user_repo import UserRepository
from app.core.deps import get_otp_service, get_user_repo
from app.schemas.otp import RequestOTPCreate, ResendOtpPayload, TokenResponse, VerifyOTPPayload
from app.services.otp_service import OTPService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

logger = setup_logger()


async def get_auth_service() -> AuthService:
    return AuthService()


@router.post("/request-otp")
async def request_otp(payload: RequestOTPCreate, otp_service: OTPService = Depends(get_otp_service)):
    """
    Generate and send OTP to contact (email or phone).
    """
    logger.info(f"Requesting OTP for contact: {payload.contact}")
    ok = await otp_service.generate_and_send(payload.contact)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    return {"message": f"OTP sent to {payload.contact}"}


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    payload: VerifyOTPPayload,
    otp_service: OTPService = Depends(get_otp_service),
    auth_service: AuthService = Depends(get_auth_service),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Verify OTP; if valid, get or create the user and return a JWT access token.

    Steps:
    1. Verify the OTP for the given contact.
    2. If OTP is valid:
       a. Fetch or create the user using the repository.
       b. Generate a JWT access token for authentication.
    3. Return the token in the response.

    :param payload: Contains `contact` (email or phone) and `otp`.
    :type payload: VerifyOTPPayload
    :param otp_service: Injected OTP service for verification.
    :param auth_svc: Injected AuthService for user management and token creation.
    :return: JWT access token wrapped in `TokenResponse`.
    :rtype: TokenResponse
    """
    try:
        # Log the OTP verification attempt
        logger.info(f"Verifying OTP for contact: {payload.contact}")

        # Step 1: Verify OTP
        valid = await otp_service.verify(payload.contact, payload.otp)
        if not valid:
            logger.warning(f"OTP verification failed for contact: {payload.contact}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )

        logger.info(f"OTP verified successfully for contact: {payload.contact}")

        # Step 2: Get or create user
        user, created = await user_repo.get_or_create_by_contact(payload.contact)

        if created:
            logger.info(f"New user created for contact: {payload.contact}, id: {user.id}")
        else:
            logger.info(f"Existing user fetched for contact: {payload.contact}, id: {user.id}")

        # Step 3: Issue JWT token
        token = auth_service.create_access_token(subject=str(user.id))
        logger.info(f"JWT token issued for user id: {user.id}")

        return TokenResponse(access_token=token)

    except HTTPException:
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.exception(f"Unexpected error verifying OTP for contact {payload.contact}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while verifying OTP"
        )


@router.post("/resend-otp")
async def resend_otp(
    payload: ResendOtpPayload,
    otp_service: OTPService = Depends(get_otp_service),
):
    """
    Resend a previously generated OTP to the user via email or phone.

    - Validates that at least one contact method (email or phone) is provided.
    - Delegates OTP fetching and sending to the OTPService.
    - Returns a success message if the resend operation succeeds.
    """
    contact = payload.email or payload.phone_number

    if not contact:
        logger.warning("Resend OTP request received without email or phone number.")
        raise HTTPException(
            status_code=400,
            detail="Either email or phone number is required"
        )

    try:
        logger.info(f"Attempting to resend OTP to contact: {contact}")
        success = await otp_service.fetch_and_send(contact)

        if success:
            logger.info(f"OTP resent successfully to {contact}")
            return {"message": "OTP resent successfully"}

        logger.error(f"Failed to resend OTP to {contact}")
        raise HTTPException(
            status_code=400,
            detail="Failed to resend OTP"
        )

    except HTTPException:
        # Let already-handled HTTP errors propagate cleanly
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while resending OTP to {contact}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while resending OTP"
        )
