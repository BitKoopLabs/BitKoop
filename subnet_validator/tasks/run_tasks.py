import asyncio
import time

from fiber import (
    SubstrateInterface,
)
from subnet_validator.services.coupon_service import (
    CouponService,
)
from subnet_validator.services.validator_sync_offset_service import (
    ValidatorSyncOffsetService,
)
from subnet_validator.services.weight_calculator_service import (
    WeightCalculatorService,
)
from subnet_validator.services.metagraph_service import (
    MetagraphService,
)
from subnet_validator.settings import (
    Settings,
)
from subnet_validator.tasks.validate_coupons import (
    validate_pending_coupons,
    validate_outdated_coupon,
)
from subnet_validator.tasks.sync_coupons import (
    sync_coupons,
)
from subnet_validator.tasks.sync_sites import sync_sites
from subnet_validator.tasks.sync_categories import sync_categories
from subnet_validator.tasks.sync_metagraph_nodes import (
    sync_metagraph,
)
from subnet_validator.tasks.set_weights import (
    set_weights,
)
from subnet_validator.dependencies import (
    get_dynamic_config_service,
    get_settings,
    get_coupon_service,
    get_validator_sync_offset_service,
    get_weight_calculator_service,
    get_metagraph_service,
)
from subnet_validator.database.database import (
    get_db,
)
from fiber.chain import (
    interface,
)
from fiber.logging_utils import (
    get_logger,
)

logger = get_logger(__name__)


async def run_tasks_in_order(
    settings: Settings,
    substrate: SubstrateInterface,
    coupon_service: CouponService,
    validator_sync_offset_service: ValidatorSyncOffsetService,
    metagraph_service: MetagraphService,
    weight_calculator: WeightCalculatorService,
    dynamic_config_service,
):
    """
    Run tasks sequentially in the required order, respecting their own intervals:
    1) Sync metagraph
    2) Sync sites
    3) Sync categories
    4) Sync coupons
    5) Validate coupons (pending + outdated)
    6) Set weights
    """
    # Track last-run timestamps per task (epoch seconds)
    last_run: dict[str, float] = {
        "metagraph": 0.0,
        "sites": 0.0,
        "categories": 0.0,
        "coupons": 0.0,
        "validate_pending": 0.0,
        "validate_outdated": 0.0,
        "set_weights": 0.0,
    }

    # Convert intervals to seconds
    intervals = {
        "metagraph": settings.sync_nodes_interval.total_seconds(),
        "sites": settings.sync_sites_interval.total_seconds(),
        "categories": settings.sync_categories_interval.total_seconds(),
        "coupons": settings.sync_coupons_interval.total_seconds(),
        "validate_pending": settings.validate_coupons_interval.total_seconds(),
        "validate_outdated": settings.validate_outdated_coupon_interval.total_seconds(),
        "set_weights": settings.set_weights_interval.total_seconds(),
    }

    first_coupons_sync = True

    def is_due(name: str, now_ts: float) -> bool:
        return (now_ts - last_run[name]) >= intervals[name]

    while True:
        now_ts = time.time()

        # 1) Sync metagraph
        if is_due("metagraph", now_ts):
            try:
                logger.info("Running: Sync metagraph")
                await sync_metagraph(settings, substrate, metagraph_service)
            except Exception as e:
                logger.error(f"Error in Sync metagraph: {e}", exc_info=True)
            finally:
                last_run["metagraph"] = time.time()

        # 2) Sync sites
        now_ts = time.time()
        if is_due("sites", now_ts):
            try:
                logger.info("Running: Sync sites")
                await sync_sites(settings)
            except Exception as e:
                logger.error(f"Error in Sync sites: {e}", exc_info=True)
            finally:
                last_run["sites"] = time.time()

        # 3) Sync categories
        now_ts = time.time()
        if is_due("categories", now_ts):
            try:
                logger.info("Running: Sync categories")
                await sync_categories(settings)
            except Exception as e:
                logger.error(f"Error in Sync categories: {e}", exc_info=True)
            finally:
                last_run["categories"] = time.time()

        # 4) Sync coupons
        now_ts = time.time()
        if is_due("coupons", now_ts):
            try:
                logger.info("Running: Sync coupons")
                await sync_coupons(
                    settings,
                    coupon_service,
                    validator_sync_offset_service,
                    metagraph_service,
                    first_coupons_sync,
                )
                first_coupons_sync = False
            except Exception as e:
                logger.error(f"Error in Sync coupons: {e}", exc_info=True)
            finally:
                last_run["coupons"] = time.time()

        # 5) Validate coupons (pending + outdated)
        now_ts = time.time()
        if is_due("validate_pending", now_ts):
            try:
                logger.info("Running: Validate pending coupons")
                await validate_pending_coupons(coupon_service, settings)
            except Exception as e:
                logger.error(f"Error in Validate pending coupons: {e}", exc_info=True)
            finally:
                last_run["validate_pending"] = time.time()

        now_ts = time.time()
        if is_due("validate_outdated", now_ts):
            try:
                logger.info("Running: Validate outdated coupons")
                await validate_outdated_coupon(
                    coupon_service,
                    settings,
                    settings.validate_outdated_coupon_interval,
                )
            except Exception as e:
                logger.error(f"Error in Validate outdated coupons: {e}", exc_info=True)
            finally:
                last_run["validate_outdated"] = time.time()

        # 6) Set weights
        now_ts = time.time()
        if is_due("set_weights", now_ts):
            try:
                logger.info("Running: Set weights")
                # Use a fresh DB session because set_weights closes it internally
                fresh_db = next(get_db())
                await set_weights(
                    settings,
                    substrate,
                    fresh_db,
                    weight_calculator,
                    metagraph_service,
                    dynamic_config_service,
                )
            except Exception as e:
                logger.error(f"Error in Set weights: {e}", exc_info=True)
            finally:
                last_run["set_weights"] = time.time()

        # Small sleep to avoid busy loop; wake frequently to honor ordering
        await asyncio.sleep(2)


if __name__ == "__main__":
    settings = get_settings()
    db = next(get_db())
    metagraph_service = get_metagraph_service(db=db)
    substrate = interface.get_substrate(
        subtensor_network=settings.subtensor_network
    )
    validator_sync_offset_service = get_validator_sync_offset_service(
        db=db,
    )
    weight_calculator = get_weight_calculator_service(
        settings=settings,
        db=db,
    )
    dynamic_config_service = get_dynamic_config_service(
        db=db,
    )
    coupon_service = get_coupon_service(
        db=db,
        settings=settings,
        metagraph_service=metagraph_service,
        dynamic_config_service=dynamic_config_service,
    )

    async def main():
        await run_tasks_in_order(
            settings,
            substrate,
            coupon_service,
            validator_sync_offset_service,
            metagraph_service,
            weight_calculator,
            dynamic_config_service,
        )

    asyncio.run(main())
