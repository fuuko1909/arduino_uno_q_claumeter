#pragma once

#include "data.h"

void transport_init(void);
bool transport_check(AccountData accounts[2]);
void transport_request_refresh(void);
