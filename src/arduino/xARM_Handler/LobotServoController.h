/******************************************************
* FileName:      LobotServoController.h
* Company:       Hiwonder
* Date:          2016/07/02  16:53
* Description:   Lobot servo controller secondary development library 's marco definition and class
*****************************************************/

#ifndef LOBOTSERVOCONTROLLER_H
#define LOBOTSERVOCONTROLLER_H

#include <Arduino.h>
#include <SoftwareSerial.h>

//Send part of the command
#define FRAME_HEADER            0x55   //Frame header
#define CMD_SERVO_MOVE          0x03   //Servo movement command
#define CMD_ACTION_GROUP_RUN    0x06   //Run action group command
#define CMD_ACTION_GROUP_STOP   0x07   //Stop run action group command
#define CMD_ACTION_GROUP_SPEED  0x0B   //Set action group runs speed command
#define CMD_GET_BATTERY_VOLTAGE 0x0F   //Get battery voltage command

//Receiver part of the command
#define BATTERY_VOLTAGE       0x0F  //Battery voltage
#define ACTION_GROUP_RUNNING  0x06  //Action group running
#define ACTION_GROUP_STOPPED  0x07  //Action group stopped
#define ACTION_GROUP_COMPLETE 0x08  //Action group complete

struct LobotServo {  //ServoID and position struct
  uint8_t  ID;       //ServoID
  uint16_t Position; //Servo data
};

class LobotServoController {
  public:
    LobotServoController(SoftwareSerial &A);
	  LobotServoController(HardwareSerial &A);
    void moveServo(uint8_t servoID, uint16_t Position, uint16_t Time);
    void moveServos(LobotServo servos[], uint8_t Num, uint16_t Time);
    void moveServos(uint8_t Num,uint16_t Time, ...);
    void runActionGroup(uint8_t NumOfAction, uint16_t Times);
    void stopActionGroup(void);
    void setActionGroupSpeed(uint8_t NumOfAction, uint16_t Speed);
    void setAllActionGroupSpeed(uint16_t Speed);

    uint16_t getBatteryVolt(void);
    uint16_t getBatteryVolt(uint32_t timeout);
    bool waitForStop(uint32_t timeout);
    void sendCMDGetBatteryVolt(void);
	  bool isRunning(void);
	  int actionGroupRunning(void);
    void receiveHandler(void);
	  void receiveHandle(void);
	  void setCallback(void *p);
	
  private:
    uint8_t  numOfActinGroupRunning; //The sequence number of the running action group
    uint16_t actionGroupRunTimes; //Number of running action group runs
	  bool isUseHardwareSerial;
	  bool isGetBatteryVolt;
    uint16_t batteryVoltage; //Controller battery voltage
	  bool isRunning_; //Is there an action group running?
	  bool stateChange;
	  void (*stateChangeCallback)(void);
    Stream *SerialX;
};
#endif
