from pathlib import Path
from typing import (
    Annotated,
)
from datetime import (
    timedelta,
)

from fastapi import (
    Depends,
)

from subnet_validator.database.entities import Site
from subnet_validator.services.category_service import CategoryService
from subnet_validator.services.coupon_validator import CouponValidator
from subnet_validator.services.playwright_coupon_validator import PlaywrightCouponValidator
from subnet_validator.services.validator_sync_offset_service import (
    ValidatorSyncOffsetService,
)

from .services.coupon_service import (
    CouponService,
)

from .services.weight_calculator_service import (
    WeightCalculatorService,
)

from .services.metagraph_service import (
    MetagraphService,
)

from .services.dynamic_config_service import (
    DynamicConfigService,
)

from .database.database import (
    get_db,
)
from .settings import (
    Settings,
)
from sqlalchemy.orm import (
    Session,
)


def get_settings():
    return Settings()


def get_metagraph_service(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    return MetagraphService(db)



def get_dynamic_config_service(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    return DynamicConfigService(db)


def get_category_service(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    return CategoryService(db)


def get_coupon_service(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    settings: Annotated[
        Settings,
        Depends(get_settings),
    ],
    metagraph_service: Annotated[
        MetagraphService,
        Depends(get_metagraph_service),
    ],
    dynamic_config_service: Annotated[
        DynamicConfigService,
        Depends(get_dynamic_config_service),
    ],
):
    return CouponService(
        db,
        metagraph_service,
        dynamic_config_service,
        settings.max_coupons_per_site,
        settings.recheck_interval,
        settings.resubmit_interval,
        settings.submit_window,
    )


def get_validator_sync_offset_service(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    return ValidatorSyncOffsetService(db)


def get_weight_calculator_service(
    settings: Annotated[
        Settings,
        Depends(get_settings),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    return WeightCalculatorService(
        db=db,
        coupon_weight=settings.coupon_weight,
        container_weight=settings.container_weight,
        delta_points=settings.delta_points,
    )


def get_coupon_validator(site: Site, settings: Annotated[Settings, Depends(get_settings)]) -> PlaywrightCouponValidator:
    if settings.env == "production":
        return PlaywrightCouponValidator(
            site=site,
            path=Path.cwd() / "coupon_validation" / "index.js",
        )
    else: 
        return CouponValidator(site=site)