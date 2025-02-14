# General
import time
import os
import sys
import datetime
import math

# save this as app.py
from flask import Flask

# Setup path
sys.path.insert(0, './plumbing')
sys.path.insert(0, './sdec')

# SDEC
import sdec
import commands
import hw_commands
import sensor_conv
import engineController

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"


if __name__ == '__main__':

    # run() method of Flask class runs the application 
    # on the local development server.
    app.run()