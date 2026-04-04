"""GeoHub Developer API — open source geospatial tool registry."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hub.config import Settings
from hub.registry import registry
from hub.routers import tools


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: discover tools
    count = registry.discover(settings.tools_dir)
    print(f"GeoHub: Discovered {count} tool(s)")
    yield


settings = Settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Open source geospatial tool registry and execution API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tools.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": settings.version,
        "tools_loaded": len(registry.list_tools()),
    }
