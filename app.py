# General
import time
import os
import sys
import datetime
import math

# save this as app.py
from flask import Flask

# Setup path
sys.path.insert(0, './sdec')

# SDEC
import sdec

app = Flask(__name__)

@app.route("/comports-l")
def comports():
    terminalSerObj = sdec.terminalData()
    userCommand = "comports"
    userArgs = ["-l"]
    terminalSerObj, ports = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return ports

@app.route("/connect-p")
def connect():
    terminalSerObj = sdec.terminalData()
    userCommand = "connect"
    userArgs = ["-p","/dev/ttyUSB0"]
    terminalSerObj, ports = sdec.command_list[userCommand](userArgs, terminalSerObj)
    return

@app.route("/")
def default():
    return "Hello, welcome to SDEC-API app"

if __name__ == '__main__':

    # run() method of Flask class runs the application 
    # on the local development server.
    app.run()