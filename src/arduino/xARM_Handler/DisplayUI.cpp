#include "DisplayUI.h"
#include <U8g2lib.h>

// ONE-PAGE buffer (128×8=102 bytes)
U8G2_SSD1306_128X64_NONAME_1_HW_I2C u8g2(U8G2_R0);


// Current text to display
static String displayMsg = "";
// Flag to indicate an update is needed
static bool refreshNow = false;

void initDisplay() {
  u8g2.begin();
  u8g2.clearDisplay();
}

void setDisplayMessage(const String &msg) {
  displayMsg = msg;
  refreshNow = true;
}

void drawDisplay() {
  if (!refreshNow) return;
  refreshNow = false;

  u8g2.firstPage();
  do {
    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_fub20_tr);
    u8g2.setCursor(0, 38);
    u8g2.print(displayMsg);
  } while (u8g2.nextPage());
}
