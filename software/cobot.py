import numpy as np
import json
import threading
import uuid
import serial

CMD_FWD = b'F\n'
CMD_BACK = b'B\n'
CMD_LEFT = b'L\n'
CMD_RIGHT = b'R\n'
CMD_STOP = b'S\n'

distance_moving_avg_size = 10
acceleration_moving_avg_size = 10

STUCK_THRESHOLD = -0.1
DISTANCE_THRESHOLD = 20

def running_mean(x, N):
        cumsum = np.cumsum(np.insert(x, 0, 0))
        return (cumsum[N:] - cumsum[:-N]) / float(N)

class Cobot(threading.Thread):
    CAPACITY = 3 #Newton

    def __init__(self, name, serial_link, is_smart):
        self.id = name + "-" + str(uuid.uuid4())[:6]
        try:
            self.serial = serial.Serial(serial_link, 9600)
        except Exception as err:
            print("ERROR:", self.id, "not available:", str(err))
            raise ValueError

        self.current_cmd = 'S'
        self.run_time = 0
        self.distances = []
        self.accelerometer_data = []
        self.is_active = True
        self.is_stuck = False
        self.is_smart = is_smart
        self.is_helping = False
        self.has_helper = False
        self.leader = None
        self.BACK_OFF_PERIOD = 2
        self.back_off_timer = self.BACK_OFF_PERIOD
        self.data = {}
        self.objective = None

    def forward(self):
        self.current_cmd = 'F'
        self.serial.write(CMD_FWD)
        print( self.id,": forward")

    def backward(self):
        self.current_cmd = 'B'
        self.serial.write(CMD_BACK)
        print(self.id,": backward")

    def left(self):
        self.current_cmd = 'L'
        self.serial.write(CMD_LEFT)
        print(self.id,": left")

    def right(self):
        self.current_cmd = 'R'
        self.serial.write(CMD_RIGHT)
        print(self.id,": right")
    
    def stop(self):
        self.current_cmd = 'S'
        self.serial.write(CMD_STOP)
        print(self.id,": stop")

    def assign_objective(self, objective, leader=None):
        self.is_active = True
        self.objective = objective
        self.leader = leader
    
    def update_data(self):
        try:
            self.data = json.loads(self.serial.readline().strip().decode('utf-8'))
        except json.decoder.JSONDecodeError:
            print("JSON Error")
            pass
        except UnicodeDecodeError:
            print("UTF-8 Error")
            pass
        return self.data

    def command_ackd(self):
        try:
            return self.data["current_cmd"] == self.current_cmd
        except:
            return True

    def retry_last_cmd(self):
        if(self.back_off_timer != 0):
            self.back_off_timer -= 1
            return

        if(self.current_cmd == 'S'):
            self.stop()
        elif (self.current_cmd == 'F'):
            self.forward()
        elif (self.current_cmd == 'B'):
            self.backward()
        elif (self.current_cmd == 'R'):
            self.right()
        elif (self.current_cmd == 'L'):
            self.left()
        else:
            print(self.id, "Invalid Command State")
            pass
        
        self.back_off_timer = 2*self.BACK_OFF_PERIOD

    def get_distance_data(self):
        try:
            distance = self.data["us_data"]
        except KeyError:
            return None

        if(distance):
            self.distances.append(distance)

            if len(self.distances) > distance_moving_avg_size:
                self.distances = self.distances[len(self.distances)-distance_moving_avg_size:]
                distance = running_mean(self.distances,10)[-1]

            self.distance = distance
            
            print(self.id, "Distance:", distance, "cm")
            return distance
        else:
            return None

    def get_acceleration_data(self):
        try:
            acc_data = self.data["acc_data"][0]
        except KeyError:
            return None

        if(acc_data):
            self.accelerometer_data.append(acc_data)

            if len(self.accelerometer_data) > acceleration_moving_avg_size:
                self.accelerometer_data = self.accelerometer_data[len(self.accelerometer_data)-acceleration_moving_avg_size:]
                acc_data = running_mean(self.accelerometer_data,5)[-1]

            print(self.id, "Forward Acceleration:", acc_data)
            return acc_data
        else:
            return None

    def near_obstacle(self):
        self.get_distance_data()
        if self.distance and self.distance > 0 and self.distance < DISTANCE_THRESHOLD:
            print(self.id, "NEAR OBSTACLE - stopping operations")
            return True
        else:
            return False

    def check_progress(self):
        if self.has_helper:
            return False
        elif self.is_stuck:
            return True

        acc_data = self.get_acceleration_data()

        if acc_data and self.current_cmd == 'F' and self.command_ackd() and acc_data < STUCK_THRESHOLD:
            print(self.id, "STUCK - stopping operations")
            self.is_stuck = True
            self.accelerometer_data = np.zeros(10).tolist()
            print(self.run_time)
        else:
            self.run_time += 1
            self.is_stuck = False

        return self.is_stuck
