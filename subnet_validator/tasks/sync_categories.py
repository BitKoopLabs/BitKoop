import asyncio
from subnet_validator.settings import (
    Settings,
)
from subnet_validator.services.category_service import (
    CategoryService,
)
from subnet_validator.database.database import (
    get_db,
)
from subnet_validator.clients.supervisor_client import (
    SupervisorApiClient,
)
from fiber.logging_utils import (
    get_logger,
)

logger = get_logger(__name__)


async def sync_categories(
    settings: Settings,
):
    logger.info("Syncing categories from supervisor API")
    async with SupervisorApiClient(settings.supervisor_api_url) as api_client:
        try:
            categories = await api_client.get_product_categories()
        except Exception as e:
            logger.error(
                f"Failed to fetch categories from supervisor API: {e}"
            )
            return
    db = next(get_db())
    service = CategoryService(db)
    processed = 0
    for category in categories:
        try:
            service.add_or_update_category(
                category_id=category.category_id,
                category_name=category.category_name,
            )
            processed += 1
        except Exception as e:
            logger.error(
                f"Failed to add/update category {category.category_id}: {e}"
            )
    logger.info(f"Processed {processed} categories.")


if __name__ == "__main__":
    settings = Settings()
    asyncio.run(sync_categories(settings))
