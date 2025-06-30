import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
rooms: Dict[str, Set[WebSocket]] = {}

@router.websocket("/join")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    room = None
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            if "room" in msg:
              
                if room is None:
                    room = msg["room"]
                    rooms.setdefault(room, set()).add(ws)
            if room is None:
                await ws.close(code=4000, reason="room missing")
                return
            for peer in list(rooms[room]):
                if peer is ws:
                    continue
                try:
                    await peer.send_text(raw)
                except WebSocketDisconnect:
                    rooms[room].discard(peer)
    except WebSocketDisconnect:
        if room and ws in rooms.get(room, set()):
            rooms[room].remove(ws)
            if not rooms[room]:
                del rooms[room]
