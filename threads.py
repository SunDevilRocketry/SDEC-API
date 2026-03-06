# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Sun Devil Rocketry

import threading
import time

from hardware import serial_lock
from SDECv2 import SerialObj, SensorSentry
from typing import Dict
from util import make_safe_number

POLL_INTERVAL = 1/60 # In seconds, target is 60 Hz

def poll_dashboard_dump(serial_connection: SerialObj, data_dict, stop_event: threading.Event):
    next_time = time.perf_counter()
   
    while not stop_event.is_set():
        next_time += POLL_INTERVAL

        with serial_lock():
            dashboard_dump = SensorSentry.dashboard_dump(serial_connection)

        curr_dashboard_dump = {}
        for sensor, readout in dashboard_dump.items():
            val = make_safe_number(readout)
            curr_dashboard_dump[sensor.short_name] = val

        data_dict.clear()
        data_dict.update(curr_dashboard_dump)

        sleep_time = next_time - time.perf_counter()
        if sleep_time > 0: 
            time.sleep(sleep_time)
        else:
            next_time = time.perf_counter()