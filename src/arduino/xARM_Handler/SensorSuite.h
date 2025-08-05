// SensorSuite.h

#ifndef SENSOR_SUITE_H
#define SENSOR_SUITE_H

#include <Arduino.h>    // ← add this!

void initSensors();
String getCurrentBlockColor();
int scanBlockRow();
bool checkIfHoldingBlock();
bool checkBlockExistsAt(int point);

#endif  // SENSOR_SUITE_H
