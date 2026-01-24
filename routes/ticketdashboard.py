from fastapi import APIRouter, Query
from database_sw import get_connection
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
        description="Filter tickets by priority",
        enum=["all", "high", "medium", "low"]
    ),
    search: str | None = Query(
        default=None,
        description="Search tickets by title"
    )
):
    conn = get_connection()

    return {
        "summary": get_summary(conn),
        "active_tickets": get_active_tickets(conn, priority, search),
        "team_load": get_team_load(conn),
        "categories": get_categories(conn)
    }
