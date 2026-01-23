from fastapi import APIRouter, Depends, HTTPException
from schemas.schemas_bonus_inc import BonusRuleCreate, IncentiveRuleCreate
from crud.bonus_rules_crud import create_bonus_rule, list_bonus_rules
from crud.incentive_rules_crud import create_incentive_rule, list_incentive_rules
from utils.dependencies import get_current_user

# def get_current_user():
#   return {"emp_code": "EMP123", "role": "MANAGER"}

router = APIRouter(prefix="/manager/rules", tags=["Manager Rules"])

@router.post("/bonus")
def add_bonus_rule(data: BonusRuleCreate, user=Depends(get_current_user)):
    return create_bonus_rule(data, user["emp_code"])

@router.get("/bonus")
def get_bonus_rules(user=Depends(get_current_user)):
    return list_bonus_rules(user["emp_code"])


@router.post("/incentive")
def add_incentive_rule(data: IncentiveRuleCreate, user=Depends(get_current_user)):
    return create_incentive_rule(data, user["emp_code"])

@router.get("/incentive")
def get_incentive_rules(user=Depends(get_current_user)):
    return list_incentive_rules(user["emp_code"])
