# Hardware wiring

Target: **Arduino UNO Q** (STM32U585 MCU side) + **WeAct Studio 2.8" TFT-LCD Module** with ILI9341 and XPT2046 touch.

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

## Proposed wiring to WeAct 2.8" module

| Module pin | Connect to UNO Q | Note |
|------------|------------------|------|
| VCC        | 3.3 V or 5 V*    | Match module regulator/jumper |
| GND        | GND              | |
| CS         | D10 (PB9)        | TFT chip select |
| RST        | D9 (PB8)         | TFT reset |
| DC / RS    | D8 (PB4)         | Data/Command |
| MOSI       | D11 (PB15)       | SPI MOSI |
| MISO       | D12 (PB14)       | SPI MISO |
| SCK        | D13 (PB13)       | SPI clock |
| BL         | D6 (PB1, PWM)    | Backlight PWM |
| T_CS       | D7 (PB2)         | XPT2046 chip select |
| T_IRQ      | D2 (PB3)         | Touch interrupt (optional) |

*Verify the module voltage: many ILI9341 modules accept 5 V VCC because they have an onboard 3.3 V regulator, but the logic pins expect 3.3 V levels. The UNO Q MCU headers are 3.3 V logic, so direct wiring is safe.

## Display orientation

The firmware uses the panel in **landscape 320×240**:
- ILI9341 native GRAM is 240×320.
- Rotation 1 or 3 gives 320×240 landscape.
- XPT2046 touch coordinates must be calibrated to match the chosen rotation.
