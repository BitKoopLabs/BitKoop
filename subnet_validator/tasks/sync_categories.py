import asyncio
from subnet_validator import dependencies
from subnet_validator.settings import (
    Settings,
)
from subnet_validator.services.category_service import (
    CategoryService,
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
    category_service: CategoryService,
):
    logger.info("Syncing categories from supervisor API")
    processed = 0
    page = 1
    page_size = 100
    
    async with SupervisorApiClient(settings.supervisor_api_url) as api_client:
        while True:
            try:
                categories = await api_client.get_product_categories(page=page, page_size=page_size)
            except Exception as e:
                logger.error(
                    f"Failed to fetch categories from supervisor API (page {page}): {e}"
                )
                break

            if not categories:
                break

            for category in categories:
                try:
                    category_service.add_or_update_category(
                        category_id=category.category_id,
                        category_name=category.category_name,
                    )
                    processed += 1
                except Exception as e:
                    logger.error(
                        f"Failed to add/update category {category.category_id}: {e}"
                    )
            # CategoryService commits internally; no extra commit needed

            if len(categories) < page_size:
                break
            page += 1

    logger.info(f"Processed {processed} categories.")


if __name__ == "__main__":
    settings = Settings()
    db = next(dependencies.get_db())
    category_service = CategoryService(db)
    asyncio.run(sync_categories(settings, category_service))
