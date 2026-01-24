from fastapi import APIRouter, Depends, HTTPException, status
from crud.employee_rewards_crud import (
    get_employee_rewards,
    get_employee_reward_insights
)
from utils.dependencies import get_current_user

# 🔐 Mock auth (replace with JWT later)
# def get_current_user():
#    return {
#        "emp_code": "EMP001",   # ✅ MUST MATCH DB
#        "role": "EMPLOYEE"
#    }

router = APIRouter(
    prefix="/employee/rewards",
    tags=["Employee Rewards"]
)

# =====================================================
# 1️⃣ Employee Rewards List (Table / Popup)
# =====================================================
@router.get("/")
def employee_rewards(
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "EMPLOYEE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can view their rewards"
        )

    return get_employee_rewards(current_user["emp_code"])


# =====================================================
# 2️⃣ Employee Earnings Insights (Charts)
# =====================================================
@router.get("/insights")
def employee_reward_insights(
    view: str = "category",   # category | monthly
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "EMPLOYEE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can view insights"
        )

    return get_employee_reward_insights(
        current_user["emp_code"],
        view
    )
