from pydantic import BaseModel
from typing import Optional

class CandidateCreate(BaseModel):
    full_name: str
    email: str
    mobile: str
    position: str
    technical_skill: bool
    communication_skill: bool
    technical_feedback: Optional[str] = None
    communication_feedback: Optional[str] = None
    overall_feedback: Optional[str] = None


class CandidateUpdate(BaseModel):
    technical_skill: Optional[bool]
    communication_skill: Optional[bool]
    technical_feedback: Optional[str]
    communication_feedback: Optional[str]
    overall_feedback: Optional[str]
    status: Optional[str]
