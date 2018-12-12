#include "Servo.h"
#include "ArduinoJson.h" //Make sure to have non-beta version of ArduinoJson 
#include "NewPing.h"

#define MAX_DISTANCE 200

const int BL_MOTOR_PIN = 6;
const int BR_MOTOR_PIN = 5;
const int FL_MOTOR_PIN = 9;
const int FR_MOTOR_PIN = 4;

const int US_TRIG_PIN = 3;
const int US_RECV_PIN = 13;

const char CMD_FWD = 'F';
const char CMD_BACK = 'B';
const char CMD_RIGHT = 'R';
const char CMD_LEFT = 'L';
const char CMD_STOP = 'S';

const int BAUD_RATE = 9600;

const size_t bufferSize = JSON_ARRAY_SIZE(3) + JSON_OBJECT_SIZE(2);

char CURRENT_CMD = 'S';

int speed = 12;
const int neutral = 90;

Servo servo_FL;
Servo servo_FR;
Servo servo_BL;
Servo servo_BR;

float ax, ay, az;
float distanceCm;


NewPing sonar(US_TRIG_PIN, US_RECV_PIN, MAX_DISTANCE);

void setup() {
  Serial.begin(BAUD_RATE);
  servo_FL.attach(FL_MOTOR_PIN);
  servo_FR.attach(FR_MOTOR_PIN);
  servo_BL.attach(BL_MOTOR_PIN);
  servo_BR.attach(BR_MOTOR_PIN);
  stop();

}
void loop() {
  getUSData();

  DynamicJsonBuffer jsonBuffer(bufferSize);
  JsonObject& root = jsonBuffer.createObject();
  root["id"] = "Cobot2";
  root["current_cmd"] = String(CURRENT_CMD);
  root["us_data"] = distanceCm;
  root.printTo(Serial);
  Serial.println();

  while (Serial.available() > 0) {
    CURRENT_CMD = Serial.readString().charAt(0);
  }

  switch (CURRENT_CMD) {
    case CMD_FWD:
      forward(speed);
      break;
    case CMD_BACK:
      backward(speed);
      break;
    case CMD_RIGHT:
      right(speed);
      break;
    case CMD_LEFT:
      left(speed);
      break;
    case CMD_STOP:
      stop();
      break;
  }
  
  Serial.flush();
  delay(50);
}

void forward(int speed) {
  // servo_FL.write(neutral + speed);
  servo_BL.write(neutral + speed);
  servo_FR.write(neutral - speed);
  servo_BR.write(neutral - speed);
}

void backward(int speed) {
  servo_FL.write(neutral - speed);
  servo_BL.write(neutral - speed);
  servo_FR.write(neutral + speed);
  servo_BR.write(neutral + speed);
}

void left(int speed) {
  servo_FL.write(neutral - speed);
  servo_BL.write(neutral - speed);
  servo_FR.write(neutral - speed);
  servo_BR.write(neutral - speed);
}

void right(int speed) {
  servo_FL.write(neutral + speed);
  servo_BL.write(neutral + speed);
  servo_FR.write(neutral + speed);
  servo_BR.write(neutral + speed);
}

void stop() {
  servo_FL.write(neutral);
  servo_BL.write(neutral);
  servo_FR.write(neutral);
  servo_BR.write(neutral);
}

void getUSData() {
  distanceCm = sonar.ping_cm();
}
