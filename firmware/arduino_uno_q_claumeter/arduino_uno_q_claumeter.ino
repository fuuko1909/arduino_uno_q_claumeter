// Arduino UNO Q Claumeter
// Displays two Claude Code usage accounts side-by-side on a WeAct 2.8" ILI9341
// (320x240 landscape, XPT2046 touch). Receives JSON payloads from the Linux
// daemon over the internal serial bridge (Serial1 on the MCU side).

#include "config.h"
#include "data.h"
#include "display.h"
#include "touch.h"
#include "serial_transport.h"

static AccountData accounts[2];

void setup() {
    Serial.begin(115200);   // USB debug
    while (!Serial && millis() < 2000) { }
    Serial.println("Claumeter MCU starting");

    display_init();
    touch_init();
    transport_init();

    display_draw_ui(accounts);
    Serial.println("Ready for data on Serial1");
}

void loop() {
    if (transport_check(accounts)) {
        Serial.println("New data received");
        display_draw_ui(accounts);
    }

    static unsigned long last_touch_ms = 0;
    const unsigned long TOUCH_DEBOUNCE_MS = 500;

    int tx, ty;
    if (touch_read(&tx, &ty)) {
        unsigned long now = millis();
        if (now - last_touch_ms >= TOUCH_DEBOUNCE_MS) {
            last_touch_ms = now;
            Serial.print("Touch: ");
            Serial.print(tx);
            Serial.print(",");
            Serial.println(ty);

            // Any tap requests a fresh poll from the Linux daemon.
            // The daemon always polls every configured account.
            transport_request_refresh();
        }
    }

    delay(10);
}
