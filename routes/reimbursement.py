from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from database_sw import get_db
from schemas.reimbursement import ReimbursementCreate
from crud.reimbursement import (
    create_reimbursement,
    upload_files,
    update_status,
    get_dashboard_counts
)

router = APIRouter()



# =========================
# EMPLOYEE
# =========================
@router.post("/employee/reimbursements")
def create_reim(
    data: ReimbursementCreate,
    db: Session = Depends(get_db)
):
    return create_reimbursement(db, data)

@router.post("/employee/reimbursements/{rid}/attachments")
def upload(
    rid: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    return upload_files(db, rid, files)


# =========================
# MANAGER
# =========================
@router.patch("/manager/approve/{rid}")
def manager_approve(rid: int, db: Session = Depends(get_db)):
    update_status(
        db=db,
        rid=rid,
        status="MANAGER_REJECTED",
        next_level=None,
        action_by_emp_code="MGR001",   # from login
        sender_role="MANAGER",
        reason="Exceeded limit"
    )


@router.patch("/manager/reject/{rid}")
def manager_reject(
    rid: int,
    reason: str,
    manager_emp_code: str, 
    db: Session = Depends(get_db),
):
    return update_status(
        db=db,
        rid=rid,
        status="MANAGER_REJECTED",
        next_level=None,
        action_by_emp_code=manager_emp_code,
        sender_role="MANAGER",
        reason=reason
    )



# =========================
# HR / ADMIN
# =========================
@router.patch("/hr/approve/{rid}")
def hr_approve(rid: int, db: Session = Depends(get_db)):
    return update_status(
        db=db,
        rid=rid,
        status="HR_APPROVED",
        next_level=None,
        sender_role="HR"
    )


@router.patch("/hr/reject/{rid}")
def hr_reject(
    rid: int,
    reason: str,
    db: Session = Depends(get_db),
):
    return update_status(
        db=db,
        rid=rid,
        status="HR_REJECTED",
        next_level=None,
        sender_role="HR",
        reason=reason
    )



@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    return get_dashboard_counts(db)

