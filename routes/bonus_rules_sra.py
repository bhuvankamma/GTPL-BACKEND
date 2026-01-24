from fastapi import APIRouter, Depends
from schemas.schemas_bonus_inc import BonusRuleCreate

from crud.bonus_rules_crud import (
    list_bonus_rules,
    create_bonus_rule,
    update_bonus_rule,
    delete_bonus_rule
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/bonus-rules", tags=["Bonus Rules"])


@router.get("/")
def get_bonus_rules(user=Depends(get_current_user)):
    return list_bonus_rules(user["emp_code"])


@router.post("/")
def add_bonus_rule(data: BonusRuleCreate, user=Depends(get_current_user)):
    return create_bonus_rule(data,user["emp_code"])


@router.put("/{rule_id}")
def edit_bonus_rule(data: BonusRuleCreate, rule_id: int, user=Depends(get_current_user)):
    return update_bonus_rule(rule_id, data, user["emp_code"])


@router.delete("/{rule_id}")
def remove_bonus_rule(rule_id: int,user=Depends(get_current_user)):
    return delete_bonus_rule(rule_id,user["emp_code"])
