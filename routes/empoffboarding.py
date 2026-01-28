from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas import empoffboarding as schemas
from crud import empoffboarding as crud

from utils.empoffdependencies import (
    get_db,
    get_current_employee,
    get_current_manager,
    get_current_hr,
    get_current_emp_or_manager
)

router = APIRouter(prefix="/offboarding", tags=["Offboarding"])


# ==================================================
# EMPLOYEE START OFFBOARDING
# ==================================================
@router.post("/start")
def start_offboarding(
    manager_emp_code: str,
    data: schemas.ResignationCreate,
    user=Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    return crud.employee_start_offboarding(
        db,
        user.emp_code,
        manager_emp_code,
        data
    )


# ==================================================
# MANAGER START OFFBOARDING (HR APPROVAL)
# ==================================================
@router.post("/manager/start")
def manager_start_offboarding(
    data: schemas.StartOffboardingSchema,
    user=Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    return crud.manager_start_offboarding(
        db=db,
        manager_emp_code=user.emp_code,
        data=data
    )


# ==================================================
# MANAGER DECISION (EMPLOYEE FLOW)
# ==================================================
@router.post("/{req_id}/manager-decision")
def manager_decision(
    req_id: int,
    data: schemas.DecisionSchema,
    user=Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    return crud.manager_decision(
        db,
        req_id,
        user.emp_code,
        data.approve,
        data.reason
    )


# ==================================================
# HANDOVER
# ==================================================
@router.post("/{req_id}/handover")
def handover(
    req_id: int,
    data: schemas.HandoverSchema,
    user=Depends(get_current_emp_or_manager),
    db: Session = Depends(get_db)
):
    return crud.save_handover(
        db,
        req_id,
        user.emp_code,
        data
    )


# ==================================================
# ASSETS
# ==================================================
@router.post("/{req_id}/assets")
def assets(
    req_id: int,
    data: schemas.AssetSchema,
    user=Depends(get_current_emp_or_manager),
    db: Session = Depends(get_db)
):
    return crud.confirm_assets(
        db,
        req_id,
        user.emp_code,
        data
    )


# ==================================================
# FINAL DOCS
# ==================================================
@router.post("/{req_id}/final-docs")
def final_docs(
    req_id: int,
    data: schemas.FinalDocsSchema,
    user=Depends(get_current_emp_or_manager),
    db: Session = Depends(get_db)
):
    return crud.submit_final_docs(
        db,
        req_id,
        user.emp_code,
        data.personal_email
    )


# ==================================================
# HR / ADMIN DECISION
# ==================================================
@router.post("/{req_id}/hr-decision")
def hr_decision(
    req_id: int,
    data: schemas.DecisionSchema,
    user=Depends(get_current_hr),
    db: Session = Depends(get_db)
):
    return crud.hr_decision(
        db,
        req_id,
        user.emp_code,
        data.approve,
        data.reason
    )
