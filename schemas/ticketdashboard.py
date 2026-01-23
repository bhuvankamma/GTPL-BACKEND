from typing import List
from pydantic import BaseModel

class Summary(BaseModel):
    open_tickets: int
    in_progress: int
    resolved_today: int
    sla_breached: int


class Ticket(BaseModel):
    ticket_id: str
    title: str
    priority: str
    assigned_to: str | None
    status: str


class TeamLoad(BaseModel):
    name: str
    load_percent: int


class Category(BaseModel):
    category: str
    count: int


class ResolvedDay(BaseModel):
    date: str
    resolved_count: int
