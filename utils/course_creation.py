from fastapi import HTTPException, status, Header
from sqlalchemy import text
from sqlalchemy.orm import Session
from database_B import SessionLocal


from typing import Optional

def link_status(url: Optional[str]):
    return "Ready" if url and url.strip() else "Missing"


def manager_only(emp_code: str = Header(..., alias="X-Emp-Code")):
    db: Session = SessionLocal()
    try:
        query = text("""
            SELECT role
            FROM users
            WHERE emp_code = :emp_code
        """)
        result = db.execute(query, {"emp_code": emp_code}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        role = result[0].strip().lower()

        if role != "manager":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can perform this action"
            )
        return True
    finally:
        db.close()
