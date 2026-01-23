from fastapi import APIRouter, Query
from crud.bonuses_crud import list_bonuses

router = APIRouter(prefix="/bonuses", tags=["Bonuses"])

@router.get("")
def get_bonuses(empCode: str = Query(...)):
    return {"bonuses": list_bonuses(empCode)}
