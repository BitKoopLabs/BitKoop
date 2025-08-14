from typing import (
    Optional,
)
from datetime import (
    UTC,
    datetime,
)
from sqlalchemy.orm import (
    Session,
)
from subnet_validator.constants import (
    SiteStatus,
    CouponStatus,
)
from subnet_validator.database.entities import (
    Site,
    Coupon,
)


class SiteService:
    """
    Service for adding or updating Site records in the database.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def add_or_update_site(
        self,
        store_id: int,
        store_domain: str,
        store_status: int,
        miner_hotkey: str | None = None,
        config: dict | None = None,
    ) -> Site:
        """
        Add a new site or update an existing one by id.
        If the site exists, update its base_url and status. Otherwise, create a new site.
        Returns the Site instance.
        """
        status = SiteStatus(store_status)
        site = self.db.query(Site).filter(Site.id == store_id).first()
        if site:
            previous_status = site.status
            site.base_url = store_domain
            site.status = status
            site.miner_hotkey = miner_hotkey
            site.config = config
            # If site transitions from ACTIVE to non-active (PENDING or INACTIVE),
            # immediately move VALID coupons to PENDING so they are revalidated ASAP.
            if previous_status == SiteStatus.ACTIVE and status != SiteStatus.ACTIVE:
                self.db.query(Coupon).filter(
                    Coupon.site_id == store_id,
                    Coupon.status == CouponStatus.VALID,
                ).update(
                    {
                        Coupon.status: CouponStatus.PENDING,
                        Coupon.last_checked_at: datetime.now(UTC),
                    },
                    synchronize_session=False,
                )
        else:
            site = Site(
                id=store_id,
                base_url=store_domain,
                status=status,
                miner_hotkey=miner_hotkey,
                config=config,
            )
            self.db.add(site)
        self.db.flush()
        return site
