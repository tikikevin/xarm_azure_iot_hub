#include "xArmCommands.h"
#include "SoftwareSerial.h"
#include "LobotServoController.h"

#define RxPin 8
#define TxPin 9

SoftwareSerial armSerial(RxPin, TxPin);
LobotServoController armController(armSerial);

void callActionGroup(int id){
  armController.runActionGroup(id, 1);
  delay(500);  // Need to wait before looking at the xARM buffer
  armController.receiveHandler();
  delay(100);

  // Wait for action group to complete
  while (armController.actionGroupRunning() != -1) {
    armController.receiveHandler();
    delay(500);
  }
}

void initArm() {
  armSerial.begin(9600);
}

void putBlockHoldingCheck(){
  callActionGroup(25);
}

void getBlockHoldingCheck(){
  callActionGroup(26);
}


int getActionIdForGetBlock(int point) {
  return point + 26;  // 1→0, 2→1…
}

int getActionIdForPutBlock(int point) {
  return point + 35;  // 1→10, 2→11…
}

bool getBlockAt(int point) {
  int id = getActionIdForGetBlock(point);
  callActionGroup(id);
  return true;
}

bool putBlockAt(int point) {
  int id = getActionIdForPutBlock(point);
  callActionGroup(id);
  return true;
}
