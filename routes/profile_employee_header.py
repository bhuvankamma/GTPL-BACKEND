from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database_su import get_db
from models.profile_employee import Employee
from schemas.profile_employee_header import EmployeeHeaderResponse

router = APIRouter(
    prefix="/employee",
    tags=["Employee"],
)

@router.get(
    "/header",
    response_model=EmployeeHeaderResponse,
    summary="Get Employee Header Card Details",
)
def get_employee_header(
    emp_code: str,   # query param ?emp_code=EMP002
    db: Session = Depends(get_db),
):
    emp = db.query(Employee).filter(Employee.emp_code == emp_code).first()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return {
        "emp_code": emp.emp_code,
        "full_name": f"{emp.first_name or ''} {emp.last_name or ''}".strip(),
        "designation": emp.designation,
        "status": emp.status,
        "is_active": bool(emp.is_active),
        "date_of_joining": emp.date_of_joining,
        "profile_photo": emp.profile_photo,
    }
