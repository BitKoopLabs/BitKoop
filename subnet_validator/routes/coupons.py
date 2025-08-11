from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Query,
)
from datetime import (
    datetime,
)
from typing import (
    Annotated,
    Literal,
    Optional,
    List,
)
from fiber.utils import (
    get_logger,
)


from ..constants import (
    CouponStatus,
)

from ..dependencies import (
    get_coupon_service,
    get_dynamic_config_service,
)
from ..services.coupon_service import (
    CouponService,
)
from ..services.dynamic_config_service import (
    DynamicConfigService,
)

from ..auth import (
    verify_hotkey_signature,
)
from ..models import (
    CouponRecheckRequest,
    CouponRecheckResponse,
    CouponSubmitRequest,
    CouponSubmitResponse,
    CouponDeleteResponse,
    CouponDeleteRequest,
    CouponResponse,
)

logger = get_logger(__name__)

router = APIRouter()


@router.put("/")
async def submit_code(
    body: CouponSubmitRequest,
    signature: Annotated[
        str,
        Depends(verify_hotkey_signature),
    ],
    coupon_service: Annotated[
        CouponService,
        Depends(get_coupon_service),
    ],
) -> CouponSubmitResponse:
    """
    Submit a coupon code with wallet signature authentication.

    Headers required:
    - X-Signature: Hex-encoded signature of the request payload
    """
    try:
        response = coupon_service.create_coupon(
            body,
            signature,
            body.hotkey,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in submit_code: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/")
def get_coupons(
    coupon_service: Annotated[
        CouponService,
        Depends(get_coupon_service),
    ],
    miner_hotkey: Optional[str] = Query(None),
    site_id: Optional[int] = Query(None),
    page_size: int = Query(
        20,
        gt=0,
        le=100,
    ),
    page_number: int = Query(
        1,
        gt=0,
    ),
    updated_from: Optional[datetime] = Query(None),
    created_from: Optional[datetime] = Query(None),
    last_action_from: Optional[datetime] = Query(None),
    status: Optional[CouponStatus] = Query(None),
    sort_by: Literal["created_at", "updated_at", "last_action_date"] = Query(
        "updated_at"
    ),
) -> List[CouponResponse]:
    return coupon_service.get_coupons(
        miner_hotkey=miner_hotkey,
        site_id=site_id,
        updated_from=updated_from,
        created_from=created_from,
        last_action_from=last_action_from,
        status=status,
        page_size=page_size,
        page_number=page_number,
        sort_by=sort_by,
    )


@router.get("/sync/status")
async def get_sync_status(
    dynamic_config_service: Annotated[
        DynamicConfigService,
        Depends(get_dynamic_config_service),
    ]
):
    try:
        progress = dynamic_config_service.get_sync_progress()
        last_result = dynamic_config_service.get_last_sync_result()
        return {
            "progress": progress or None,
            "last_result": last_result or None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read sync status: {e}",
        )


@router.post(
    "/delete"
)  # We use POST instead of DELETE because DELETE do not use body
async def delete_code(
    body: CouponDeleteRequest,
    signature: Annotated[
        str,
        Depends(verify_hotkey_signature),
    ],
    coupon_service: Annotated[
        CouponService,
        Depends(get_coupon_service),
    ],
) -> CouponDeleteResponse:
    """
    Delete a coupon code with wallet signature authentication.

    Headers required:
    - X-Signature: Hex-encoded signature of the request payload
    """
    try:
        response = coupon_service.delete_coupon(
            body,
            signature,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in delete_code: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@router.post("/recheck")
async def recheck_coupon(
    body: CouponRecheckRequest,
    signature: Annotated[
        str,
        Depends(verify_hotkey_signature),
    ],
    coupon_service: Annotated[
        CouponService,
        Depends(get_coupon_service),
    ],
) -> CouponRecheckResponse:
    try:
        response = coupon_service.recheck_coupon(
            body,
            signature,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in recheck_coupon: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )
