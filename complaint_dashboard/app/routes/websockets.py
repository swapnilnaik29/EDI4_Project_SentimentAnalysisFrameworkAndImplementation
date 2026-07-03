import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard notifications.
    Keeps client channel active to push newly processed complaints instantly.
    """
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect incoming data from dashboard clients, but we read to detect disconnects.
            data = await websocket.receive_text()
            # Send simple ping-pong heartbeat if requested
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket execution error: {e}")
        manager.disconnect(websocket)
