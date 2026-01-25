from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/employee", tags=["Employee"])


@router.get("/dashboard")
def employee_dashboard(role: str = Header(...)):
    if role != "EMPLOYEE":
        raise HTTPException(403, "Access denied")
    return {"dashboard": "Employee Dashboard"}


@router.get("/manager/dashboard")
def manager_dashboard(role: str = Header(...)):
    if role != "MANAGER":
        raise HTTPException(403, "Access denied")
    return {"dashboard": "Manager Dashboard"}


@router.get("/admin/dashboard")
def admin_dashboard(role: str = Header(...)):
    if role not in ["ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(403, "Access denied")
    return {"dashboard": "Admin Portal"}
