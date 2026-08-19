// TFT + touch bring-up test for Arduino UNO Q + WeAct 2.8" ILI9341/XPT2046.
// Fills the screen with colors, prints touch coordinates, and cycles backlight.

#include <Arduino_GFX_Library.h>
#include <XPT2046_Touchscreen.h>

#define PIN_TFT_CS    D10
#define PIN_TFT_DC    D8
#define PIN_TFT_RST   D9
#define PIN_TFT_BL    D6
#define PIN_TCH_CS    D7
#define PIN_TCH_IRQ   D2

#define SCREEN_W 320
#define SCREEN_H 240

#ifndef BLACK
#define BLACK 0x0000
#define WHITE 0xFFFF
#define RED   0xF800
#define GREEN 0x07E0
#define BLUE  0x001F
#endif

Arduino_DataBus* bus = new Arduino_HWSPI(PIN_TFT_DC, PIN_TFT_CS);
Arduino_GFX* gfx = new Arduino_ILI9341(bus, PIN_TFT_RST, 3 /* landscape 320x240 */);
XPT2046_Touchscreen ts(PIN_TCH_CS, PIN_TCH_IRQ);

void setup() {
    Serial.begin(115200);
    while (!Serial && millis() < 2000) { }
    Serial.println("TFT bring-up test");

    pinMode(PIN_TFT_BL, OUTPUT);
    analogWrite(PIN_TFT_BL, 255);

    gfx->begin(40000000);
    Serial.println("Display init done");

    ts.begin();
    ts.setRotation(3);
    Serial.println("Touch init done");

    gfx->fillScreen(BLACK);
    gfx->setTextColor(WHITE, BLACK);
    gfx->setTextSize(2);
    gfx->setCursor(20, 100);
    gfx->print("Hello UNO Q!");
    delay(1000);
}

void loop() {
    gfx->fillScreen(RED);
    delay(500);
    gfx->fillScreen(GREEN);
    delay(500);
    gfx->fillScreen(BLUE);
    delay(500);
    gfx->fillScreen(BLACK);

    gfx->setTextColor(WHITE, BLACK);
    gfx->setTextSize(2);
    gfx->setCursor(10, 10);
    gfx->print("Touch test");

    for (int i = 0; i < 20; i++) {
        if (ts.touched()) {
            TS_Point p = ts.getPoint();
            Serial.print("Raw touch: ");
            Serial.print(p.x);
            Serial.print(",");
            Serial.println(p.y);

            gfx->fillRect(10, 40, 300, 40, BLACK);
            gfx->setCursor(10, 50);
            gfx->print("x=");
            gfx->print(p.x);
            gfx->print(" y=");
            gfx->print(p.y);
        }
        delay(100);
    }

    static uint8_t bl = 255;
    bl = bl ? 0 : 255;
    analogWrite(PIN_TFT_BL, bl);
}
