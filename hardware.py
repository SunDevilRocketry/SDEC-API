import threading

# BaseController
from SDECv2 import Firmware
# SerialController
from SDECv2 import SerialObj
# Sensor
from SDECv2 import SensorSentry
# Sensor utility
from SDECv2 import create_sensors

# Serial connection lock
_serial_lock = threading.Lock()

# APPA Firmware
firmware = Firmware(
    id=b"\x06",
    name="APPA",
    preset_frame_size=0,
    preset_file=""
)

# SensorSentry with all APPA sensors
sensors = create_sensors.flight_computer_rev2_sensors()
sensor_sentry = SensorSentry()
for sensor in sensors: sensor_sentry.add_sensor(sensor)

# Serial connection 
serial_connection = SerialObj()

def serial_lock():
    return _serial_lock