# General
import threading
import time
import os
import sys
import datetime
import math
import json
import asyncio

# save this as app.py
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
# Setup path
sys.path.insert(0, './sdec')

# SDEC
import sdec
import ws

terminalSerObj = sdec.terminalData()

app = Flask(__name__)
CORS(app)

# Globals for sensor dump
is_polling = False
latest_data_dump = None
polling_thread = None
poll_interval = 0.01666666  # seconds, adjust as needed
request_timeout = 5 # seconds before timeout
busy_wait_break = 0.03 # seconds between response tries

# --------------------------------------------------------------------
# Sensor Dump Thread
# --------------------------------------------------------------------
def poll_sensor_data():
    """Continuously run 'sensor dump' command and cache the result."""
    global terminalSerObj, latest_data_dump, is_polling

    if terminalSerObj.firmware == 'APPA':
        userCommand = "dashboard-dump"
        userArgs = []
    else:
        userCommand = "sensor"
        userArgs = ["dump"]

    while is_polling:
        start_time = time.time()
        try:
            terminalSerObj, data_dump = sdec.command_list[userCommand](userArgs, terminalSerObj)
            # sanitize invalid values
            for key in data_dump:
                if math.isinf(data_dump[key]):
                    data_dump[key] = 999999
            latest_data_dump = data_dump
        except Exception as e:
            print(f"[poll_sensor_data] Error: {e}")
            is_polling = False
        elapsed_time = time.time() - start_time # print this value for debugging
        time.sleep( max( poll_interval - elapsed_time, 0 ) ) # sleep if not reached interval yet

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
    global terminalSerObj, latest_data_dump, is_polling, polling_thread, request_timeout, busy_wait_break

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
        if latest_data_dump is not None:
            return jsonify(latest_data_dump)
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
    t = threading.Thread(target=ws.ws_main, daemon=True)
    t.start()

    # Start Flask server in main thread
    # run() method of Flask class runs the application 
    # on the local development server.
    app.run()