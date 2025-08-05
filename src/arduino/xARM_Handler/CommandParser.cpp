#include "CommandParser.h"
#include <Arduino.h>
#include "xArmCommands.h"
#include "SensorSuite.h"
#include "DisplayUI.h"

void initParser() {
  Serial.begin(9600);
  initArm();        // from xArmCommands
  initSensors();    // from SensorSuite
  initDisplay();    // from DisplayUI
}

void processSerialCommands() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  char response[32];

  // GET BLOCK X
  if (cmd.startsWith("GET BLOCK")) {
    int point = cmd.substring(10).toInt();
    bool ok = getBlockAt(point);
    snprintf(response, sizeof(response), "GET BLOCK %d: %s", point, ok?"true":"false");


  // PUT BLOCK X
  } else if (cmd.startsWith("PUT BLOCK")) {
    int point = cmd.substring(10).toInt();
    bool ok = putBlockAt(point);
    snprintf(response, sizeof(response), "PUT BLOCK %d: %s", point, ok?"true":"false");

  // GET COLOR
  } else if (cmd == "GET COLOR") {
    String c = getCurrentBlockColor();
    snprintf(response, sizeof(response), "GET COLOR %s : %s", c);

  // HOLDING BLOCK
  } else if (cmd == "HOLDING BLOCK") {
    putBlockHoldingCheck();
    bool holding = checkIfHoldingBlock();
    if(holding == true){
      getBlockHoldingCheck();
    }
    snprintf(response, sizeof(response), "HOLDING: %s", holding?"true":"false");

  // BLOCK EXISTS X
  } else if (cmd.startsWith("BLOCK EXISTS")) {
    int point = cmd.substring(13).toInt();
    bool exists = checkBlockExistsAt(point);
    snprintf(response, sizeof(response), "BLOCK EXISTS %d : %s", point, exists?"true":"false");

  // SCAN ROW
  } else if (cmd == "SCAN ROW") {
    int pos = scanBlockRow();
    snprintf(response, sizeof(response), "SCAN RESULT %d : %s", pos);

  } else {
    snprintf(response, sizeof(response), "UNKNOWN COMMAND");
  }

  // Print response to Python and local display
  Serial.println(response);
  setDisplayMessage(response);
}
