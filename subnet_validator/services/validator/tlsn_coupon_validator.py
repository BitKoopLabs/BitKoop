import asyncio
from datetime import UTC, datetime
from typing import List, Tuple, Optional

import httpx

from fiber.logging_utils import get_logger
from subnet_validator.constants import CouponStatus
from subnet_validator.database.entities import Coupon, Site
from subnet_validator.services.validator.base import BaseCouponValidator


logger = get_logger(__name__)


class TlsnCouponValidator(BaseCouponValidator):
    def __init__(self, site: Site, verifier_url: str):
        self.site = site
        self.verifier_url = verifier_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_or_create_client(self) -> httpx.AsyncClient:
        if self._client is None:
            timeout = httpx.Timeout(connect=5.0, read=20.0, write=10.0, pool=10.0)
            self._client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        return self._client

    async def _close_client(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass
            finally:
                self._client = None

    async def _check_coupon(self, coupon: Coupon) -> Optional[bool]:
        """Post TLSN presentation hex in coupon.code to verifier service.

        Expects verifier to return JSON with { valid: bool, ... }.
        Returns True/False on definitive result, None otherwise.
        """
        try:
            client = await self._get_or_create_client()
            payload = {"data": coupon.code}
            logger.info(
                "Posting TLSN proof for coupon | site_id=%s code_len=%s url=%s",
                coupon.site_id,
                len(coupon.code or ""),
                self.verifier_url,
            )
            resp = await client.post(self.verifier_url, json=payload, headers={"Accept": "application/json"})
            resp.raise_for_status()
            data = resp.json()
            valid = data.get("valid")
            if isinstance(valid, bool):
                return valid
            return None
        except httpx.RequestError as e:
            logger.error("TLSN verifier request error | site_id=%s code=%s err=%s", coupon.site_id, coupon.code, e)
            return None
        except asyncio.TimeoutError:
            logger.error("TLSN verifier timed out | site_id=%s code=%s", coupon.site_id, coupon.code)
            return None
        except Exception as e:
            logger.exception("TLSN verifier unexpected error | site_id=%s code=%s err=%s", coupon.site_id, coupon.code, e)
            return None

    async def validate(self, coupons: List[Coupon]) -> List[Tuple[Coupon, bool]]:
        results: List[Tuple[Coupon, bool]] = []
        try:
            for coupon in coupons:
                try:
                    result = await self._check_coupon(coupon)
                    if result is True:
                        coupon.status = CouponStatus.VALID
                    elif result is False:
                        coupon.status = CouponStatus.INVALID
                    coupon.last_checked_at = datetime.now(UTC)
                    results.append((coupon, result is True))
                except Exception as e:
                    logger.exception("Error validating coupon via TLSN | code=%s err=%s", coupon.code, e)
                    try:
                        coupon.last_checked_at = datetime.now(UTC)
                    except Exception:
                        pass
                    results.append((coupon, False))
        finally:
            await self._close_client()
        return results


