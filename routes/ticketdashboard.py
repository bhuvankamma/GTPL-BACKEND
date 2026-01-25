from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from database_sw import get_db
from crud.ticketdashboard import (
    get_summary,
    get_active_tickets,
    get_team_load,
    get_categories
)

router = APIRouter()

@router.get("/dashboard")
def dashboard(
    priority: str = Query(
        default="all",
        enum=["all", "high", "medium", "low"]
    ),
    search: str | None = None,
    db: Session = Depends(get_db),
):
    return {
        "summary": get_summary(db),
        "active_tickets": get_active_tickets(db, priority, search),
        "team_load": get_team_load(db),
        "categories": get_categories(db),
    }
