from pydantic import BaseModel
from datetime import date
from typing import Optional
from pydantic import BaseModel

class ReimbursementCreate(BaseModel):
    emp_code: str
    expense_type: str 
    expense_date: date
    description: Optional[str] = None
    amount: float

class StatusUpdate(BaseModel):
    emp_code: str

class RejectReason(BaseModel):
    reason: str