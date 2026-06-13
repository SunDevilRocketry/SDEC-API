# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Sun Devil Rocketry

import atexit
import threading

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from hardware import serial_connection, sensor_sentry, serial_lock, firmware # Objects from hardware.py
from serial import SerialException
from threads import poll_dashboard_dump
from typing import List, Dict
from util import make_safe_number

# BaseController
from SDECv2 import BaseController, Controller, Firmware, create_controllers, create_firmwares
# SerialController
from SDECv2 import SerialObj
# Sensor
from SDECv2 import SensorSentry
# Parser
from SDECv2 import Telemetry
# Sensor utility
from SDECv2 import create_sensors

app = Flask(__name__)
CORS(app)

# Globals for polling dashboard dump
stop_event = threading.Event()
telemetry_obj = Telemetry()
dashboard_dump_thread = threading.Thread(target=poll_dashboard_dump, 
                                         args=(serial_connection, stop_event, telemetry_obj), 
                                         daemon=True)

@app.route("/ping")
def ping():
    with serial_lock():
        serial_connection.send(b"\x01")
        data = serial_connection.read()

        if data == b"\x05" or data == b'\x10': #should not hardcode
            return "Ping response received"
        else:
            return "Ping failed"
        
@app.route("/comports")
def comports():
    return serial_connection.available_comports()
        
@app.route("/connect", methods=["POST"])
def connect():
    # Set up handling for request
    connected = False
    data = request.get_json(silent=True)
    if not data: return "Missing POST JSON data"

    name = data.get("comport")
    timeout = data.get("timeout", 5)

    if not name: return "Missing 'comport' field"

    try:
        timeout = int(timeout)
    except (TypeError, ValueError):
        return "Invalid timeout value"
    
    # Check for an existing connection
    if serial_connection.target is not None:
        connected = True
    
    # Initialize a new connection if one does not exist
    if not connected:
        try:
            with serial_lock():
                serial_connection.init_comport(name=name, baudrate=921600, timeout=timeout)

                if not serial_connection.open_comport(): return "Failed to open comport"

                # send connect opcode
                serial_connection.connect()

                if( serial_connection.target is None ):
                    return Response("Serial connection failed.", status=400)
                else:
                    connected = True
        
        except SerialException as e:
            return Response("Serial connection error", status=400)
    
    # Return connection status
    if connected and serial_connection.target is not None:
        return jsonify({
            "controller": {
                "firmware": serial_connection.target.firmware.name,
                "name": serial_connection.target.controller.name
            },
            "status": "connected"
        })
    else: # Shouldn't get here -- protective case
        return Response("Serial connection failed (server-side error).", status=500)
    
@app.route("/disconnect")
def disconnect():
    with serial_lock():
        if not serial_connection.close_comport(): return "Failed to close comport"
        return "Disconnected"

@app.route("/wireless-stats")
def wireless_stats():
    if serial_connection.target is None:
        return Response("Not connected to a target.", status=400)
    elif serial_connection.target.firmware.id == b'\x11':
        return telemetry_obj.get_latest_wireless_stats()
    else:
        return Response("No wireless target available.", status=204)
    
@app.route("/dashboard-dump", methods=["GET", "POST"])
def dashboard_dump():
    if request.method == "GET":
        return jsonify(telemetry_obj.get_latest_dashboard_dump())
    
    elif request.method == "POST":
        data = request.get_json(silent=True)
        if not data: return "Missing POST JSON data"

        start = data.get("start")
        stop = data.get("stop")

        if bool(start) == bool(stop): return Response("Only start XOR stop can be set", status=400)

        if start:
            if dashboard_dump_thread.is_alive(): # Protective case
                return Response("Polling was already running", status=204)
            else:
                stop_event.clear()
                dashboard_dump_thread.start()
                return Response("Dashboard-dump poll started", status=200)
        elif stop:
            if not dashboard_dump_thread.is_alive(): # Protective case
                return Response("Polling was already stopped", status=204)
            else:
                stop_event.set()
                return Response("Dashboard-dump poll stopped", status=200)
    
    return Response("Invalid condition", status=400)
    
@app.route("/sensor-dump")
def sensor_dump():
    with serial_lock():
        sensor_dump = sensor_sentry.dump(serial_connection)

    data_dict = {}
    for sensor, readout in sensor_dump.items():
        val = make_safe_number(readout)
        data_dict[sensor.short_name] = val

    return data_dict

@app.route("/sensor-poll")
def sensor_poll():
    polls = int(request.args.get("count", 0)) # Poll count takes priority
    time = int(request.args.get("time", 0))

    def do_poll():
        with serial_lock():
            if polls: 
                iterator = sensor_sentry.poll(serial_connection, count=polls)
            elif time:
                iterator = sensor_sentry.poll(serial_connection, timeout=time)
            else:
                iterator = sensor_sentry.poll(serial_connection, count=10) # No given values defaults to 10 polls

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
    try: serial_connection.close_comport()
    except: pass
    stop_event.set()
    if dashboard_dump_thread.is_alive(): dashboard_dump_thread.join()

if __name__ == "__main__":
    app.run()