import json

from fastapi import (
    HTTPException,
    Header,
    Request,
)
from fiber import (
    Keypair,
)

from fiber.logging_utils import get_logger
from .models import (
    HotkeyRequest,
    CouponActionRequest,
    CouponTypedActionRequest,
    CouponSubmitRequest,
    CouponDeleteRequest,
    CouponRecheckRequest,
)
from .constants import CouponAction


logger = get_logger(__name__)


def verify_signature(
    hotkey: str,
    message: bytes | str,
    signature: bytes | str,
) -> bool:
    """Verify the signature using the hotkey."""
    keypair = Keypair(hotkey)
    return keypair.verify(
        message,
        signature,
    )


def is_signature_valid(
    body: HotkeyRequest,
    x_signature: str,
) -> bool:
    try:
        message = json.dumps(
            body.model_dump(mode="json"),
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
        )
        logger.debug(f"Message: {message}, signature: {x_signature}")
        return verify_signature(
            body.hotkey,
            message,
            bytes.fromhex(x_signature),
        )
    except Exception as e:
        return False


def get_action_from_request_type(
    request_body: CouponActionRequest,
) -> CouponAction:
    """Determine the action type based on the request type."""
    if isinstance(request_body, CouponSubmitRequest):
        return CouponAction.CREATE
    elif isinstance(request_body, CouponDeleteRequest):
        return CouponAction.DELETE
    elif isinstance(request_body, CouponRecheckRequest):
        return CouponAction.RECHECK
    else:
        raise ValueError(f"Unknown request type: {type(request_body)}")


def get_action_from_path(
    request: Request,
) -> CouponAction:
    """Determine the action type based on the request path."""
    path = request.url.path
    if path.endswith("/delete"):
        return CouponAction.DELETE
    elif path.endswith("/recheck"):
        return CouponAction.RECHECK
    elif path.endswith("/") or path.endswith(""):
        return CouponAction.CREATE
    else:
        raise ValueError(f"Unknown path for action determination: {path}")


def verify_hotkey_signature(
    body: CouponActionRequest,
    request: Request,
    x_signature: str = Header(
        ...,
        alias="X-Signature",
    ),
) -> str:
    """
    Verify wallet signature by mapping request to CouponTypedActionRequest.

    This method:
    1. Determines the action type from the request type or path
    2. Creates a CouponTypedActionRequest with the appropriate action
    3. Verifies the signature of the typed request
    """
    # Determine action type from request type first, fallback to path
    try:
        action = get_action_from_request_type(body)
    except ValueError:
        # Fallback to path-based determination
        action = get_action_from_path(request)

    # Create typed action request
    typed_request = CouponTypedActionRequest(
        hotkey=body.hotkey,
        site_id=body.site_id,
        code=body.code,
        submitted_at=body.submitted_at,
        action=action,
    )

    # Verify signature of the typed request
    if not is_signature_valid(typed_request, x_signature):
        raise HTTPException(
            status_code=401,
            detail="Invalid signature",
        )

    return x_signature
