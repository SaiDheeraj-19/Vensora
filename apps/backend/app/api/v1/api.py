from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.health import router as health_router
from app.api.v1.calls import router as calls_router
from app.api.v1.crm import router as crm_router
from app.api.v1.dev import router as dev_router
from app.modules.telephony.router import router as telephony_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(calls_router, prefix="/calls", tags=["calls"])
api_router.include_router(crm_router, prefix="/crm", tags=["crm"])
api_router.include_router(dev_router, prefix="/dev", tags=["dev"])
api_router.include_router(telephony_router, prefix="/telephony", tags=["telephony"])
