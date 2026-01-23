from pydantic import BaseModel
from typing import Optional, Literal
from decimal import Decimal
from datetime import datetime, date

# =====================================================
# BONUS RULES
# =====================================================
class BonusRuleCreate(BaseModel):
    bonusCode: str
    bonusName: str
    frequency: str
    percentageOfCtc: Optional[Decimal] = None
    fixedAmount: Optional[Decimal] = None
    isActive: bool = True


class BonusRuleUpdate(BonusRuleCreate):
    pass


# =====================================================
# BONUSES
# =====================================================
class BonusCreate(BaseModel):
    empCode: str
    year: int
    status: str
    bonusCode: Optional[str] = None
    bonusType: Optional[str] = None
    amount: Optional[Decimal] = None
    paymentDate: Optional[date] = None


# =====================================================
# INCENTIVE RULES
# =====================================================
class IncentiveRuleCreate(BaseModel):
    incentiveCode: str
    incentiveName: str
    formulaType: str
    percentageValue: Optional[Decimal] = None
    perUnitAmount: Optional[Decimal] = None
    fixedAmount: Optional[Decimal] = None
    isActive: bool = True


# =====================================================
# INCENTIVES
# =====================================================
class IncentiveCreate(BaseModel):
    empCode: str
    status: str
    incentiveCode: Optional[str] = None
    incentiveType: Optional[str] = None
    metricValue: Optional[Decimal] = None
    targetValue: Optional[Decimal] = None
    period: Optional[str] = None
    amount: Optional[Decimal] = None


# =====================================================
# REWARD FLOW (BONUS + INCENTIVE)
# ROLE-BASED (NO ID-BASED LOGIC)
# =====================================================

# -------- Manager recommends reward --------
class RewardRecommendSchema(BaseModel):
    emp_code: str                                  # Employee who gets reward
    reward_type: Literal["BONUS", "INCENTIVE"]
    reward_rule_id: int                            # bonus_rules.id / incentive_rules.id
    amount: Decimal
    note: Optional[str] = None


# -------- Admin approves / rejects --------
class RewardAdminActionSchema(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    note: Optional[str] = None


# -------- Read-only response (Employee/Admin) --------
class RewardResponseSchema(BaseModel):
    id: int
    emp_code: str
    reward_type: str
    reward_rule_id: int
    recommended_by: str
    recommended_amount: Decimal
    status: str
    admin_action_by: Optional[str]
    admin_action_note: Optional[str]
    created_at: datetime
    admin_action_at: Optional[datetime]

    model_config = {"from_attributes": True}
