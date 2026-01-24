from fastapi import APIRouter, Query
from crud.incentives_crud import list_incentives

router = APIRouter(prefix="/incentives", tags=["Incentives"])

@router.get("")
def get_incentives(empCode: str = Query(...)):
    return {"incentives": list_incentives(empCode)}
