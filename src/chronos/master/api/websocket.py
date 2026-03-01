import asyncio

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from chronos.master.events import event_bus

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("websocket_client_connected", clients=event_bus.subscriber_count + 1)
    try:
        async for event in event_bus.subscribe():
            try:
                await websocket.send_json(event)
            except (WebSocketDisconnect, RuntimeError):
                break
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        logger.info("websocket_client_disconnected", clients=event_bus.subscriber_count)
