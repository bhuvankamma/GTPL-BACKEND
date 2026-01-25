from fastapi import APIRouter
from app.services.dashboard_service import (
    get_dashboard_counts,
    get_weekly_attendance_trend,
    get_upcoming_hr_events
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview")
def dashboard_overview():
    return {
        "status": "success",
        "data": {
            **get_dashboard_counts(),
            "weekly_attendance_trend": get_weekly_attendance_trend(),
            "upcoming_hr_events": get_upcoming_hr_events()
        }
    }
