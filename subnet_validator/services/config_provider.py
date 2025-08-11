import shelve
import aiohttp
import logging
from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Optional,
)
from koupons_validator.models import (
    Config,
)

logger = logging.getLogger(__name__)


class ConfigProvider:
    def __init__(
        self,
        api_url: str = "https://api.discount.ai/config",
        cache_file: str = "config",
    ):
        self.api_url = api_url
        self.cache_file = cache_file
        self.cache_key = "sites_config"

    def _get_cached_config(
        self,
    ) -> Optional[Config]:
        """Retrieve config from local cache if it exists and is not expired."""
        try:
            with shelve.open(self.cache_file) as db:
                if self.cache_key in db:
                    config: Config = db[self.cache_key]
                    if (
                        config.expirationDate
                        and config.expirationDate > datetime.now()
                    ):
                        return config
        except Exception as e:
            logger.error(
                "Error reading from cache: %s",
                e,
            )
        return None

    def _cache_config(
        self,
        config: Config,
    ) -> None:
        """Cache the config with updated expiration date."""
        try:
            config.expirationDate = datetime.now() + timedelta(
                minutes=config.expirationTimeMinutes
            )
            with shelve.open(self.cache_file) as db:
                db[self.cache_key] = config
        except Exception as e:
            logger.error(
                "Error caching config: %s",
                e,
            )

    async def _fetch_config_from_api(
        self,
    ) -> Config:
        """Fetch config from the API using aiohttp."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return Config.model_validate(data)
        except Exception as e:
            logger.error(
                "Error fetching config from API: %s",
                e,
            )
            raise

    async def get_config(
        self,
    ) -> Config:
        """Get config from cache if available and not expired, otherwise fetch from API."""
        # Try to get from cache first
        cached_config = self._get_cached_config()
        if cached_config:
            return cached_config

        # If not in cache or expired, fetch from API
        config = await self._fetch_config_from_api()
        self._cache_config(config)
        return config
