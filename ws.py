# ws.py - Websocket implementation for live data

# Packages
import asyncio
import websockets
import random
import time
import threading

# Project
import app

# Globals
connected_clients = set()
poll_rate = 0.0166666667 # ~60hz

# Loop endlessly and post data in the websocket
async def broadcast():
    while app.is_polling:
        if connected_clients:
            message = app.latest_data_dump
            await asyncio.gather(*[
                ws.send(message)
                for ws in connected_clients
                if ws.open
            ])
        await asyncio.sleep(poll_rate)

async def handler(websocket):
    connected_clients.add(websocket)
    print("Client connected")
    try:
        # Attempt to start the polling process
        if not is_polling:
            is_polling = True
            polling_thread = threading.Thread(target=app.poll_sensor_data, daemon=True)
            polling_thread.start()
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print("Client disconnected")

async def ws_open():
    # Run websocket on localhost 50 ports offset from Flask API
    async with websockets.serve(handler, "127.0.0.1", 5050):
        print("WebSocket server running on ws://127.0.0.1:5050")
        await asyncio.Future()  # run forever

def ws_main():
    asyncio.run(ws_open())