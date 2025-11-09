"""API router aggregator."""

from fastapi import APIRouter

from app.api.routes import critical_css, images

api_router = APIRouter()
api_router.include_router(images.router)
api_router.include_router(critical_css.router)

