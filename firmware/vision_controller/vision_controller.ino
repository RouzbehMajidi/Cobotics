#include "ArduinoJson.h" //Make sure to have non-beta version of ArduinoJson 
#include "NewPing.h"

#define MAX_DISTANCE 400

const int US_TRIG_PIN = 4;
const int US_ECHO_PIN = 3;

float distanceCm;
float prevDistanceCm = 31;

const int BAUD_RATE = 9600;

NewPing sonar(US_TRIG_PIN, US_ECHO_PIN, MAX_DISTANCE);

void setup() {
  Serial.begin(BAUD_RATE);
}

void loop() {
  distanceCm = getUSData();
  if (distanceCm != 0){
    Serial.println(distanceCm);
    prevDistanceCm = distanceCm;
  } else{
    Serial.println(prevDistanceCm);
  }

  
}

float getUSData(){
  delay(50);
  return sonar.ping_cm();
}
