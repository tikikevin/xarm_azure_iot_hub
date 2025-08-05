#include <SoftWire.h>
#include <Adafruit_APDS9960.h>
#include <Arduino.h>    // for Serial
#include "SensorSuite.h"
#include "Ultrasound.h"

#define SDA             6
#define SCL             7
#define PHOTOSENSITIVE  A2
#define ULTRASOUND_I2C_ADDR 0x77

Ultrasound sonar;
SoftWire sw(SDA, SCL);
Adafruit_APDS9960 apds(sw);

void initSensors() {
  if (!apds.begin()) {
    Serial.println("APDS9960 not found");
  }
  apds.enableColor(true);
}

String getCurrentBlockColor() {
  uint16_t r, g, b, c;
  apds.getColorData(&r, &g, &b, &c);   // just call it

  if (r > g && r > b)      return "red";
  else if (g > r && g > b) return "green";
  else if (b > r && b > g) return "blue";
  else                     return "unknown";
}

int scanBlockRow() {
  uint16_t distance;
  sonar.wireReadDataArray(ULTRASOUND_I2C_ADDR, 0, (uint8_t*)&distance, 2);

  if (distance < 100) return 4;
  else if (distance < 200) return 5;
  else if (distance < 300) return 6;
  else return -1;  // no block detected
}

bool checkIfHoldingBlock() {
  
  int brightness = map(analogRead(PHOTOSENSITIVE), 0, 1023, 100, 0);
  return brightness < 15;
}

bool checkBlockExistsAt(int point) {
  switch (point) {
    case 1: return digitalRead(3);
    case 2: return digitalRead(4);
    case 3: return digitalRead(5);
    default: return false;
  }
}
