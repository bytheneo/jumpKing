#!/usr/bin/env python3
"""JumpKing - WebSocket Game Server"""

import asyncio
import json
import secrets
import threading
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import websockets

rooms = {}

def generate_room_id():
    return secrets.token_urlsafe(4).upper().replace("-", "0").replace("_", "1")[:6]

async def broadcast_to_room(room_id, message, exclude=None):
    if room_id not in rooms:
        return
    for ws in rooms[room_id]["players"]:
        if ws is not None and ws != exclude:
            try:
                await ws.send(json.dumps(message, ensure_ascii=False))
            except:
                pass

async def send_to_player(ws, message):
    try:
        await ws.send(json.dumps(message, ensure_ascii=False))
    except:
        pass

async def handler(websocket):
    player_name = ""
    room_id = None
    player_number = 0

    try:
        async for raw_msg in websocket:
            try:
                msg = json.loads(raw_msg)
            except json.JSONDecodeError:
                await send_to_player(websocket, {"type": "error", "message": "Invalid message"})
                continue

            msg_type = msg.get("type")

            if msg_type == "create_room":
                player_name = msg.get("playerName", "Player1")
                while True:
                    new_id = generate_room_id()
                    if new_id not in rooms:
                        break
                room_id = new_id
                player_number = 1
                rooms[room_id] = {
                    "players": [websocket, None],
                    "names": [player_name, ""],
                    "state": None
                }
                await send_to_player(websocket, {
                    "type": "room_created",
                    "roomId": room_id,
                    "playerNumber": 1,
                    "playerName": player_name
                })

            elif msg_type == "join_room":
                target_room = msg.get("roomId", "").upper()
                player_name = msg.get("playerName", "Player2")
                if target_room not in rooms:
                    await send_to_player(websocket, {"type": "error", "message": "Room not found"})
                    continue
                if rooms[target_room]["players"][1] is not None:
                    await send_to_player(websocket, {"type": "error", "message": "Room is full"})
                    continue
                room_id = target_room
                player_number = 2
                rooms[room_id]["players"][1] = websocket
                rooms[room_id]["names"][1] = player_name
                await send_to_player(websocket, {
                    "type": "room_joined",
                    "roomId": room_id,
                    "playerNumber": 2,
                    "playerName": player_name,
                    "opponentName": rooms[room_id]["names"][0]
                })
                await send_to_player(rooms[room_id]["players"][0], {
                    "type": "opponent_joined",
                    "opponentName": player_name
                })

            elif msg_type == "start_game":
                if room_id and room_id in rooms:
                    board_size = msg.get("boardSize", 9)
                    board_mode = msg.get("boardMode", "standard")
                    await broadcast_to_room(room_id, {
                        "type": "game_started",
                        "boardSize": board_size,
                        "boardMode": board_mode,
                        "player1Name": rooms[room_id]["names"][0],
                        "player2Name": rooms[room_id]["names"][1]
                    })

            elif msg_type == "game_action":
                if room_id and room_id in rooms:
                    action = msg.get("action")
                    data = msg.get("data", {})
                    await broadcast_to_room(room_id, {
                        "type": "game_action",
                        "playerNumber": player_number,
                        "action": action,
                        "data": data
                    }, exclude=websocket)

            elif msg_type == "end_turn":
                if room_id and room_id in rooms:
                    await broadcast_to_room(room_id, {
                        "type": "turn_ended",
                        "playerNumber": player_number
                    }, exclude=websocket)

            elif msg_type == "chat":
                if room_id and room_id in rooms:
                    await broadcast_to_room(room_id, {
                        "type": "chat",
                        "playerNumber": player_number,
                        "playerName": player_name,
                        "message": msg.get("message", "")
                    }, exclude=websocket)

            elif msg_type == "leave_room":
                if room_id and room_id in rooms:
                    await broadcast_to_room(room_id, {
                        "type": "opponent_left",
                        "playerName": player_name
                    }, exclude=websocket)
                break

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        if room_id and room_id in rooms:
            other = rooms[room_id]["players"][1] if player_number == 1 else rooms[room_id]["players"][0]
            if other is not None:
                try:
                    await other.send(json.dumps({"type": "opponent_disconnected"}))
                except:
                    pass
            del rooms[room_id]
            print(f"Room {room_id} closed")


def start_http_server(port):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    class Handler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            super().end_headers()
        def log_message(self, format, *args):
            pass
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


async def main():
    print("JumpKing game server starting...")
    print("WebSocket: ws://localhost:8765")
    print("HTTP:      http://localhost:8080")
    print("Press Ctrl+C to stop")

    http_thread = threading.Thread(target=start_http_server, args=(8080,), daemon=True)
    http_thread.start()

    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
