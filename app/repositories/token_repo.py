from app.models.user import RefreshToken


async def create_refresh_token(db, user_id: int, jti: str, expires_at, device_info: str | None):
    token = RefreshToken(
        user_id=user_id,
        jti=jti,
        expires_at=expires_at,
        device_info=device_info
    )
    db.add(token)
    await db.commit()
    return token
