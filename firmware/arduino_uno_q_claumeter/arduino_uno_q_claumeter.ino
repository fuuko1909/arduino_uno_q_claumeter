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

    int tx, ty;
    if (touch_read(&tx, &ty)) {
        Serial.print("Touch: ");
        Serial.print(tx);
        Serial.print(",");
        Serial.println(ty);

        // Tap upper half = request refresh from daemon.
        if (ty < SCREEN_H / 2) {
            transport_request_refresh();
        }
        // Tap lower half could switch to a status view later.
    }

    delay(10);
}
