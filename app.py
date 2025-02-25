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

@app.route("/ping")
def ping():
    terminalSerObj = sdec.terminalData()
    userCommand = "ping"
    userArgs = ["-t"]
    terminalSerObj, response = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return response

@app.route("/comports-l", methods=['GET'])
def comports():
    terminalSerObj = sdec.terminalData()
    userCommand = "comports"
    userArgs = ["-l"]
    terminalSerObj, ports = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return ports

@app.route("/comports-d", methods=['GET'])
def comports_disconnect():
    terminalSerObj = sdec.terminalData()
    userCommand = "comports"
    userArgs = ["-d"]
    terminalSerObj, confirmation = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return confirmation

@app.route("/connect-p", methods=['POST'])
def connect():
    if request.method == "POST":
        com_port = request.get_json()["comport"]
        terminalSerObj = sdec.terminalData()
        userCommand = "connect"
        userArgs = ["-p",com_port]
        terminalSerObj, status = sdec.command_list[userCommand](userArgs, terminalSerObj)
        return status
    return "invalid"

@app.route("/")
def default():
    return "Hello, welcome to SDEC-API app"

if __name__ == '__main__':

    # run() method of Flask class runs the application 
    # on the local development server.
    app.run()