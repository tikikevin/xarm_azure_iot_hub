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
  if (cmd.startsWith("get_block")) {
    int point = cmd.substring(10).toInt();
    bool ok = getBlockAt(point);
    snprintf(response, sizeof(response), "get_block %d: %s", point, ok?"true":"false");


  // PUT BLOCK X
  } else if (cmd.startsWith("put_block")) {
    int point = cmd.substring(10).toInt();
    bool ok = putBlockAt(point);
    snprintf(response, sizeof(response), "put_block %d: %s", point, ok?"true":"false");

  // GET COLOR
  } else if (cmd.startsWith("get_color")) {
    String c = getCurrentBlockColor();
    snprintf(response, sizeof(response), "get_color %s : %s", c);

  // HOLDING BLOCK
  } else if (cmd.startsWith("holding_block")) {
    putBlockHoldingCheck();
    bool holding = checkIfHoldingBlock();
    if(holding == true){
      getBlockHoldingCheck();
    }
    snprintf(response, sizeof(response), "holding_block: %s", holding?"true":"false");

  // BLOCK EXISTS X
  } else if (cmd.startsWith("block_exists")) {
    int point = cmd.substring(13).toInt();
    bool exists = checkBlockExistsAt(point);
    snprintf(response, sizeof(response), "block_exists %d : %s", point, exists?"true":"false");

  // SCAN ROW
  } else if (cmd.startsWith( "scan_row")) {
    int pos = scanBlockRow();
    snprintf(response, sizeof(response), "scan_row %d : %s", pos);

  } else {
    snprintf(response, sizeof(response), "command unknown");
  }

  // Print response to Python and local display
  Serial.println(response);
  setDisplayMessage(response);
}
