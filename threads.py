import threading
import time

from hardware import serial_lock
from SDECv2 import SerialObj, SensorSentry
from typing import Dict
from util import make_safe_number

POLL_INTERVAL = 0.1 # In seconds

def poll_dashboard_dump(serial_connection: SerialObj, data_dict: Dict[str, str], stop_event: threading.Event):
    while not stop_event.is_set():
        with serial_lock():
            sensor_dump = SensorSentry.dashboard_dump(serial_connection)

        for sensor, readout in sensor_dump.items():
            val = make_safe_number(readout)
            data_dict[sensor.name] = {
                "value": val,
                "unit": sensor.unit
            }

        time.sleep(1)