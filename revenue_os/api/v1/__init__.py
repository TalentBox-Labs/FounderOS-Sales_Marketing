from fastapi import APIRouter, Depends

from revenue_os.auth import get_current_user
from revenue_os.api.v1.agents import router as agents_router
from revenue_os.api.v1.auth import router as auth_router
from revenue_os.api.v1.command_center import router as command_center_router
from revenue_os.api.v1.contacts import router as contacts_router
from revenue_os.api.v1.companies import router as companies_router
from revenue_os.api.v1.deals import router as deals_router
from revenue_os.api.v1.outreach import router as outreach_router
from revenue_os.api.v1.social import router as social_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(agents_router, dependencies=[Depends(get_current_user)])
v1_router.include_router(command_center_router, dependencies=[Depends(get_current_user)])
v1_router.include_router(contacts_router, dependencies=[Depends(get_current_user)])
v1_router.include_router(companies_router, dependencies=[Depends(get_current_user)])
v1_router.include_router(deals_router, dependencies=[Depends(get_current_user)])
v1_router.include_router(outreach_router, dependencies=[Depends(get_current_user)])
v1_router.include_router(social_router, dependencies=[Depends(get_current_user)])

__all__ = ["v1_router"]