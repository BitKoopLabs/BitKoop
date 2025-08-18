import os
from datetime import (
    UTC,
    datetime,
)
from contextlib import asynccontextmanager
from fastapi import (
    FastAPI,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from .routes import (
    coupons,
    test,
    weights,
    info,
)
from . import (
    __version__ as version,
    APP_TITLE,
)
from .database.database import (
    get_db,
)
from . import (
    dependencies,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup, set a non-empty sync_progress to block submissions until next sync completes
    db_gen = get_db()
    db = next(db_gen)
    try:
        dynamic_config_service = dependencies.get_dynamic_config_service(db=db)
        sync_progress = dynamic_config_service.get_sync_progress()
        if not sync_progress:
            dynamic_config_service.set_sync_progress(
                {
                    "status": "pending",
                    "started_at": datetime.now(UTC).isoformat(),
                }
            )
    finally:
        # Ensure generator finalization (commit/close or rollback)
        try:
            next(db_gen)
        except StopIteration:
            pass
    yield

ENV = os.getenv("ENV")

app = FastAPI(
    title=APP_TITLE,
    description="API for validating coupon codes and managing miner sessions",
    version=version,
    lifespan=lifespan,
    docs_url=None if ENV == "prod" else "/docs",
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    coupons.router,
    prefix="/coupons",
    tags=["coupons"],
)
if os.getenv("ENV") == "test":
    app.include_router(
        test.router,
        prefix="/test",
        tags=["test"],
    )

    app.include_router(
        weights.router,
        prefix="/weights",
        tags=["weights"],
    )

app.include_router(
    info.router,
    prefix="/info",
    tags=["info"],
)
