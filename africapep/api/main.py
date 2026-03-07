"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from africapep.api.routers import screen, pep, graph, search, health

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
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
