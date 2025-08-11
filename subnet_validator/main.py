import os
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

app = FastAPI(
    title=APP_TITLE,
    description="API for validating coupon codes and managing miner sessions",
    version=version,
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
