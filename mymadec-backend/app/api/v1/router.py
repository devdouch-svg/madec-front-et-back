from fastapi import APIRouter

from app.api.v1 import (
    auth,
    annuaire,
    banners,
    catalog,
    dashboard,
    notifications,
    orders,
    payment_methods,
    products,
    settings,
    sync,
    users,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(annuaire.router)
api_router.include_router(products.router)
api_router.include_router(catalog.router)
api_router.include_router(orders.router)
api_router.include_router(sync.router)
api_router.include_router(payment_methods.router)
api_router.include_router(settings.router)
api_router.include_router(notifications.router)
api_router.include_router(banners.router)
api_router.include_router(dashboard.router)
