# General
import time
import os
import sys
import datetime
import math

# save this as app.py
from flask import Flask, request
from flask_cors import CORS
# Setup path
sys.path.insert(0, './sdec')

# SDEC
import sdec

app = Flask(__name__)
CORS(app)

terminalSerObj = sdec.terminalData()

@app.route("/comports-l", methods=['GET'])
def comports():
    global terminalSerObj
    userCommand = "comports"
    userArgs = ["-l"]
    print(terminalSerObj)
    terminalSerObj, ports = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return ports

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

@app.route("/data-dump", methods=['GET'])
def sensor_dump():
    global terminalSerObj
    userCommand = "sensor"
    userArgs = ["dump"]
    terminalSerObj, sensor_data_dict = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return sensor_data_dict
# TODO: Impl comports -d (Disconnect active port)
#       Impl "ping"       : commands.ping


@app.route("/")
def default():
    return "Hello, welcome to SDEC-API app"

if __name__ == '__main__':

    # run() method of Flask class runs the application 
    # on the local development server.
    app.run()