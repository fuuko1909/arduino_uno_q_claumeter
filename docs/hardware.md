# Hardware wiring

Target: **Arduino UNO Q** (STM32U585 MCU side) + **WeAct Studio 2.8" TFT-LCD Module** with ILI9341 and XPT2046 touch (16-pin version).

## Arduino UNO Q MCU pinout (UNO headers)

| Arduino pin | STM32U585 pin | Function |
|-------------|---------------|----------|
| D0 / RX     | PB7           | USART1_RX |
| D1 / TX     | PB6           | USART1_TX |
| D2          | PB3           | GPIO |
| D3          | PB0           | GPIO / PWM |
| D4          | PA12          | GPIO |
| D5          | PA11          | GPIO / PWM |
| D6          | PB1           | GPIO / PWM |
| D7          | PB2           | GPIO |
| D8          | PB4           | GPIO |
| D9          | PB8           | GPIO / PWM |
| D10 / SS    | PB9           | SPI2_NSS |
| D11 / MOSI  | PB15          | SPI2_MOSI |
| D12 / MISO  | PB14          | SPI2_MISO |
| D13 / SCK   | PB13          | SPI2_SCK |
| D20 / SDA   | PB11          | I2C2_SDA |
| D21 / SCL   | PB10          | I2C2_SCL |

`SPI` on the UNO Q maps to **SPI2**.

## 16-pin WeAct ILI9341 + XPT2046 wiring

A common 16-pin module silkscreen looks like this (please verify against your board labels):

| Pin | Label  | Connect to UNO Q | Note |
|-----|--------|------------------|------|
| 1   | VCC    | 3.3 V or 5 V*    | Module power |
| 2   | GND    | GND              | |
| 3   | CS     | D10 (PB9)        | TFT chip select |
| 4   | RST    | D9 (PB8)         | TFT reset |
| 5   | DC/RS  | D8 (PB4)         | Data/Command |
| 6   | SDI/MOSI | D11 (PB15)    | SPI MOSI |
| 7   | MISO   | D12 (PB14)       | SPI MISO |
| 8   | SCK    | D13 (PB13)       | SPI clock |
| 9   | BL     | D6 (PB1, PWM)    | Backlight PWM |
| 10  | T_CS   | D7 (PB2)         | Touch chip select |
| 11  | T_DIN  | D11 (PB15)       | Touch MOSI (shared with TFT) |
| 12  | T_DO   | D12 (PB14)       | Touch MISO (shared with TFT) |
| 13  | T_IRQ  | D2 (PB3)         | Touch interrupt |
| 14  | T_CLK  | D13 (PB13)       | Touch SCK (shared with TFT) |
| 15  | GND    | GND              | (extra ground) |
| 16  | VCC    | 3.3 V or 5 V*    | (extra power) |

> ⚠️ **Verify your silkscreen labels.** 16-pin modules can vary. If your labels differ, share a photo or list and we'll adjust the pin mapping in `config.h`.

*Voltage: many ILI9341 modules accept 5 V VCC because they have an onboard 3.3 V regulator, but the logic pins expect 3.3 V levels. The UNO Q MCU headers are 3.3 V logic, so direct wiring to MOSI/MISO/SCK/CS/DC is safe. Do **not** drive 5 V into a 3.3 V-only logic pin.*

## Display orientation

The firmware uses the panel in **landscape 320×240**:
- ILI9341 native GRAM is 240×320.
- Rotation 1 or 3 gives 320×240 landscape.
- XPT2046 touch coordinates must be calibrated to match the chosen rotation.
