#ifndef COMMAND_PARSER_H
#define COMMAND_PARSER_H

// Call once in setup()
void initParser();

// Call every loop to read Serial, dispatch, and respond
void processSerialCommands();

#endif  // COMMAND_PARSER_H
