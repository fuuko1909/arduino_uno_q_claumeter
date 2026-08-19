#pragma once
#include <Arduino.h>

struct AccountData {
    char label[16];
    int session_pct;
    int session_reset_mins;
    int weekly_pct;
    int weekly_reset_mins;
    char status[16];
    bool valid;
};

// Copy helper for platforms without strlcpy.
size_t safe_strlcpy(char* dst, const char* src, size_t size);
