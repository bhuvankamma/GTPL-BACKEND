# app/routers/payroll.py
from fastapi import APIRouter, Depends
from schemas.schemas_payslip import *
from crud import payslip_crud
from utils.dependencies import get_current_user

router = APIRouter(prefix="/payroll", tags=["Payroll"])


@router.post("/select-tax-regime")
def select_tax(
    payload: SelectTaxRegime,
    current_user = Depends(get_current_user)
):
    return payslip_crud.action_select_tax_regime(
        payload.dict(),
        current_user
    )


@router.post("/generate")
def generate(
    payload: GeneratePayslip,
    current_user = Depends(get_current_user)
):
    return payslip_crud.action_generate(
        payload.dict(),
        current_user
    )


@router.post("/generate-bulk")
def generate_bulk(
    payload: BulkGenerate,
    current_user = Depends(get_current_user)
):
    return payslip_crud.action_generate_bulk(
        payload.dict(),
        current_user
    )


@router.post("/request")
def request_payslip(
    payload: GeneratePayslip,
    current_user = Depends(get_current_user)
):
    return payslip_crud.action_request_payslip(
        payload.dict(),
        current_user
    )


@router.post("/approve")
def approve(
    payload: GeneratePayslip,
    current_user = Depends(get_current_user)
):
    return payslip_crud.action_approve_payslip_request(
        payload.dict(),
        current_user
    )


@router.post("/reject")
def reject(
    payload: GeneratePayslip,
    current_user = Depends(get_current_user)
):
    return payslip_crud.action_reject_payslip_request(
        payload.dict(),
        current_user
    )


@router.post("/form16/part-b")
def form16(
    payload: Form16Request,
    current_user = Depends(get_current_user)
):
    return payslip_crud.action_generate_form16_part_b(
        payload.dict(),
        current_user
    )
