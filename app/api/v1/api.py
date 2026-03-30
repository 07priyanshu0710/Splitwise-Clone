
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, groups, expenses, balances, settlements, reports

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(balances.router, prefix="/balances", tags=["balances"])
api_router.include_router(settlements.router, prefix="/settlements", tags=["settlements"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
