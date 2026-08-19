#pragma once
#include <Arduino_GFX_Library.h>

void display_init(void);
void display_set_brightness(uint8_t level);
void display_draw_ui(const struct AccountData accounts[2]);
