import os
import sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from uarm.wrapper import SwiftAPI

#Initialize Swift Parameters
swift = SwiftAPI(filters={'hwid': 'USB VID:PID=2341:0042'})
swift.waiting(timeout=3)
speed = 250
swift.set_mode(0)
swift.set_height_offset(offset=45)

x = 100
y = 0
z = 150

swift.reset(wait=True, speed=speed)
swift.set_position(x=x, speed=speed)
swift.set_position(y=y)
swift.set_position(z=z)
swift.flush_cmd(wait_stop=True)
