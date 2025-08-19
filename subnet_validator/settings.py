from datetime import (
    timedelta,
)
from . import (
    constants,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from pydantic import Field


class Settings(BaseSettings):
    database_url: str
    env: str = "dev"
    subtensor_network: str = "finney"
    max_coupons_per_site: int = 3
    recheck_interval: timedelta = timedelta(days=1)
    resubmit_interval: timedelta = timedelta(days=1)
    validate_coupons_interval: timedelta = timedelta(minutes=1)
    validate_outdated_coupon_interval: timedelta = timedelta(days=1)
    sync_sites_interval: timedelta = timedelta(minutes=10)
    sync_coupons_interval: timedelta = timedelta(minutes=2)
    sync_categories_interval: timedelta = timedelta(minutes=10)
    sync_nodes_interval: timedelta = timedelta(minutes=5)
    set_weights_interval: timedelta = timedelta(hours=1)  # Run every hour
    delta_points: timedelta = timedelta(days=7)
    submit_window: timedelta = timedelta(minutes=2)
    coupon_weight: float = 0.8
    container_weight: float = 0.2
    supervisor_api_url: str = "http://91.99.203.36/api"
    min_weight_stake: float = 1000.0
    sync_coupons_use_gather: bool = True
    wallet_name: str = "default"
    hotkey_name: str = Field(default="default", alias="WALLET_HOTKEY")
    # Peer sync preflight
    respect_peer_sync: bool = True
    peer_sync_preflight_max_wait: timedelta = timedelta(seconds=15)
    peer_sync_preflight_interval: timedelta = timedelta(seconds=3)

    @property
    def netuid(
        self,
    ) -> int:
        return constants.NETWORK_TO_NETUID[self.subtensor_network]

    model_config = SettingsConfigDict(env_file=".env")
