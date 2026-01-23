from pydantic import BaseModel
from typing import Optional
from datetime import date


class EmployeeHeaderResponse(BaseModel):
    emp_code: str
    full_name: str
    designation: Optional[str]
    status: Optional[str]
    is_active: bool
    date_of_joining: Optional[date]
    profile_photo: Optional[str]

    model_config = {
        "from_attributes": True
    }
