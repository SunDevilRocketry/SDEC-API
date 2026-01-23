# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Sun Devil Rocketry

import atexit

from flask import Flask, request, Response
from flask_cors import CORS
from hardware import serial, sensor_sentry, serial_lock
from serial import SerialException
from typing import List

# BaseController
from sdecv2 import Firmware
# SerialController
from sdecv2 import SerialObj
# Sensor
from sdecv2 import SensorSentry
# Sensor utility
from sdecv2 import create_sensors

app = Flask(__name__)
CORS(app)

@app.route("/ping")
def ping():
    with serial_lock():
        serial.send(b"\x01")
        data = serial.read()

        if data == b"\x05":
            return "Ping response received"
        else:
            return "Ping failed"
        
@app.route("/comports")
def comports():
    return serial.available_comports()
        
@app.route("/connect", methods=["POST"])
def connect():
    data = request.get_json(silent=True)
    if not data: return "Missing POST JSON data"

    name = data.get("comport")
    timeout = data.get("timeout", 5)

    if not name: return "Missing 'comport' field"

    try:
        timeout = int(timeout)
    except (TypeError, ValueError):
        return "Invalid timeout value"
    
    try:
        serial.init_comport(name=name, baudrate=921600, timeout=timeout)

        if not serial.open_comport(): return "Failed to open comport"

        return "Connected"
    
    except SerialException as e:
        return "Serial connection error"
    
@app.route("/disconnect")
def disconnect():
    if not serial.close_comport(): return "Failed to close comport"
    return "Disconnected"
    
@app.route("/sensor-dump")
def sensor_dump():
    with serial_lock():
        sensor_dump = sensor_sentry.dump(serial)

    lines = []
    for sensor, readout in sensor_dump.items():
        val = readout if readout is not None else 0.0
        lines.append(f"{sensor.name}: {val:.2f} {sensor.unit}\n")

    return "\n".join(lines)

@app.route("/sensor-poll")
def sensor_poll():
    polls = int(request.args.get("count", 0)) # Poll count takes priority
    time = int(request.args.get("time", 0))

    def do_poll():
        with serial_lock():
            if polls: 
                iterator = sensor_sentry.poll(serial, count=polls)
            elif time:
                iterator = sensor_sentry.poll(serial, timeout=time)
            else:
                iterator = sensor_sentry.poll(serial, count=10) # No given values defaults to 10 polls

            for poll in iterator:
                for sensor, readout in poll.items():
                    val = readout if readout is not None else 0.0
                    yield f"{sensor.name}: {val:.2f} {sensor.unit}"

    return Response(do_poll(), mimetype="text/plain")

@app.route("/")
def default():
    return "Hello, welcome to the SDECv2 API"

@atexit.register
def shutdown():
    serial.close_comport()

if __name__ == "__main__":
    app.run()