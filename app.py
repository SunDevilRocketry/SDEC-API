# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Sun Devil Rocketry

from flask import Flask
from flask_cors import CORS
from sdecv2 import SerialObj

app = Flask(__name__)
CORS(app)

@app.route("/ping")
def ping():
    serial_connection = SerialObj()
    serial_connection.init_comport(name="COM3", baudrate=921600, timeout=5)
    serial_connection.open_comport()
    serial_connection.send(b"\x01")
    data = serial_connection.read()

    if data == b"\x05":
        serial_connection.close_comport()
        return "Ping response received"
    else:
        serial_connection.close_comport()
        return "Ping failed"

@app.route("/")
def default():
    return "Hello, welcome to the SDECv2-API"

if __name__ == "__main__":
    app.run()