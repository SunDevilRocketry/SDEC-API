# General
import threading
import time
import os
import sys
import datetime
import math
import json
import asyncio
import traceback
import websockets

# save this as app.py
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
# Setup path
sys.path.insert(0, './sdec')

# SDEC
import sdec

terminalSerObj = sdec.terminalData()

app = Flask(__name__)
CORS(app)

# Globals for sensor dump
is_polling = False
polling_thread = None
poll_interval = 0.01666666  # seconds, adjust as needed
request_timeout = 5 # seconds before timeout
busy_wait_break = 0.03 # seconds between response tries

# WS Globals
connected_clients = set()

# Shared data from the sensors
class SensorData:
    def __init__(self):
        self.lock = threading.Lock()
        self.dump = {}

shared_data = SensorData()

# --------------------------------------------------------------------
# Sensor Dump Thread
# --------------------------------------------------------------------
def poll_sensor_data():
    """Continuously run 'sensor dump' command and cache the result."""
    global terminalSerObj, shared_data, is_polling

    if terminalSerObj.firmware == 'APPA':
        userCommand = "dashboard-dump"
        userArgs = []
    elif terminalSerObj.firmware != None:
        userCommand = "sensor"
        userArgs = ["dump"]

    if terminalSerObj.firmware is None:
        print("Terminal not connected yet, waiting...")
        while terminalSerObj.firmware is None and is_polling:
            time.sleep(0.1)

    while is_polling:
        start_time = time.time()
        try:
            terminalSerObj, data_dump = sdec.command_list[userCommand](userArgs, terminalSerObj)
            # sanitize invalid values
            for key in data_dump:
                if math.isinf(data_dump[key]):
                    data_dump[key] = 999999
                if math.isnan(data_dump[key]):
                    data_dump[key] = 999999
            with shared_data.lock:
                shared_data.dump.clear()
                shared_data.dump.update(data_dump)
        except Exception as e:
            print(f"Poll Error: {e}")
            traceback.print_exc()
            print(terminalSerObj.firmware)
            is_polling = False
        elapsed_time = time.time() - start_time # print this value for debugging
        time.sleep( max( poll_interval - elapsed_time, 0 ) ) # sleep if not reached interval yet

# --------------------------------------------------------------------
# Async Websocket Functions
# --------------------------------------------------------------------
# Loop endlessly and post data in the websocket
async def broadcast():
    global shared_data
    while True:
        if connected_clients:
            with shared_data.lock:
                message = shared_data.dump.copy()
            if message:
                # Try sending to all clients, catch exceptions
                for client in list(connected_clients):  # list() to safely modify set
                    try:
                        await client.send(json.dumps(message))
                    except Exception as e:
                        print(f"Removing disconnected client: {e}")
                        connected_clients.remove(client)
        await asyncio.sleep(0.001)

async def handler(websocket):
    connected_clients.add(websocket)
    print("Client connected")
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print("Client disconnected")

async def ws_open():
    # Run websocket on localhost 50 ports offset from Flask API
    async with websockets.serve(handler, "127.0.0.1", 5050):
        print("WebSocket server running on ws://127.0.0.1:5050")
        asyncio.create_task(broadcast())
        await asyncio.Future()  # run forever

# --------------------------------------------------------------------
# Flask API Routes
# --------------------------------------------------------------------

@app.route("/ping")
def ping():
    global terminalSerObj
    userCommand = "ping"
    userArgs = ["-t"]
    terminalSerObj, response = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return response

@app.route("/comports-l", methods=['GET'])
def comports():
    global terminalSerObj
    userCommand = "comports"
    userArgs = ["-l"]
    terminalSerObj, ports = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return ports

@app.route("/comports-d", methods=['GET'])
def comports_disconnect():
    global terminalSerObj
    userCommand = "comports"
    userArgs = ["-d"]
    terminalSerObj, confirmation = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return confirmation

@app.route("/connect-p", methods=['POST'])
def connect():
    if request.method == "POST":
        global terminalSerObj
        com_port = request.get_json()["comport"]
        userCommand = "connect"
        userArgs = ["-p",com_port]
        terminalSerObj, status = sdec.command_list[userCommand](userArgs, terminalSerObj)
        return status
    return "invalid"

@app.route("/sensor-dump", methods=['GET'])
def sensor_dump():
    global terminalSerObj, shared_data, is_polling, polling_thread, request_timeout, busy_wait_break

    start_time = time.time()

    # Start polling thread on first call
    if not is_polling:
        is_polling = True
        polling_thread = threading.Thread(target=poll_sensor_data, daemon=True)
        polling_thread.start()
        print("[sensor-dump] Started background polling thread")

    while ((time.time() - start_time) <= request_timeout):
        # Return latest cached data if exists
        # else continue trying until timeout
        with shared_data.lock:
            if shared_data.dump:
                return jsonify(shared_data.dump)
        time.sleep(busy_wait_break)
    return jsonify({"message": "No response returned in the specified period."}), 500
        
@app.route("/sensor-dump-stop", methods=['GET'])
def stop_sensor_dump():
    global is_polling
    is_polling = False
    polling_thread.join()
    return "Dump Stopped."
        

def sensor_poll_dump(dumps):
    global terminalSerObj
    userCommand = "sensor"
    userArgs = ["dump"]

    for i in range(0, dumps):
        terminalSerObj, data_dump = sdec.command_list[userCommand](userArgs, terminalSerObj)
        print("yield: {0}".format(i + 1))
        yield f"data: {json.dumps(data_dump)}\n\n"
        time.sleep(0.1)

@app.route("/sensor-poll", methods=['GET'])
def sensor_poll():
    # \?time=<time>
    time = int(request.args.get('time', 100)) # Defaults to 100 sensor-dumps
    return Response(sensor_poll_dump(time), mimetype='text/event-stream')

@app.route("/get-flash-config", methods=['GET'])
def get_flash_config_data():
    global terminalSerObj
    userCommand = "read-preset"
    userArgs = [""]
    terminalSerObj, data = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return jsonify(data)

@app.route("/")
def default():
    return "Hello, welcome to SDEC-API app"

if __name__ == '__main__':
    # Start asyncio loop in a separate thread
    t = threading.Thread(target=lambda: asyncio.run(ws_open()), daemon=True)
    t.start()

    # Start Flask server in main thread
    # run() method of Flask class runs the application 
    # on the local development server.
    app.run()