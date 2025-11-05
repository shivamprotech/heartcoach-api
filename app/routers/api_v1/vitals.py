from datetime import datetime
from typing import Optional
from uuid import UUID
import anyio
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.vitals import UserVital
from app.schemas.vitals import VitalCreate, VitalResponse, VitalUpdate
from app.services.vitals_service import VitalService
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

router = APIRouter(prefix="/api/v1/vitals", tags=["Vitals"])


vital_service = VitalService()


@router.post("/", response_model=VitalResponse, status_code=status.HTTP_201_CREATED)
async def record_vitals(
    request: Request,
    payload: VitalCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Record user vitals — partial entries allowed (e.g. only BP or HR).
    """
    user_id = getattr(request.state, "user_id", None)
    if not any([payload.systolic_bp, payload.diastolic_bp, payload.heart_rate, payload.spo2, payload.weight]):
        raise HTTPException(status_code=400, detail="At least one vital must be provided")

    new_vital = UserVital(
        user_id=user_id,
        systolic_bp=payload.systolic_bp,
        diastolic_bp=payload.diastolic_bp,
        heart_rate=payload.heart_rate,
        spo2=payload.spo2,
        weight=payload.weight,
        reading_time=payload.reading_time,
    )

    db.add(new_vital)
    await db.commit()
    await db.refresh(new_vital)
    return new_vital


@router.get("/me", response_model=list[VitalResponse])
async def get_my_vitals(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all vitals for the current user (for graph/trend view).
    """
    user_id = getattr(request.state, "user_id", None)
    result = await db.execute(
        select(UserVital).where(UserVital.user_id == user_id).order_by(UserVital.recorded_at.desc())
    )
    return result.scalars().all()


@router.put("/{vital_id}", response_model=VitalResponse)
async def update_vital(
    request: Request,
    vital_id: UUID,
    payload: VitalUpdate,
    db: AsyncSession = Depends(get_db),
):
    user_id = getattr(request.state, "user_id", None)
    updated_vital = await vital_service.update_vital(db, user_id, vital_id, payload.dict(exclude_unset=True))
    if not updated_vital:
        raise HTTPException(status_code=404, detail="Vital not found or not authorized")
    return updated_vital


@router.delete("/{vital_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vital(
    request: Request,
    vital_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    user_id = getattr(request.state, "user_id", None)
    deleted = await vital_service.delete_vital(db, user_id, vital_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Vital not found or not authorized")
    return None


# -----------------------
# Helper: Fetch vitals
# -----------------------
async def _fetch_vitals(db: AsyncSession, user_id: str, start: Optional[datetime], end: Optional[datetime]):
    q = select(UserVital).where(UserVital.user_id == user_id)
    if start:
        q = q.where(UserVital.recorded_at >= start)
    if end:
        q = q.where(UserVital.recorded_at <= end)
    q = q.order_by(UserVital.recorded_at.asc())
    res = await db.execute(q)
    return res.scalars().all()


# -----------------------
# Helper: Render vitals as table image
# -----------------------
def _render_table_image(df: pd.DataFrame, title: str = "Vitals Summary") -> bytes:
    """
    Render a Pandas DataFrame to a PNG table image.
    """
    display_df = df.copy()
    if "recorded_at" in display_df.columns:
        display_df["recorded_at"] = display_df["recorded_at"].dt.strftime("%Y-%m-%d %H:%M")

    # Adjust figure size dynamically
    rows, cols = display_df.shape
    row_height = 0.5
    col_width = 2.0
    fig_height = max(2.5, row_height * (rows + 1))
    fig_width = max(6, col_width * cols)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis('off')
    ax.set_title(title, fontsize=14, pad=12, fontweight="bold")

    # Build table
    table_data = display_df.fillna("").astype(str).values.tolist()
    col_labels = list(display_df.columns)

    table = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        loc='center',
        cellLoc='center',
        colLoc='center'
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)

    for i in range(len(col_labels)):
        table.auto_set_column_width(i)

    plt.tight_layout()

    # Save as bytes
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# -----------------------
# Endpoint: Export as PNG
# -----------------------
@router.get("/export", summary="Export vitals as PNG table")
async def export_vitals_png(
    request: Request,
    db: AsyncSession = Depends(get_db),
    start: Optional[datetime] = Query(None, description="Start datetime (ISO)"),
    end: Optional[datetime] = Query(None, description="End datetime (ISO)"),
    max_rows: int = Query(500, description="Max rows to export (safety limit)")
):
    """
    Returns a PNG image of the user's vitals in a tabular format.
    Optional query params:
    - `start` / `end`: ISO datetimes for filtering.
    - `max_rows`: limits results for safety.
    """
    user_id = getattr(request.state, "user_id", None)
    vitals = await _fetch_vitals(db, user_id, start, end)

    if not vitals:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No vitals found for the given range")

    rows = []
    for v in vitals[:max_rows]:
        rows.append({
            "Recorded At": v.recorded_at,
            "Time of Day": v.reading_time.value if getattr(v, "reading_time", None) else None,
            "Systolic BP": v.systolic_bp,
            "Diastolic BP": v.diastolic_bp,
            "Heart Rate": v.heart_rate,
            "SpO₂": v.spo2,
            "Weight": v.weight,
        })

    df = pd.DataFrame(rows)

    # Render in a thread (non-blocking)
    png_bytes = await anyio.to_thread.run_sync(_render_table_image, df, f"{user_id}'s Vitals")

    return StreamingResponse(BytesIO(png_bytes), media_type="image/png")

