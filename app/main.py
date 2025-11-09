"""FastAPI application entrypoint."""

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import router as api_router
from app.api.dependencies import get_auth_dependency
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router.api_router, prefix=settings.api_v1_prefix)

templates = Jinja2Templates(directory="app/web/templates")
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Render the lightweight frontend."""

    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/healthz", tags=["health"])
def health_check() -> dict:
    """Simple health probe endpoint."""

    logger.debug("health_check_invoked")
    return {"status": "ok", "environment": settings.environment}


@app.get("/auth-check", tags=["health"], dependencies=[Depends(get_auth_dependency)])
def auth_check() -> dict:
    """Endpoint to verify API auth configuration."""

    return {"status": "authorized"}

