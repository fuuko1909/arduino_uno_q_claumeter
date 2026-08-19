# Firmware build and flash

The firmware is an Arduino sketch for the **STM32U585** on the Arduino UNO Q. It uses the **Arduino Zephyr core**.

## Prerequisites

- [Arduino CLI](https://arduino.github.io/arduino-cli/latest/installation/) (tested with 1.5.1)
- Arduino Zephyr board package
- Libraries: `GFX Library for Arduino`, `XPT2046_Touchscreen`, `ArduinoJson`

## Install Arduino CLI and board package

```bash
# Install arduino-cli to ~/bin (or any directory on PATH)
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=$HOME/bin sh

export PATH="$HOME/bin:$PATH"

# Add board package URL
arduino-cli config init --overwrite
arduino-cli config add board_manager.additional_urls \
  "https://downloads.arduino.cc/packages/package_zephyr_index.json"
arduino-cli core update-index

# Install Arduino UNO Q core
arduino-cli core install arduino:zephyr@0.90.0

# Install libraries
arduino-cli lib install "GFX Library for Arduino" "XPT2046_Touchscreen" "ArduinoJson"
```

## Build

```bash
cd firmware/arduino_uno_q_claumeter
arduino-cli compile --fqbn arduino:zephyr:unoq .
```

## Flash

The UNO Q typically uploads to the STM32U585 through the on-board CMSIS-DAP/debug link that is bridged by the Linux processor. Check the Arduino UNO Q documentation for the exact upload method.

Common options:

```bash
# USB CDC upload (if the MCU enumerates as a serial port)
arduino-cli upload --fqbn arduino:zephyr:unoq -p /dev/ttyACM0 .

# Or via the remote OpenOCD path used by the Arduino Zephyr core
```

If you see upload errors, verify that the UNO Q is in bootloader/upload mode and that the Linux side is running the expected bridge services.

## Bring-up test

Before loading the main firmware, flash `firmware/tft_bringup_test` to verify wiring, display colors and touch raw coordinates:

```bash
cd firmware/tft_bringup_test
arduino-cli compile --fqbn arduino:zephyr:unoq .
arduino-cli upload --fqbn arduino:zephyr:unoq -p /dev/ttyACM0 .
```

The screen should cycle red/green/blue and print raw XPT2046 values over USB serial when you touch it. Use those values to tune `TOUCH_X_MIN/MAX` and `TOUCH_Y_MIN/MAX` in `config.h` if the mapped cursor is off.

## Test the MCU firmware without Claude tokens

You can feed fake two-account payloads to the running main firmware from a PC or from the UNO Q MPU:

```bash
cd daemon
.venv/bin/python mock_sender.py /dev/ttyACM0   # or the internal /dev/ttyHS1 on the UNO Q
```

The main sketch parses the JSON and redraws the side-by-side panels each time a new line arrives.

## Serial monitor

```bash
arduino-cli monitor -p /dev/ttyACM0 -b 115200
```
