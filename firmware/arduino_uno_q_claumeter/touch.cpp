#include "touch.h"
#include "config.h"
#include <XPT2046_Touchscreen.h>

static XPT2046_Touchscreen ts(PIN_TCH_CS, PIN_TCH_IRQ);

void touch_init(void) {
    ts.begin();
    ts.setRotation(3); // match ILI9341 landscape 320x240
}

bool touch_read(int* x, int* y) {
    if (!ts.touched()) return false;
    TS_Point p = ts.getPoint();

    // Map raw XPT2046 coordinates to screen pixels.
    int tx = constrain(map(p.x, TOUCH_X_MIN, TOUCH_X_MAX, 0, SCREEN_W), 0, SCREEN_W);
    int ty = constrain(map(p.y, TOUCH_Y_MIN, TOUCH_Y_MAX, 0, SCREEN_H), 0, SCREEN_H);

    *x = tx;
    *y = ty;
    return true;
}
