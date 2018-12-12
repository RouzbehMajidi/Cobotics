from cobot import Cobot
from objective import Objective
import threading
import time
import math
import uuid
from context import Context

HELP_DISTANCE_MIN = 15
HELP_DISTANCE_MAX = 70
START_DELAY =  5 #seconds

def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

class Swarm:
    def __init__(self):
        self.id = "swarm-" + str(uuid.uuid4())[:6]
        self.cobots = set()
        self.objective = None
        self.running = False
        self.start_time = -1
        self.stop_time = -1
        self.total_ticks = 0

    def add_robot(self, cobot):
        cobot.stop()
        self.cobots.add(cobot)

    def remove_robot(self,cobot):
        cobot.stop()
        self.cobots.remove(cobot)

    def stop(self, is_emergency_stop):
        print(self.id, "Stopping Swarm")

        self.running = False
        self.stop_time = int(round(time.time() * 1000))

        total_run_time = float((self.stop_time - self.start_time)/1000)*0.1

        for cobot in self.cobots:
            cobot.stop()
            while(not cobot.command_ackd()):
                cobot.update_data()
                cobot.retry_last_cmd()
                time.sleep(0.1)

        if not is_emergency_stop:
            print(self.id, "Robots returning to base")
            for cobot in self.cobots:
                cobot.stop()
                time.sleep(0.5)
                if self.total_ticks != 0:
                    return_time = (cobot.run_time/self.total_ticks)*total_run_time
                if return_time > 0:
                    cobot.backward()
                    while(not cobot.command_ackd()):
                        cobot.update_data()
                        cobot.retry_last_cmd()
                        time.sleep(0.1)
                    time.sleep(return_time)
                    cobot.stop()
                print("\t", cobot.id, "stopped")

        if self.objective.is_heavier:
            print(self.id, ":", "Objective was heavier than expected, increasing density assumption")
            Context.DENSITY += 0.3

    def get_available_robots(self):
        return [cobot for cobot in self.cobots if not cobot.objective and not cobot.is_stuck]

    def get_active_robots(self):
        return [cobot for cobot in self.cobots if cobot.objective and cobot.is_active]

    def assign_task(self, objective):
        if self.objective != None:
            return
        else:
            self.objective = objective
        
        work_factor = math.ceil(objective.get_force_required() / Cobot.CAPACITY)

        if(work_factor <= len(self.cobots)):
            i = 0
            for cobot in sorted(self.cobots, key=lambda cobot: cobot.is_smart, reverse=True):
                if(i == work_factor):
                    break
                if(not cobot.objective):
                    cobot.assign_objective(self.objective)
                    i += 1

            print(self.id, ": objective added to swarm")
            print(objective.id, "Work factor: ", work_factor)
        else:
            raise ValueError(self.id, "ERROR: ", work_factor, " robots required for this objective, while ", len(self.cobots), " currently exist in swarm")

    def start(self):
        if(len(self.cobots) == 0):
            raise ValueError(self.id, "ERROR: No robots in swarm")

        self.running = True
        self.start_time = int(round(time.time() * 1000))

        print("Swarm activating in",START_DELAY,"seconds")
        time.sleep(START_DELAY)

        while self.running:
            if(len(self.get_active_robots()) == 0 and len(self.get_available_robots()) == 0):
                print(self.id, ": No active robots in swarm")
                self.stop(False)

            for cobot in self.cobots:
                print(cobot.id, ":", cobot.update_data())

                if(cobot.is_active and cobot.objective):
                    is_stuck = cobot.check_progress()
                    distance_data = cobot.get_distance_data()

                    if(cobot.is_helping and distance_data and (distance_data < HELP_DISTANCE_MIN or distance_data > HELP_DISTANCE_MAX)):
                        print("STARTING HELPER")
                        cobot.stop()
                        cobot.is_helping = False
                        cobot.leader.is_active = True
                        cobot.leader.is_stuck = False
                        cobot.leader.has_helper = True
                    
                    if(is_stuck and len(self.get_available_robots()) > 0):
                        print(cobot.id, ":", "ROBOT STUCK - REQUESTING HELP")
                        helper_cobot = self.get_available_robots()[0]
                        helper_cobot.assign_objective(self.objective, cobot)
                        helper_cobot.is_helping = True
                        self.objective.is_heavier = True
                        continue
                    elif(is_stuck):
                        print(cobot.id, ":", "ROBOT STUCK - NO HELP AVAILABLE")
                        cobot.stop()
                        cobot.is_active = False
                        self.objective.is_heavier = True
                        print(cobot.id, ":", cobot.id, " deactivated")
                    elif(not cobot.command_ackd()):
                        print(cobot.id, ":", "RETRYING LAST COMMAND")
                        cobot.retry_last_cmd()
                    elif(not cobot.current_cmd == 'F'):
                        cobot.forward()
            
            self.total_ticks += 1
                


