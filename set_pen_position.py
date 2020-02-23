import os
import sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from uarm.wrapper import SwiftAPI

#Initialize Swift Parameters
swift = SwiftAPI(filters={'hwid': 'USB VID:PID=2341:0042'})
swift.waiting_ready(timeout=3)
device_info = swift.get_device_info()
print(device_info)
firmware_version = device_info['firmware_version']
if firmware_version and not firmware_version.startswith(('0.', '1.', '2.', '3.')):
    swift.set_speed_factor(0.0005)
swift.set_mode(0)
speed = 20000

#Go to Z=0
swift.reset(wait=True, z=50, speed=speed)
swift.set_position(x=200, speed=speed)
swift.set_position(y=0)
swift.set_position(z=0)
swift.flush_cmd(wait_stop=True)

#Wait for Confirm then Reset
confirm = input('Enter any key to continue')
swift.reset(wait=True, z=50, speed=speed)
swift.disconnect()
