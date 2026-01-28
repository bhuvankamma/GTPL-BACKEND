from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database_sw import get_db
from models.empoffboarding import User, Employee


# ==================================================
# COMMON USER FETCH (INTERNAL)
# ==================================================
def _get_active_user(
    db: Session,
    emp_code: str,
):
    user = (
        db.query(User)
        .join(Employee, Employee.emp_code == User.emp_code)
        .filter(
            User.emp_code == emp_code,
            func.lower(User.status) == "active",
            func.lower(Employee.status) == "active",
        )
        .first()
    )

    return user


# ==================================================
# EMPLOYEE AUTH
# ==================================================
def get_current_employee(
    emp_code: str = Header(..., alias="emp-code"),
    db: Session = Depends(get_db),
):
    user = _get_active_user(db, emp_code)

    if not user or user.role != "EMPLOYEE":
        raise HTTPException(
            status_code=403,
            detail="EMPLOYEE not found or inactive"
        )

    return user


# ==================================================
# MANAGER AUTH
# ==================================================
def get_current_manager(
    emp_code: str = Header(..., alias="emp-code"),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        User.emp_code == emp_code,
        func.lower(User.role) == "manager",
        func.lower(User.status) == "active"
    ).first()

    if not user:
        raise HTTPException(
            status_code=403,
            detail="MANAGER not found or inactive"
        )

    return user


# ==================================================
# HR OR ADMIN AUTH
# ==================================================
def get_current_hr(
    emp_code: str = Header(..., alias="emp-code"),
    db: Session = Depends(get_db),
):
    user = _get_active_user(db, emp_code)

    if not user or user.role not in ("HR", "ADMIN"):
        raise HTTPException(
            status_code=403,
            detail="HR or ADMIN not found or inactive"
        )

    return user

def get_current_emp_or_manager(
    emp_code: str = Header(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        User.emp_code == emp_code,
        User.role.in_(["EMPLOYEE", "MANAGER"]),
        User.status == "ACTIVE"
    ).first()

    if not user:
        raise HTTPException(
            status_code=403,
            detail="EMPLOYEE or MANAGER access required"
        )

    return user
