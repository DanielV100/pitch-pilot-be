
import json, uuid
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()              
rooms: Dict[str, Set[WebSocket]] = {}


@router.websocket("/join")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            try:
                raw = await ws.receive_text()
                msg = json.loads(raw)
                room = msg.get("room")
                if not room:
                    await ws.close(code=4000, reason="room missing")
                    break
            except (json.JSONDecodeError, KeyError) as e:
                print("bad message", raw, e)
                await ws.close(code=4001, reason="bad json")
                break

            rooms.setdefault(room, set()).add(ws)
           
            for peer in rooms[room].copy():
                if peer is ws:
                    continue
                try:
                    await peer.send_text(raw)
                except WebSocketDisconnect:
                    rooms[room].discard(peer)
    except WebSocketDisconnect:
        
        for peers in rooms.values():
            peers.discard(ws)
