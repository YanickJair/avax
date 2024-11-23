import asyncio

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay


class WebRTCManager:
    def __init__(self):
        self.peer_connections = {}
        self.media_relay = MediaRelay()

    async def create_peer_connection(self, client_id):
        pc = RTCPeerConnection()
        self.peer_connections[client_id] = pc

        @pc.on('track')
        async def on_track(track):
            if track.kind == 'audio':
                pc.addTrack(self.media_relay.subscribe(track))

        return pc

    async def handle_offer(self, client_id, offer):
        pc = await self.create_peer_connection(client_id)
        await pc.setRemoteDescription(RTCSessionDescription(sdp=offer, type='offer'))
        if answer := await pc.createAnswer():
            await pc.setLocalDescription(answer)
        return {'sdp': pc.localDescription.sdp, 'type': pc.localDescription.type}
