from fastapi import APIRouter

router = APIRouter()

@router.get("/employees/{employee_code}/id-card")
def get_employee_id_card(employee_code: str):
    return {
        "message": f"ID card API called for {employee_code}",
        "status": "NOT_IMPLEMENTED"
    }
