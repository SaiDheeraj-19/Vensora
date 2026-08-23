from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from app.modules.telephony.router import router as telephony_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(telephony_router, prefix="/telephony", tags=["telephony"])
