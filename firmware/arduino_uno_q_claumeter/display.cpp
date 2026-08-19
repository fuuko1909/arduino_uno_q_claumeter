#include "display.h"
#include "config.h"
#include "data.h"
#include <Arduino_GFX_Library.h>

static Arduino_DataBus* bus = nullptr;
static Arduino_GFX* gfx = nullptr;

void display_init(void) {
    pinMode(PIN_TFT_BL, OUTPUT);
    analogWrite(PIN_TFT_BL, 255);

    bus = new Arduino_HWSPI(PIN_TFT_DC, PIN_TFT_CS);
    gfx = new Arduino_ILI9341(bus, PIN_TFT_RST, 3 /* landscape 320x240 */);
    gfx->begin(40000000); // 40 MHz; lower if unstable
    gfx->fillScreen(COLOR_BG);
}

void display_set_brightness(uint8_t level) {
    analogWrite(PIN_TFT_BL, level);
}

static uint16_t bar_color(int pct) {
    if (pct >= 80) return COLOR_BAR_FULL;
    if (pct >= 50) return COLOR_BAR_WARN;
    return COLOR_BAR_OK;
}

static void draw_header(void) {
    gfx->setTextColor(COLOR_TEXT, COLOR_BG);
    gfx->setTextSize(1);
    gfx->setCursor(4, 4);
    gfx->print("Claumeter");
}

static void draw_account_panel(int idx, int x, int y, int w, int h, const AccountData accounts[2]) {
    const AccountData& a = accounts[idx];
    uint16_t border = (idx == 0) ? COLOR_ACCENT_1 : COLOR_ACCENT_2;

    gfx->drawRect(x, y, w, h, border);
    gfx->fillRect(x + 1, y + 1, w - 2, h - 2, COLOR_PANEL);

    gfx->setTextColor(COLOR_TEXT, COLOR_PANEL);
    gfx->setTextSize(1);
    gfx->setCursor(x + 6, y + 8);
    gfx->print(a.valid ? a.label : "--");

    gfx->setTextSize(2);
    gfx->setCursor(x + 6, y + 30);
    if (a.valid) {
        gfx->print("S:");
        gfx->print(a.session_pct);
        gfx->print("%");
    } else {
        gfx->print("---");
    }

    if (a.valid) {
        int bar_w = w - 12;
        int bar_h = 8;
        int bx = x + 6;
        int by = y + 56;
        gfx->fillRect(bx, by, bar_w, bar_h, COLOR_BAR_BG);
        int fill = (bar_w * a.session_pct) / 100;
        gfx->fillRect(bx, by, fill, bar_h, bar_color(a.session_pct));

        gfx->setTextSize(1);
        gfx->setTextColor(COLOR_TEXT_DIM, COLOR_PANEL);
        gfx->setCursor(x + 6, y + 74);
        gfx->print("W:");
        gfx->print(a.weekly_pct);
        gfx->print("%  ");
        gfx->print(a.status);
    } else {
        gfx->setTextSize(1);
        gfx->setTextColor(COLOR_TEXT_DIM, COLOR_PANEL);
        gfx->setCursor(x + 6, y + 74);
        gfx->print("No data");
    }
}

void display_draw_ui(const struct AccountData accounts[2]) {
    gfx->fillScreen(COLOR_BG);
    draw_header();

    int panel_w = SCREEN_W - 8;
    int panel_h = (SCREEN_H - 40) / 2;

    draw_account_panel(0, 4, 28, panel_w, panel_h, accounts);
    draw_account_panel(1, 4, 32 + panel_h, panel_w, panel_h, accounts);
}
