"""FastAPI application entry point with production hardening."""
import time

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import OperationalError, InterfaceError
import structlog

from africapep.api.routers import screen, pep, graph, search, health

log = structlog.get_logger()

# ── Rate limiter ──
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="AfricaPEP API",
    description=(
        "African Politically Exposed Persons (PEP) Database API. "
        "Provides screening, search, and graph traversal capabilities "
        "for KYC/AML compliance. All data sourced from official African "
        "government publications."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pep.patrickaiafrica.com",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ──
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    log.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


# ── Error handlers ──

# Rate limit exceeded -> 429
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded. Please slow down and retry shortly.",
            "code": "RATE_LIMIT_EXCEEDED",
        },
    )


# Pydantic validation errors -> 400 (instead of default 422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if errors:
        first = errors[0]
        loc = " -> ".join(str(l) for l in first.get("loc", []))
        msg = first.get("msg", "Invalid input")
        detail = f"{loc}: {msg}" if loc else msg
    else:
        detail = "Invalid request input"

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": detail,
            "code": "VALIDATION_ERROR",
        },
    )


# Database connection errors -> 503
@app.exception_handler(OperationalError)
async def db_operational_error_handler(request: Request, exc: OperationalError):
    log.error("database_connection_error", error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database is temporarily unavailable. Please try again later.",
            "code": "DATABASE_UNAVAILABLE",
        },
    )


@app.exception_handler(InterfaceError)
async def db_interface_error_handler(request: Request, exc: InterfaceError):
    log.error("database_interface_error", error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database is temporarily unavailable. Please try again later.",
            "code": "DATABASE_UNAVAILABLE",
        },
    )


# Catch-all for unhandled exceptions -> 500
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", error=str(exc), type=type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "code": "INTERNAL_ERROR",
        },
    )


# ── Mount routers ──
app.include_router(health.router, tags=["Health"])
app.include_router(screen.router, prefix="/api/v1", tags=["Screening"])
app.include_router(pep.router, prefix="/api/v1", tags=["PEP Profiles"])
app.include_router(graph.router, prefix="/api/v1", tags=["Graph"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "AfricaPEP API",
        "version": "1.0.0",
        "docs": "/docs",
    }
