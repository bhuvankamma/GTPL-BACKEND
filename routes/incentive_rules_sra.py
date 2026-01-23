from fastapi import APIRouter, Depends, HTTPException
from crud.incentive_rules_crud import (
    create_incentive_rule,
    list_incentive_rules,
    deactivate_incentive_rule
)
from utils.dependencies import get_current_user
from schemas.schemas_bonus_inc import IncentiveRuleCreate
# def get_current_user():
#    return {
#        "emp_code": "EMP001",   # ✅ MUST MATCH DB
#        "role": "EMPLOYEE"
#    }

router = APIRouter(prefix="/incentive-rules", tags=["Incentive Rules"])


# --------------------------------------------------
# GET – List incentive rules
# --------------------------------------------------
@router.get("")
def get_incentive_rules(user=Depends(get_current_user)):
    return list_incentive_rules(user["emp_code"])


# --------------------------------------------------
# POST – Create incentive rule
# --------------------------------------------------
@router.post("/incentive-rules")
def add_incentive_rule(
    data: IncentiveRuleCreate,
    user = Depends(get_current_user)
):
    return create_incentive_rule(data, user["emp_code"])


# --------------------------------------------------
# DELETE – Deactivate incentive rule
# --------------------------------------------------
@router.delete("/{rule_id}")
def remove_incentive_rule(rule_id: int, user=Depends(get_current_user)):
    if user["role"] not in ["MANAGER", "ADMIN"]:
        raise HTTPException(403, "Not authorized")

    return deactivate_incentive_rule(rule_id, user["emp_code"])
