from pydantic import BaseModel

class AssignmentCreate(BaseModel):
    device_id: int
    applies_to: str
    location_context: str | None = None
    access_schedule: str


class AssignmentResponse(AssignmentCreate):
    id: int

    class Config:
        from_attributes = True
