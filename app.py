# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Sun Devil Rocketry

import atexit

from flask import Flask, request, Response
from flask_cors import CORS
from hardware import serial, sensor_sentry, serial_lock
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
    return "Hello, welcome to the SDECv2-API"

@atexit.register
def shutdown():
    serial.close_comport()

if __name__ == "__main__":
    app.run()