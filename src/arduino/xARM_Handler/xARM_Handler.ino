#include "CommandParser.h"
#include "DisplayUI.h"

void setup() {
  initParser();
  // Optionally show a welcome message
  setDisplayMessage("xARM Ready");
}

void loop() {
  processSerialCommands();
  drawDisplay();
}