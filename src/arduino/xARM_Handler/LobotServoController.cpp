/******************************************************
 * FileName:      LobotServoController.cpp
 ** Company:       Hiwonder
 * Date:           2016/07/02  16:53
 * Description:    Lobot servo controller second development library, this document contains the concrete realization of this library
 *****************************************************/

#include "LobotServoController.h"
#include <Stream.h>

#define GET_LOW_BYTE(A) (uint8_t)((A))
//Marco function, get lower eight bits of A
#define GET_HIGH_BYTE(A) (uint8_t)((A) >> 8)
//Marco function,get high 8 bits of A
#define BYTE_TO_HW(A, B) ((((uint16_t)(A)) << 8) | (uint8_t)(B))
//Marco function,A is the high 8bits and B is the low 8bits,which is combined into 16 bits

LobotServoController::LobotServoController(SoftwareSerial &A)
{
	//Set the running action group number is 0xFF, the number of runs to be 0, the mark to be false in running, and the battery voltage to be 0
	numOfActinGroupRunning = 0xFF;
	actionGroupRunTimes = 0;
	isGetBatteryVolt = false;
	isRunning_ = false;
	batteryVoltage = 0;
	stateChange = false;
	isUseHardwareSerial = false;
	stateChangeCallback = NULL;
	A.listen();
	SerialX = (Stream*)(&A);
}

LobotServoController::LobotServoController(HardwareSerial &A)
{
	//Set the running action group number is 0xFF, the number of runs to be 0, the mark to be false is running, and the battery voltage to be 0
	numOfActinGroupRunning = 0xFF;
	actionGroupRunTimes = 0;
	isGetBatteryVolt = false;
	isRunning_ = false;
	batteryVoltage = 0;
	stateChange = false;
	isUseHardwareSerial = true;
	stateChangeCallback = NULL;
	SerialX = (Stream*)(&A);
}

/*********************************************************************************
 * Function:  moveServo
 * Description Control the single servo rotation
 * Parameters:   sevoID:servoIDPosition:target position ,Time: rotation time
 Servo ID value:0<= servo ID<=31,Time value: Time > 0
 * Return:      no return 
 * Others:
 **********************************************************************************/
void LobotServoController::moveServo(uint8_t servoID, uint16_t Position, uint16_t Time)
{
	uint8_t buf[11];
	if (servoID > 31 || !(Time > 0)) { //The servo ID should not be greater than 31,which can be modified according to corresponding controller
		return;
	}
	buf[0] = FRAME_HEADER;                   //Fill frame header
	buf[1] = FRAME_HEADER;
	buf[2] = 8;                              //Date length=number of control servos*3+5,here=1*3+5
	buf[3] = CMD_SERVO_MOVE;                 //Fill servo movement command
	buf[4] = 1;                              //Number of servo to be controlled
	buf[5] = GET_LOW_BYTE(Time);             //Fill time of low 8 bits
	buf[6] = GET_HIGH_BYTE(Time);            //Fill time of high 8 bits
	buf[7] = servoID;                        //Servo ID
	buf[8] = GET_LOW_BYTE(Position);         //Fill target position of low 8 bits
	buf[9] = GET_HIGH_BYTE(Position);        //Fill target position of high 8 bits

	SerialX->write(buf, 10);
}

/*********************************************************************************
 * Function:  moveServos
 * Description Control multiple servos rotation
 * Parameters:   servos[]:Servo struct arrayNum:the munber of servos,Time:rotation time
 0 < Num <= 32,Time > 0
 * Return:       no return
 * Others:
 **********************************************************************************/
void LobotServoController::moveServos(LobotServo servos[], uint8_t Num, uint16_t Time)
{
	uint8_t buf[103];    //Set the cache
	if (Num < 1 || Num > 32 || !(Time > 0)) {
		return; //The number of the servos can not be 0 and the maximum is 32, the time can not be 0
	}
	buf[0] = FRAME_HEADER;    //Fill frame header
	buf[1] = FRAME_HEADER;
	buf[2] = Num * 3 + 5;     //Date length=number of control servo*3+5
	buf[3] = CMD_SERVO_MOVE;  //Fill servo movement command
	buf[4] = Num;             //Number of servo to be controlled
	buf[5] = GET_LOW_BYTE(Time); //Get time of low 8 bits
	buf[6] = GET_HIGH_BYTE(Time); //Get time of high 8 bits
	uint8_t index = 7;
	for (uint8_t i = 0; i < Num; i++) { //Circularly fill the servo ID and the corresponding target position
		buf[index++] = servos[i].ID; //Fill servo ID
		buf[index++] = GET_LOW_BYTE(servos[i].Position); //Fill target position of low 8 bits
		buf[index++] = GET_HIGH_BYTE(servos[i].Position);//Fill target position of high 8 bits
	}
	SerialX->write(buf, buf[2] + 2); //Send the frame,the length of which is the data length + two bytes of the frame header
}

/*********************************************************************************
 * Function:  moveServos
 * Description Control multiple servos rotation
 * Parameters:   Num:the number of servo,Time:rotation time,...:servoID,rotation angleservoID,rotation angle....
 * Return:       no return
 * Others:
 **********************************************************************************/
void LobotServoController::moveServos(uint8_t Num, uint16_t Time, ...)
{
	uint8_t buf[128];
	va_list arg_ptr = NULL;
	va_start(arg_ptr, Time); //Gets the variable parameter address
	if (Num < 1 || Num > 32 || (!(Time > 0)) || arg_ptr == NULL) {
		return; //The number of the servos can not be 0 and the maximum is 32, the time can not be 0,variable arguments cannot be empty
	}
	buf[0] = FRAME_HEADER;     //Fill frame header
	buf[1] = FRAME_HEADER;
	buf[2] = Num * 3 + 5;      //Date length=number of control servo * 3 + 5
	buf[3] = CMD_SERVO_MOVE;   //Servo movement command
	buf[4] = Num;              //Number of servo to be controlled
	buf[5] = GET_LOW_BYTE(Time); //Get time of low 8 bits
	buf[6] = GET_HIGH_BYTE(Time); //Get time of high 8 bits
	uint8_t index = 7;
	for (uint8_t i = 0; i < Num; i++) { //Circularly fill the servo ID and the corresponding target position from variable parameter
		uint16_t tmp = va_arg(arg_ptr, uint16_t); //Get the servo ID from variable parameter
		buf[index++] = GET_LOW_BYTE(tmp); //avrgcc's variable-parameterare all 16 bits
		//Get it's low 8 bits
		uint16_t pos = va_arg(arg_ptr, uint16_t); //Getcorresponding target position from variable parameter
		buf[index++] = GET_LOW_BYTE(pos); //Fill target position of low 8 bits
		buf[index++] = GET_HIGH_BYTE(pos); //Fill target position of high 8 bits
	}
	va_end(arg_ptr);     //Empty arg_ptr
	SerialX->write(buf, buf[2] + 2); //Send frame
}


/*********************************************************************************
 * Function:  runActionGroup
 * Description Runs the specified action group
 * Parameters:   NumOfAction:action group number, Times:perform Times
 * Return:       No return
 * Others:       Times = 0 is infinited loop
 **********************************************************************************/
void LobotServoController::runActionGroup(uint8_t numOfAction, uint16_t Times)
{
	uint8_t buf[7];
	buf[0] = FRAME_HEADER;   //Fill frame header
	buf[1] = FRAME_HEADER;
	buf[2] = 5;      //Data length, the number of bytes of data frame except the head part of the data frame, this command is fixed to 5
	buf[3] = CMD_ACTION_GROUP_RUN; //Fill runs action group command
	buf[4] = numOfAction;      //Fill runs action group number
	buf[5] = GET_LOW_BYTE(Times); //Gets the low 8 bits to run the number of times
	buf[6] = GET_HIGH_BYTE(Times); //Gets the high 8 bits to run the number of times
	//isRunning_ = true;
	SerialX->write(buf, 7);      //Send digital frame
}

/*********************************************************************************
 * Function:  stopActiongGroup
 * Description Stop action group running
 * Parameters:   Speed: target speed
 * Return:       No return
 * Others:
 **********************************************************************************/
void LobotServoController::stopActionGroup(void)
{
	uint8_t buf[4];
	buf[0] = FRAME_HEADER;     //Fill frame header
	buf[1] = FRAME_HEADER;
	buf[2] = 2;                //Data length, the number of bytes of data frame except the head part of the data frame, this command is fixed to 2
	buf[3] = CMD_ACTION_GROUP_STOP; //Fill stop running action group command

	SerialX->write(buf, 4);      //Send digital frame
}

/*********************************************************************************
 * Function:  setActionGroupSpeed
 * Description Sets the speed of the specified action group
 * Parameters:   NumOfAction: action group number, Speed:target speed
 * Return:       no Return
 * Others:
 **********************************************************************************/
void LobotServoController::setActionGroupSpeed(uint8_t numOfAction, uint16_t Speed)
{
	uint8_t buf[7];
	buf[0] = FRAME_HEADER;     //Fill frame header
	buf[1] = FRAME_HEADER;
	buf[2] = 5;                //Data length, the number of bytes of data frame except the head part of the data frame, this command is fixed to 5
	buf[3] = CMD_ACTION_GROUP_SPEED; //Fill the set action group speed command
	buf[4] = numOfAction;      //Fill the action group number to set
	buf[5] = GET_LOW_BYTE(Speed); //Get the lower eight of the target speed
	buf[6] = GET_HIGH_BYTE(Speed); //Get the high eight of the target speed

	SerialX->write(buf, 7);      //Send digital frame
}


/*********************************************************************************
 * Function:  setAllActionGroupSpeed
 * Description Sets the running speed of all action groups
 * Parameters:   Speed: target speed
 * Return:        no Return
 * Others:
 **********************************************************************************/
void LobotServoController::setAllActionGroupSpeed(uint16_t Speed)
{
	setActionGroupSpeed(0xFF, Speed); //Call the action group speed set, and set the speed of all groups when the group number is 0xFF
}

/*********************************************************************************
 * Function:  sendCMDGetBatteryVolt
 * Description Send get battery voltage command
 * Parameters:   no input parameter
 * Return:        no Return
 * Others:
 **********************************************************************************/
void LobotServoController::sendCMDGetBatteryVolt()
{
	uint8_t buf[4];
	buf[0] = FRAME_HEADER;         //Fill frame header
	buf[1] = FRAME_HEADER;
	buf[2] = 2;                   //Data length, the number of bytes of data frame except the head part of the data frame, this command is fixed to 2
	buf[3] = CMD_GET_BATTERY_VOLTAGE; //Battery voltage command after filling
	if(!isUseHardwareSerial)
		((SoftwareSerial*)(SerialX))->listen();
	isGetBatteryVolt = false;
	SerialX->write(buf, 4);        //Send digital frame
}

uint16_t LobotServoController::getBatteryVolt(void)
{
	if(isGetBatteryVolt)
	{
		isGetBatteryVolt = false;
		return batteryVoltage;
	}else{
		return -1;
	}
}

uint16_t LobotServoController::getBatteryVolt(uint32_t timeout)
{
	isGetBatteryVolt = false;
	sendCMDGetBatteryVolt();
	timeout += millis();
	while(!isGetBatteryVolt)
	{
		if(timeout < millis())
		{
			return -1;
		}
		receiveHandle();
	}
	return batteryVoltage;
}
bool LobotServoController::isRunning()
{
	return isRunning_;
}

int LobotServoController::actionGroupRunning()
{
	int ret;
	ret = isRunning_ ? numOfActinGroupRunning : (-1);
	return ret;
}

bool LobotServoController::waitForStop(uint32_t timeout)
{
	while(SerialX->available())
		SerialX->read();
	timeout += millis();
	while(isRunning_)
	{
		if(timeout < millis())
		{
			return false;
		}
		receiveHandle();
	}
	return true;
}

void LobotServoController::setCallback(void *p)
{
	if(p != NULL)
	{
		stateChangeCallback = (void(*)())p;
	}
}
void LobotServoController::receiveHandler()
{
	uint8_t rx;
	static uint8_t buf[16];
	static bool isGetFrameHeader = false;
	static uint8_t frameHeaderCount = 0;
	static uint8_t dataLength = 2;
	static uint8_t dataCount = 0;

	while(SerialX->available() > 0)
	{
		rx = SerialX->read();
		if(!isGetFrameHeader)
		{
			if(rx == 0x55)
			{
				frameHeaderCount++;
				if(frameHeaderCount == 2)
				{
					frameHeaderCount = 0;
					isGetFrameHeader = true;
					dataCount = 1;
				}
			} else {
				isGetFrameHeader = false;
				dataCount = 0;
				frameHeaderCount = 0;
			}
		}
		if(isGetFrameHeader)
		{
			buf[dataCount] = rx;
			if(dataCount == 2)
			{
				dataLength = buf[dataCount];
				if(dataLength < 2 || dataLength > 8)
				{
					dataLength = 2;
					isGetFrameHeader = false;
				}
			}
			dataCount++;
			if(dataCount == dataLength + 2)
			{
				isGetFrameHeader = false;
				switch(buf[3])
				{
					case BATTERY_VOLTAGE:
						batteryVoltage = BYTE_TO_HW(buf[5], buf[4]);
						isGetBatteryVolt = true;
						break;
					case ACTION_GROUP_RUNNING:
						isRunning_ = true;
						stateChange = true;
						numOfActinGroupRunning = buf[4];
						actionGroupRunTimes = BYTE_TO_HW(buf[6],buf[5]);
						break;
					case ACTION_GROUP_COMPLETE:
					case ACTION_GROUP_STOPPED:
						stateChange = true;
						numOfActinGroupRunning = 0xFF;
						actionGroupRunTimes = 0;
						isRunning_ = false;
						break;
					default:
						break;
				}
			}
		}
	}
	if(stateChange)
	{
		stateChange = false;
		if(stateChangeCallback != NULL)
			(*stateChangeCallback)();
	}
}

void LobotServoController::receiveHandle()
{
  receiveHandler();
}

