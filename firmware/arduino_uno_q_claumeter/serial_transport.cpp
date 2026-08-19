#include "serial_transport.h"
#include "config.h"
#include "data.h"
#include <ArduinoJson.h>

static char rx_buf[JSON_BUF_SIZE];
static int rx_pos = 0;

void transport_init(void) {
    DATA_SERIAL.begin(DATA_BAUD);
}

// Parse a single JSON line into the two account slots.
// Returns true if new valid data arrived.
bool transport_check(AccountData accounts[2]) {
    bool got_new = false;
    while (DATA_SERIAL.available()) {
        char c = DATA_SERIAL.read();
        if (c == '\n') {
            rx_buf[rx_pos] = '\0';
            if (rx_pos > 0) {
                JsonDocument doc;
                DeserializationError err = deserializeJson(doc, rx_buf);
                if (!err && doc["ok"] | false) {
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
                    // Mark any remaining slot invalid if not present.
                    for (; idx < 2; idx++) {
                        accounts[idx].valid = false;
                    }
                    got_new = true;
                }
            }
            rx_pos = 0;
        } else if (rx_pos < JSON_BUF_SIZE - 1) {
            rx_buf[rx_pos++] = c;
        }
    }
    return got_new;
}

void transport_request_refresh(void) {
    DATA_SERIAL.println("{\"cmd\":\"refresh\"}");
}
