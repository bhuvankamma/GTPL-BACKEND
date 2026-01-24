from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database_su import get_db

from models.profile_employee import Employee
from models.profile_statutory import EmployeeStatutory
from models.profile_reporting import EmployeeReportingHierarchy
from models.profile_emergency import EmployeeEmergencyContact

from schemas.profile_admin_basic import AdminEmployeeBasicUpdate
from schemas.profile_admin_bank import AdminBankStatutoryUpdate

router = APIRouter(
    prefix="/admin/employee",
    tags=["Admin"],
)

# ==================================================
# VIEW EMPLOYEE PROFILE (ADMIN)
# ==================================================
@router.get("/{emp_code}/profile", status_code=status.HTTP_200_OK)
def admin_view_profile(
    emp_code: str,
    db: Session = Depends(get_db),
):
    emp = db.query(Employee).filter(Employee.emp_code == emp_code).first()
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    statutory = (
        db.query(EmployeeStatutory)
        .filter(EmployeeStatutory.emp_code == emp_code)
        .first()
    )

    reporting = (
        db.query(EmployeeReportingHierarchy)
        .filter(EmployeeReportingHierarchy.emp_code == emp_code)
        .all()
    )

    emergency = (
        db.query(EmployeeEmergencyContact)
        .filter(EmployeeEmergencyContact.emp_code == emp_code)
        .all()
    )

    return {
        "basic_information": emp,
        "organization_details": emp,
        "bank_and_statutory": statutory,
        "reporting_management": reporting,
        "emergency_contacts": emergency,
    }

# ==================================================
# UPDATE BASIC / ORGANIZATION DETAILS (ADMIN)
# ==================================================
@router.put("/{emp_code}/basic-information", status_code=status.HTTP_200_OK)
def admin_update_basic(
    emp_code: str,
    payload: AdminEmployeeBasicUpdate,
    db: Session = Depends(get_db),
):
    emp = db.query(Employee).filter(Employee.emp_code == emp_code).first()
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    try:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(emp, key, value)

        db.commit()
        db.refresh(emp)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employee details",
        )

    return {"message": "Employee details updated successfully"}

# ==================================================
# UPDATE BANK & STATUTORY DETAILS (ADMIN)
# ==================================================
@router.put("/{emp_code}/bank-statutory", status_code=status.HTTP_200_OK)
def admin_update_bank_statutory(
    emp_code: str,
    payload: AdminBankStatutoryUpdate,
    db: Session = Depends(get_db),
):
    emp = db.query(Employee).filter(Employee.emp_code == emp_code).first()
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    try:
        stat = (
            db.query(EmployeeStatutory)
            .filter(EmployeeStatutory.emp_code == emp_code)
            .first()
        )

        if not stat:
            stat = EmployeeStatutory(emp_code=emp_code)
            db.add(stat)

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(stat, key, value)

        db.commit()
        db.refresh(stat)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bank & statutory details",
        )

    return {"message": "Bank & statutory details updated successfully"}
