#ifndef XARM_COMMANDS_H
#define XARM_COMMANDS_H

void initArm();
bool getBlockAt(int point);
bool putBlockAt(int point);
void putBlockHoldingCheck(void);
void getBlockHoldingCheck(void);

#endif
