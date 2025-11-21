# General
import threading
import time
import os
import sys
import datetime
import math
import json
import traceback
import queue

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
usb_poll_interval = 0.01666666  # seconds, adjust as needed
wireless_poll_interval = 0.1 # seconds, adjust as needed
poll_interval = 0
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
        poll_interval = usb_poll_interval
    elif terminalSerObj.firmware == 'Receiver':
        userCommand = "lora-recieve-next"
        userArgs = []
        throwaway = None
        poll_interval = wireless_poll_interval
    else:
        print("Unsupported Firmware!")
        is_polling = False

    while is_polling:
        start_time = time.time()
        try:
            terminalSerObj, outcome = sdec.command_list[userCommand](userArgs, terminalSerObj)
        except Exception as e:
            print(f"[poll_sensor_data] Error: {e}")
            traceback.print_exc()
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

        # Check if GS connected
        if terminalSerObj.firmware == 'Receiver':
            # Run telem setting upload command
            userCommand = "telem"
            userArgs = ["upload", "sdec/input/telem.cfg"]
            terminalSerObj, _ = sdec.command_list[userCommand](userArgs, terminalSerObj)
        return status
    return "invalid"

# Dummy route for now
@app.route("/wireless-stats", methods=['GET'])
def wireless_stats():
    if terminalSerObj and terminalSerObj.firmware == 'Receiver':
        return jsonify(sdec.dashboard.vehicle_id)
    else:
        return Response("No wireless target available.", status=204)

@app.route("/next-msg", methods=['GET'])
def next_msg():
    try:
        return jsonify(sdec.dashboard.get_next_msg())
    except queue.Empty:
        return Response(status=204)

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
        if sdec.dashboard.latest_data_dump is not None:
            return jsonify(sdec.dashboard.latest_data_dump)
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

    # run() method of Flask class runs the application 
    # on the local development server.
    app.run()