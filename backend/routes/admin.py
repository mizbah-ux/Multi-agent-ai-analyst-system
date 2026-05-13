from fastapi import APIRouter, Depends
from auth.dependencies import require_role

router = APIRouter()

@router.get("/admin/dashboard")
def admin_dashboard(user=Depends(require_role("admin"))):
    return {"message": "Welcome Admin"}