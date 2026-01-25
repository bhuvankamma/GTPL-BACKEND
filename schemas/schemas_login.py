from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal


# ========= AUTH =========

class SuperAdminRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class SetPasswordSchema(BaseModel):
    token: str
    new_password: str
    confirm_password: str


# ========= EMPLOYEE =========

class CreateEmployee(BaseModel):
    full_name: str
    emp_code: str = Field(..., pattern=r"^EMP\d{3}$")
    department: str
    role: Literal["ADMIN", "MANAGER", "EMPLOYEE"]
    employee_type: Literal["FULL_TIME", "CONTRACT", "TEMPORARY"]
    email: EmailStr
    reporting_manager_emp_code: Optional[str] = Field(
        default=None,
        pattern=r"^EMP\d{3}$"
    )
