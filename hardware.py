import threading

# BaseController
from sdecv2 import Firmware
# SerialController
from sdecv2 import SerialObj
# Sensor
from sdecv2 import SensorSentry
# Sensor utility
from sdecv2 import create_sensors

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
serial = SerialObj()
serial.init_comport(name="COM3", baudrate=921600, timeout=5)
serial.open_comport() # TODO consider moving to an api call

def serial_lock():
    return _serial_lock