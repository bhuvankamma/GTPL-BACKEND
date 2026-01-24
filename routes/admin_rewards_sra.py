from fastapi import APIRouter
from schemas.schemas_bonus_inc import RewardAdminActionSchema
from crud.admin_rewards_crud import (
    list_pending_rewards,
    admin_action_reward
)

router = APIRouter(prefix="/admin/rewards", tags=["Admin Rewards"])

@router.get("/pending")
def get_pending_rewards():
    return list_pending_rewards()

@router.put("/{rec_id}/action")
def admin_action(rec_id: int, data: RewardAdminActionSchema):
    return admin_action_reward(rec_id, data)
