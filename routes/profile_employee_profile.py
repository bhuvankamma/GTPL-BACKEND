from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database_su import get_db

from models.profile_employee import Employee
from models.profile_statutory import EmployeeStatutory
from models.profile_reporting import EmployeeReportingHierarchy
from models.profile_emergency import EmployeeEmergencyContact

from schemas.profile_employee_response import EmployeeProfileResponse
from schemas.profile_employee import EmployeeBasicUpdate

router = APIRouter(
    prefix="/employee",
    tags=["Employee"],
)

# ==================================================
# VIEW EMPLOYEE PROFILE
# ==================================================
@router.get(
    "/profile",
    response_model=EmployeeProfileResponse,
    summary="Employee View Profile",
)
def employee_view_profile(
    emp_code: str,   # query param ?emp_code=EMP001
    db: Session = Depends(get_db),
):
    emp = db.query(Employee).filter_by(emp_code=emp_code).first()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return {
        # REQUIRED BY RESPONSE MODEL
        "basic_information": emp,
        "organization_details": emp,

        # OPTIONAL SINGLE OBJECT
        "bank_and_statutory": (
            db.query(EmployeeStatutory)
            .filter_by(emp_code=emp_code)
            .first()
        ),

        # LISTS → MUST ALWAYS EXIST
        "reporting_management": (
            db.query(EmployeeReportingHierarchy)
            .filter_by(emp_code=emp_code)
            .all()
        ),

        "emergency_contacts": (
            db.query(EmployeeEmergencyContact)
            .filter_by(emp_code=emp_code)
            .all()
        ),
    }


# ==================================================
# UPDATE BASIC INFORMATION (EMPLOYEE EDITABLE)
# ==================================================
@router.put(
    "/profile/basic-information",
    summary="Employee Update Basic Information",
)
def employee_update_basic(
    emp_code: str,   # query param
    payload: EmployeeBasicUpdate,
    db: Session = Depends(get_db),
):
    emp = db.query(Employee).filter_by(emp_code=emp_code).first()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(emp, key, value)

    db.commit()
    return {"message": "Employee basic information updated successfully"}
