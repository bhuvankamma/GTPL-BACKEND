from pydantic import BaseModel, EmailStr
from typing import Optional

class CreateEmployee(BaseModel):
    full_name: str
    emp_code: str
    department: str
    role: str                  # ADMIN | MANAGER | EMPLOYEE
    employee_type: str         # CONTRACT | PERMANENT
    reporting_manager_emp_code: Optional[str] = None
    email: EmailStr
