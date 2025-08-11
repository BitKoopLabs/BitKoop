import asyncio
import socket
import struct

from subnet_validator.services.metagraph_service import MetagraphService
from subnet_validator.settings import (
    Settings,
)
from fiber.chain.fetch_nodes import (
    get_nodes_for_netuid,
)
from fiber.chain import (
    interface,
    chain_utils,
)
from async_substrate_interface import (
    SubstrateInterface,
)
from fiber.logging_utils import (
    get_logger,
)
from fiber.chain.models import (
    Node,
)
from subnet_validator import (
    __version__ as version,
    APP_TITLE,
)
import httpx
from typing import Optional


async def sync_metagraph(
    settings: Settings,
    substrate: SubstrateInterface,
    metagraph_service: MetagraphService,
):
    logger = get_logger(__name__)

    logger.info("Syncing metagraph nodes")
    nodes = await _get_all_nodes(
        substrate=substrate,
        netuid=settings.netuid,
    )

    if not nodes:
        logger.warning("No nodes found")
        return

    await _sync_nodes_to_database(
        nodes,
        metagraph_service,
        logger,
    )
    logger.info(f"Finished syncing {len(nodes)} metagraph nodes.")


async def _sync_nodes_to_database(
    nodes: list[Node],
    metagraph_service: MetagraphService,
    logger,
):
    async def sync_node(node: Node):
        try:
            # Get validator version if available
            validator_version = await _get_validator_version(node)

            # Create or update node in database
            is_created = metagraph_service.create_or_update_node(
                node, validator_version=validator_version
            )

            action = "Created" if is_created else "Updated"
            logger.info(f"{action} node {node.hotkey} in database")

        except Exception as e:
            logger.error(f"Failed to sync node {node.hotkey}: {e}")

    await asyncio.gather(*(sync_node(node) for node in nodes))


async def _get_all_nodes(
    substrate: SubstrateInterface,
    netuid: int,
):
    nodes = [
        _fix_node_ip(node)
        for node in get_nodes_for_netuid(
            substrate=substrate,
            netuid=netuid,
        )
    ]
    return nodes


async def _get_validator_version(
    node: Node,
) -> Optional[str]:
    """
    Get validator version from the node's API endpoint.
    Based on _is_bitkoop_validator but returns the version instead of boolean.
    """
    ip = node.ip
    port = node.port

    if ip == "0.0.0.0":
        return None

    url = f"http://{ip}:{port}/openapi.json"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            data: dict = resp.json()
            info: dict = data.get("info", {})

            # Check if it's a BitKoop validator
            if info.get("title") == APP_TITLE:
                return info.get("version")
            return None
    except Exception:
        return None


def _parse_ip(
    ip_int: int,
):
    ip_bytes = struct.pack(
        ">I",
        ip_int,
    )  # Little-endian unsigned int
    return socket.inet_ntoa(ip_bytes)


def _fix_node_ip(
    node: Node,
):
    node.ip = _parse_ip(int(node.ip))
    return node


if __name__ == "__main__":
    from subnet_validator import dependencies

    settings = dependencies.get_settings()
    substrate = interface.get_substrate(
        subtensor_network=settings.subtensor_network
    )
    db = next(dependencies.get_db())
    metagraph_service = dependencies.get_metagraph_service(db=db)

    asyncio.run(
        sync_metagraph(
            settings,
            substrate,
            metagraph_service,
        )
    )
