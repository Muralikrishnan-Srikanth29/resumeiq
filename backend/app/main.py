from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.v1 import analysis_routes, jd_routes, misc_routes, resume_routes
from app.core.config import get_settings
from app.core.exceptions import ResumeIQError
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import limiter

settings = get_settings()
configure_logging(debug=settings.DEBUG)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ResumeIQ API starting | environment=%s", settings.ENVIRONMENT)
    yield
    logger.info("ResumeIQ API shutting down")


app = FastAPI(
    title="ResumeIQ API",
    description="AI-powered resume analysis with a deterministic rule engine and minimal-token AI layer.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(ResumeIQError)
async def domain_error_handler(request: Request, exc: ResumeIQError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please try again later."})


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


app.include_router(resume_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(jd_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(analysis_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(misc_routes.router, prefix=settings.API_V1_PREFIX)
