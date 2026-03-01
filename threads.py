# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Sun Devil Rocketry

import threading
import time

from hardware import serial_lock
from SDECv2 import SerialObj, SensorSentry
from typing import Dict
from util import make_safe_number

POLL_INTERVAL = 0.1 # In seconds

def poll_dashboard_dump(serial_connection: SerialObj, data_dict, stop_event: threading.Event):
    while not stop_event.is_set():
        with serial_lock():
            dashboard_dump = SensorSentry.dashboard_dump(serial_connection)

        curr_dashboard_dump = {}
        for sensor, readout in dashboard_dump.items():
            val = make_safe_number(readout)
            curr_dashboard_dump[sensor.name] = {
                "value": val,
                "unit": sensor.unit
            }

        data_dict.clear()
        data_dict.update(curr_dashboard_dump)

        time.sleep(POLL_INTERVAL)