# General
import threading
import time
import os
import sys
import datetime
import math
import json

# save this as app.py
from flask import Flask, request, Response
from flask_cors import CORS
# Setup path
sys.path.insert(0, './sdec')

# SDEC
import sdec

from sdec import sdec

terminalSerObj = sdec.terminalData()

app = Flask(__name__)
CORS(app)

# Global terminalSerObj
terminalSerObj = sdec.terminalData()
is_polling = False

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
    global terminalSerObj
    userCommand = "sensor"
    userArgs = ["dump"]
    terminalSerObj, data_dump = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return data_dump

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

@app.route("/")
def default():
    return "Hello, welcome to SDEC-API app"

if __name__ == '__main__':

    # run() method of Flask class runs the application 
    # on the local development server.
    app.run()