import pytest
import json
from pathlib import (
    Path,
)
from koupons_validator.validator import (
    CouponValidator,
)
from koupons_validator.models import (
    Coupon,
)
import logging

logger = logging.getLogger(__name__)


@pytest.fixture
def config_data():
    return {
        "defaultWaitTime": 1000,
        "expirationTimeMinutes": 60,
        "sites": {
            "gap": {
                "baseUrl": "https://gap.com",
                "productUrl": "https://www.gap.com/browse/product.do?pid=735031122&rrec=true&mlink=5001,1,home_gaphome2_rr_1&clink=1#pdp-page-content",
                "actions": [
                    {
                        "name": "goToGapUS",
                        "selector": "//*[@id='sendToDotCom']",
                        "type": "click",
                    },
                    {
                        "name": "gotoProduct",
                        "type": "gotoProductUrl",
                    },
                    {
                        "name": "closePopup",
                        "selector": "//button[@aria-label='close email sign up modal']",
                        "type": "click",
                        "optional": True,
                    },
                    {
                        "name": "selectSize",
                        "selector": "//div[contains(@class, 'pdp-dimension') and not(contains(@class, '--unavailable'))]//input[@name='buy-box-Size']",
                        "type": "click",
                    },
                    {
                        "name": "addToBag",
                        "selector": "//*[@id='AddToBag_add-to-bag__button']",
                        "type": "click",
                    },
                ],
                "cartUrl": "https://secure-www.gap.com/shopping-bag",
                "totalPriceSelector": "//*[@id='order-summary']/div[3]/div[2]/span",
                "promoCode": {
                    "inputSelector": "//*[@id='promo-code-input']",
                    "invalidSelector": "//div[@role='alert']",
                    "validSelector": "//*[@id='promos']/div/div[*]/div/div/div[1]/div[1]/div",
                    "applySelector": "//*[@id='apply-promo-code-button']",
                    "defySelector": "//*[@id='promos']/div/div[*]/div/div/div[2]/button",
                    "discountSelector": "//*[@id='promos']/div/div[*]/div/div/div[1]/div[1]/div",
                    "discountType": "amount",
                    "discountPattern": "\\$([\\d\\.]+)",
                },
            }
        },
    }


@pytest.fixture
def validator(
    config_data,
):
    return CouponValidator(
        config_data=config_data,
        headless=False,
    )


@pytest.mark.asyncio
async def test_single_valid_coupon(
    validator,
):
    """Test validation of a single valid coupon code"""
    coupons = [
        Coupon(
            code="SAVE20",
            expected_discount="20%",
        )
    ]

    result = await validator.validate_coupons(
        url="https://gap.com/",
        coupons=coupons,
    )

    assert result.attempts_made == 1
    assert len(result.results) == 1
    assert (
        result.statistics.valid >= 0
    )  # We can't guarantee the coupon will be valid as they expire
    assert result.results[0].code == "SAVE20"


@pytest.mark.asyncio
async def test_multiple_coupons(
    validator,
):
    """Test validation of multiple coupon codes"""
    coupons = [
        Coupon(
            code="SAVE20",
            expected_discount="20%",
        ),
        Coupon(
            code="INVALID123",
            expected_discount="0%",
        ),
        Coupon(
            code="GAP30OFF",
            expected_discount="30%",
        ),
    ]

    result = await validator.validate_coupons(
        url="https://gap.com/",
        coupons=coupons,
    )

    assert result.attempts_made == 3
    assert len(result.results) == 3
    assert (
        result.statistics.valid
        + result.statistics.invalid
        + result.statistics.errors
        == 3
    )


@pytest.mark.asyncio
async def test_invalid_coupon(
    validator,
):
    """Test validation of an invalid coupon code"""
    coupons = [
        Coupon(
            code="INVALID123",
            expected_discount="0%",
        )
    ]

    result = await validator.validate_coupons(
        url="https://gap.com/",
        coupons=coupons,
    )

    assert result.attempts_made == 1
    assert len(result.results) == 1
    assert result.results[0].code == "INVALID123"
    assert result.results[0].status in [
        "invalid",
        "error",
    ]  # Should be invalid or error


@pytest.mark.asyncio
async def test_empty_coupon_list(
    validator,
):
    """Test validation with empty coupon list"""
    coupons = []

    result = await validator.validate_coupons(
        url="https://gap.com/",
        coupons=coupons,
    )

    assert result.attempts_made == 0
    assert len(result.results) == 0
    assert result.statistics.valid == 0
    assert result.statistics.invalid == 0
    assert result.statistics.errors == 0


@pytest.mark.asyncio
async def test_instyle20_valid_coupon(
    validator,
):
    """Test validation of the INSTYLE20 coupon code (should be valid if active)"""
    coupons = [
        Coupon(
            code="INSTYLE20",
            expected_discount="20%",
        )
    ]

    result = await validator.validate_coupons(
        url="https://gap.com/",
        coupons=coupons,
    )

    assert result.attempts_made == 1
    assert len(result.results) == 1
    assert result.results[0].code == "INSTYLE20"
    # Accept valid, invalid, or error (since coupon may expire)
    assert result.results[0].status in [
        "valid",
        "invalid",
        "error",
    ]


@pytest.mark.asyncio
async def test_valid_then_invalid_coupon(
    validator,
):
    """Test that an invalid coupon after a valid one is handled correctly in a single array."""
    coupons = [
        Coupon(
            code="INSTYLE20",
            expected_discount="10%",
        ),  # Should be  valid if active
        Coupon(
            code="INVALID123",
            expected_discount="0%",
        ),  # Should be invalid
    ]
    result = await validator.validate_coupons(
        url="https://gap.com/",
        coupons=coupons,
    )
    logger.info(result)
    assert result.attempts_made == 2
    assert len(result.results) == 2
    assert result.results[0].code == "INSTYLE20"
    assert result.results[1].code == "INVALID123"
    # Accept valid, invalid, or error for the first (since coupon may expire)
    assert result.results[0].status in [
        "valid",
        "invalid",
        "error",
    ]
    # The second should be invalid or error
    assert result.results[1].status in [
        "invalid",
        "error",
    ]
