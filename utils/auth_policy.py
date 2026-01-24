# app/auth.py

from fastapi import Header, HTTPException

def get_current_user(
    x_emp_id: int = Header(...),
    x_role: str = Header(...)
):
    if x_role not in ("ADMIN", "MANAGER", "EMPLOYEE"):
        raise HTTPException(status_code=403, detail="Invalid role")

    return {
        "emp_id": x_emp_id,
        "role": x_role
    }
