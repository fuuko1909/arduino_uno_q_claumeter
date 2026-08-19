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

## Serial monitor

```bash
arduino-cli monitor -p /dev/ttyACM0 -b 115200
```
