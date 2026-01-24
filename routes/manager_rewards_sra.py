from fastapi import APIRouter, Depends, HTTPException
from schemas.schemas_bonus_inc import RewardRecommendSchema
from crud.manager_rewards_crud import create_reward_recommendation
from utils.dependencies import get_current_user

router = APIRouter(prefix="/manager/rewards", tags=["Manager Rewards"])


@router.post("/recommend")
def recommend_reward(
    data: RewardRecommendSchema,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "MANAGER":
        raise HTTPException(status_code=403, detail="Only managers can recommend rewards")

    return create_reward_recommendation(
        data=data,
        manager_emp_code=current_user["emp_code"]
    )
