// Arduino UNO Q Claumeter — pin and geometry configuration

#pragma once

// ---- Pinout: Arduino UNO Q (STM32U585) UNO headers ----
// Matches the 16-pin WeAct ILI9341 + XPT2046 module wiring in docs/hardware.md.
#define PIN_TFT_CS    D10
#define PIN_TFT_DC    D8
#define PIN_TFT_RST   D9
#define PIN_TFT_BL    D6
#define PIN_TCH_CS    D7
#define PIN_TCH_IRQ   D2

// ---- Display geometry ----
#define SCREEN_W      320
#define SCREEN_H      240

// ---- Transport ----
// Serial1 on the STM32U585 is connected to the Linux MPU UART.
#define DATA_SERIAL   Serial1
#define DATA_BAUD     115200
#define JSON_BUF_SIZE 512

// ---- Touch calibration ----
// XPT2046 raw ranges; tune after measuring your panel.
// Landscape 320x240, rotation 3 in XPT2046_Touchscreen.
#define TOUCH_X_MIN   300
#define TOUCH_X_MAX   3800
#define TOUCH_Y_MIN   300
#define TOUCH_Y_MAX   3800

// ---- Colors ----
#ifndef BLACK
#define BLACK 0x0000
#define WHITE 0xFFFF
#endif

#define COLOR_BG          BLACK
#define COLOR_PANEL       0x1082  // dark grey
#define COLOR_ACCENT_1    0x07E0  // green
#define COLOR_ACCENT_2    0x001F  // blue
#define COLOR_TEXT        WHITE
#define COLOR_TEXT_DIM    0x8410  // mid grey
#define COLOR_BAR_BG      0x4208  // dark bar
#define COLOR_BAR_OK      0x07E0
#define COLOR_BAR_WARN    0xFFE0
#define COLOR_BAR_FULL    0xF800
