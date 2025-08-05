#ifndef DISPLAY_UI_H
#define DISPLAY_UI_H

#include <Arduino.h>

// Initialize the OLED display
void initDisplay();

// Queue a new status message to show on the OLED
void setDisplayMessage(const String &msg);

// Call this each loop to refresh the OLED if needed
void drawDisplay();

#endif  // DISPLAY_UI_H
