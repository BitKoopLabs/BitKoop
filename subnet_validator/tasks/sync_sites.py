import asyncio
from subnet_validator.clients.supervisor_client import (
    SupervisorApiClient,
)
from subnet_validator.settings import (
    Settings,
)
from subnet_validator.services.site_service import (
    SiteService,
)
from subnet_validator.database.database import (
    get_db,
)
from fiber.logging_utils import (
    get_logger,
)

logger = get_logger(__name__)


async def sync_sites(
    settings: Settings,
):
    logger.info("Syncing sites from supervisor API")
    async with SupervisorApiClient(settings.supervisor_api_url) as api_client:
        try:
            sites = await api_client.get_sites()
        except Exception as e:
            logger.error(f"Failed to fetch sites from supervisor API: {e}")
            return
    db = next(get_db())
    service = SiteService(db)
    processed = 0
    for site in sites:
        try:
            service.add_or_update_site(
                store_id=site.store_id,
                store_domain=site.store_domain,
                store_status=site.store_status,
                miner_hotkey=site.miner_hotkey,
                config=site.config,
            )
            processed += 1
        except Exception as e:
            logger.error(f"Failed to add/update site {site.store_id}: {e}")
        db.commit()
    logger.info(f"Processed {processed} sites.")


if __name__ == "__main__":
    settings = Settings()
    asyncio.run(sync_sites(settings))
