#pragma once
#include <Arduino.h>

struct AccountData {
    char label[16];
    char account_type[8];   // "pro" / "ent"
    int session_pct;
    int session_reset_mins;
    int weekly_pct;
    int weekly_reset_mins;
    char status[16];
    char error[16];         // non-empty when ok == false
    bool valid;
};

// Copy helper for platforms without strlcpy.
size_t safe_strlcpy(char* dst, const char* src, size_t size);
