from fastapi import APIRouter, WebSocket

from .client import WebRTCManager

routes = APIRouter()
webrtc_manager = WebRTCManager()


@routes.websocket('/ws/{client_id}')
async def webrtc(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if data['type'] == 'offer':
                answer = await webrtc_manager.handle_offer(client_id, data['sdp'])
                await websocket.send_json(answer)
    except:
        pass
    finally:
        if client_id in webrtc_manager.peer_connections:
            await webrtc_manager.peer_connections[client_id].close()
            del webrtc_manager.peer_connections[client_id]
