// Arduino UNO Q Claumeter
// Displays two Claude Code usage accounts side-by-side on a WeAct 2.8" ILI9341
// (320x240 landscape, XPT2046 touch). Receives JSON payloads from the Linux
// daemon over the internal serial bridge (Serial1 on the MCU side).

#include <Arduino_GFX_Library.h>
#include <XPT2046_Touchscreen.h>
#include <ArduinoJson.h>

// ---- Pinout: Arduino UNO Q (STM32U585) UNO headers ----
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
#define DATA_SERIAL   Serial1
#define DATA_BAUD     115200
#define JSON_BUF_SIZE 512

// ---- GFX bus and display ----
Arduino_DataBus* bus = new Arduino_HWSPI(PIN_TFT_DC, PIN_TFT_CS);
Arduino_GFX* gfx = new Arduino_ILI9341(bus, PIN_TFT_RST, 3 /* landscape 320x240 */);

#ifndef BLACK
#define BLACK 0x0000
#define WHITE 0xFFFF
#endif

// ---- Touch ----
XPT2046_Touchscreen ts(PIN_TCH_CS, PIN_TCH_IRQ);

// Zephyr/newlib may not provide strlcpy; supply a tiny fallback.
static inline size_t safe_strlcpy(char* dst, const char* src, size_t size) {
    if (size == 0) return 0;
    size_t i = 0;
    while (i + 1 < size && src[i] != '\0') {
        dst[i] = src[i];
        i++;
    }
    dst[i] = '\0';
    while (src[i] != '\0') i++;
    return i;
}

// ---- Usage data ----
struct AccountData {
    char label[16];
    int session_pct;
    int session_reset_mins;
    int weekly_pct;
    int weekly_reset_mins;
    char status[16];
    bool valid;
};

static AccountData accounts[2];
static bool data_fresh = false;
static uint32_t last_data_ms = 0;

static void init_display(void) {
    pinMode(PIN_TFT_BL, OUTPUT);
    analogWrite(PIN_TFT_BL, 255);

    gfx->begin(40000000); // 40 MHz SPI; adjust if unstable
    gfx->fillScreen(BLACK);
}

static void init_touch(void) {
    ts.begin();
    ts.setRotation(3); // match display landscape
}

static void draw_header(void) {
    gfx->setTextColor(WHITE, BLACK);
    gfx->setTextSize(1);
    gfx->setCursor(4, 4);
    gfx->print("Claumeter");
}

static void draw_account_panel(int idx, int x, int y, int w, int h) {
    const AccountData& a = accounts[idx];
    uint16_t border = (idx == 0) ? 0x07E0 : 0x001F; // green / blue accent

    gfx->drawRect(x, y, w, h, border);
    gfx->fillRect(x + 1, y + 1, w - 2, h - 2, 0x1082); // dark panel bg

    gfx->setTextColor(WHITE, 0x1082);
    gfx->setTextSize(1);
    gfx->setCursor(x + 6, y + 8);
    gfx->print(a.valid ? a.label : "--");

    gfx->setTextSize(2);
    gfx->setCursor(x + 6, y + 32);
    if (a.valid) {
        gfx->print("S:");
        gfx->print(a.session_pct);
        gfx->print("%");
    } else {
        gfx->print("---");
    }

    gfx->setTextSize(1);
    gfx->setCursor(x + 6, y + 64);
    if (a.valid) {
        gfx->print("W:");
        gfx->print(a.weekly_pct);
        gfx->print("%  ");
        gfx->print(a.status);
    } else {
        gfx->print("No data");
    }
}

static void draw_ui(void) {
    gfx->fillScreen(BLACK);
    draw_header();

    int panel_w = SCREEN_W - 8;
    int panel_h = (SCREEN_H - 36) / 2;

    draw_account_panel(0, 4, 28, panel_w, panel_h);
    draw_account_panel(1, 4, 32 + panel_h, panel_w, panel_h);
}

static void parse_payload(const char* json) {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, json);
    if (err) {
        Serial.print("JSON parse error: ");
        Serial.println(err.c_str());
        return;
    }

    if (!doc["ok"] | false) {
        return;
    }

    JsonArray arr = doc["accounts"].as<JsonArray>();
    int idx = 0;
    for (JsonObject acct : arr) {
        if (idx >= 2) break;
        safe_strlcpy(accounts[idx].label, acct["label"] | "Account", sizeof(accounts[idx].label));
        accounts[idx].session_pct = acct["s"] | 0;
        accounts[idx].session_reset_mins = acct["sr"] | -1;
        accounts[idx].weekly_pct = acct["w"] | 0;
        accounts[idx].weekly_reset_mins = acct["wr"] | -1;
        safe_strlcpy(accounts[idx].status, acct["st"] | "unknown", sizeof(accounts[idx].status));
        accounts[idx].valid = true;
        idx++;
    }
    data_fresh = true;
    last_data_ms = millis();
    draw_ui();
}

static void check_transport(void) {
    static char buf[JSON_BUF_SIZE];
    static int pos = 0;

    while (DATA_SERIAL.available()) {
        char c = DATA_SERIAL.read();
        if (c == '\n') {
            buf[pos] = '\0';
            if (pos > 0) {
                Serial.print("RX: ");
                Serial.println(buf);
                parse_payload(buf);
            }
            pos = 0;
        } else if (pos < JSON_BUF_SIZE - 1) {
            buf[pos++] = c;
        }
    }
}

static void check_touch(void) {
    if (ts.touched()) {
        TS_Point p = ts.getPoint();
        Serial.print("Touch: ");
        Serial.print(p.x);
        Serial.print(",");
        Serial.println(p.y);
        // TODO: navigate UI / request refresh
    }
}

void setup() {
    Serial.begin(115200);   // USB debug
    DATA_SERIAL.begin(DATA_BAUD); // Linux daemon

    while (!Serial && millis() < 2000) { }
    Serial.println("Claumeter MCU starting");

    init_display();
    init_touch();
    draw_ui();

    Serial.println("Ready for data on Serial1");
}

void loop() {
    check_transport();
    check_touch();

    // Redraw once shortly after boot even if no data, then only on new data.
    static bool boot_drawn = false;
    if (!boot_drawn && millis() > 3000) {
        draw_ui();
        boot_drawn = true;
    }

    delay(10);
}
