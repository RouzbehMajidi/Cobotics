import time
from cobot import Cobot
from swarm import Swarm
from objective import Objective
import vision
import serial
from context import Context

Context.load()

swarm = Swarm()

try:
    cobot1 = Cobot("cobot1","/dev/cu.usbmodem141240", True) #101
    swarm.add_robot(cobot1)
except ValueError:
    pass

try:
    cobot2 = Cobot("cobot2","/dev/cu.usbmodem141220", False) #Uno
    swarm.add_robot(cobot2)
except ValueError:
    pass

objective = vision.find_objective()

swarm.assign_task(objective)

try:
    swarm.start()
except(KeyboardInterrupt,SystemExit):
    swarm.stop(False)

Context.save()