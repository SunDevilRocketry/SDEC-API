# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Sun Devil Rocketry

import threading
import time

from hardware import serial_lock
from SDECv2 import SerialObj, SensorSentry, Telemetry
from typing import Dict
from util import make_safe_number

POLL_INTERVAL = 1/60 # In seconds, target is 60 Hz

def poll_dashboard_dump(serial_connection: SerialObj, stop_event: threading.Event, telemetry_obj: Telemetry):
    next_time = time.perf_counter()
   
    while not stop_event.is_set():
        next_time += POLL_INTERVAL

        with serial_lock():
            telemetry_obj.dashboard_dump(serial_connection)

        sleep_time = next_time - time.perf_counter()
        if sleep_time > 0: 
            time.sleep(sleep_time)
        else:
            next_time = time.perf_counter()