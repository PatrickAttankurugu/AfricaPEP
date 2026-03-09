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

from africapep.config import settings
from africapep.api.routers import screen, pep, graph, search, health, countries

log = structlog.get_logger()

# ── Rate limiter ──
limiter = Limiter(key_func=get_remote_address)

tags_metadata = [
    {"name": "Health", "description": "System health and database connectivity checks"},
    {"name": "Screening", "description": "Screen names against the PEP database using fuzzy matching"},
    {"name": "Search", "description": "Full-text search across PEP profiles with filters"},
    {"name": "Countries", "description": "List supported African countries and coverage stats"},
    {"name": "PEP Profiles", "description": "Retrieve individual PEP profiles and details"},
    {"name": "Graph", "description": "Graph traversal for relationship exploration"},
]

is_production = settings.environment == "production"

app = FastAPI(
    title="AfricaPEP API",
    description=(
        "## African Politically Exposed Persons (PEP) Database\n\n"
        "Open-source PEP screening API covering all **54 African Union member states**. "
        "Built from scratch using web scrapers, NLP pipelines, and entity resolution — "
        "no third-party PEP data providers.\n\n"
        "### Key Features\n"
        "- **Name Screening** — Fuzzy match names against 1,500+ PEP profiles\n"
        "- **Batch Screening** — Screen up to 50 names in a single request\n"
        "- **Full-text Search** — Search by name, country, tier, and active status\n"
        "- **FATF-aligned Tiers** — Tier 1 (heads of state), Tier 2 (MPs/judges), Tier 3 (local officials)\n"
        "- **Dual Database** — Neo4j graph + PostgreSQL for fast search\n"
    ),
    version="1.0.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
    openapi_tags=tags_metadata,
    contact={"name": "Patrick Attankurugu", "url": "https://github.com/PatrickAttankurugu/AfricaPEP"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

app.state.limiter = limiter

# ── CORS (configurable via env) ──
_default_origins = ["https://pep.patrickaiafrica.com"]
if not is_production:
    _default_origins.append("http://localhost:3000")

if settings.cors_origins:
    cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
else:
    cors_origins = _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


# ── Request body size limit middleware ──
@app.middleware("http")
async def request_size_limit_middleware(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_request_size:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "detail": f"Request body too large. Maximum size is {settings.max_request_size} bytes.",
                "code": "REQUEST_TOO_LARGE",
            },
        )
    return await call_next(request)


# ── API key authentication middleware ──
# Public endpoints that don't require authentication
_PUBLIC_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json"}
# Read-only API paths open for the public demo frontend
_PUBLIC_API_PREFIXES = ("/api/v1/stats", "/api/v1/search", "/api/v1/pep/",
                        "/api/v1/screen", "/api/v1/countries")


@app.middleware("http")
async def api_key_auth_middleware(request: Request, call_next):
    if not settings.api_key_enabled or not settings.api_key:
        return await call_next(request)

    path = request.url.path
    if path in _PUBLIC_PATHS or request.method == "OPTIONS":
        return await call_next(request)
    if any(path.startswith(prefix) for prefix in _PUBLIC_API_PREFIXES):
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != settings.api_key:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": "Invalid or missing API key. Provide a valid key via the X-API-Key header.",
                "code": "UNAUTHORIZED",
            },
        )

    return await call_next(request)


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
        loc = " -> ".join(str(part) for part in first.get("loc", []))
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
    log.error("database_connection_error", error_type=type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database is temporarily unavailable. Please try again later.",
            "code": "DATABASE_UNAVAILABLE",
        },
    )


@app.exception_handler(InterfaceError)
async def db_interface_error_handler(request: Request, exc: InterfaceError):
    log.error("database_interface_error", error_type=type(exc).__name__)
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
    log.error("unhandled_exception", error_type=type(exc).__name__)
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
app.include_router(countries.router, prefix="/api/v1", tags=["Countries"])


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "AfricaPEP API",
        "version": "1.0.0",
        "docs": "/docs",
    }
