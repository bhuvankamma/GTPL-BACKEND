from pydantic import BaseModel, EmailStr
from typing import Optional

class AdminRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class CreateEmployee(BaseModel):
    full_name: str
    emp_code: str
    department: str
    role: str
    employee_type: str
    reporting_manager_emp_code: Optional[str] = None
    email: EmailStr
