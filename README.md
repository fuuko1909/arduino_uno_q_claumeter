# Arduino UNO Q Claumeter

A Claude Code usage meter for the **Arduino UNO Q** + **WeAct Studio 2.8" ILI9341 TFT LCD** (320×240 landscape, optional XPT2046 touch).

This is a port of the idea behind [Clawdmeter](https://github.com/fuuko1909/Clawdmeter) but redesigned for a wired, self-contained setup: the Arduino UNO Q's Linux processor (Qualcomm QRB2210) polls the Anthropic API directly over Wi-Fi and streams usage data to the STM32U585 MCU over the internal serial bridge. No Bluetooth required.

## Features

- **Dual Claude accounts side-by-side** on one 320×240 screen.
- **Direct API polling** on the UNO Q Linux side — no host computer needed.
- **ILI9341 2.8" TFT** via SPI, 320×240 landscape.
- **XPT2046 resistive touch** for switching views / refresh.
- No BLE, no HID keyboard — pure display usage.

## Repository layout

```text
.
├── daemon/         # Python daemon that runs on the UNO Q Linux processor
├── docs/           # Wiring, build and install guides
├── firmware/       # Arduino sketch for the STM32U585 MCU
├── tools/          # Asset conversion helpers
└── .github/        # CI workflows
```

## Quick start

See:
- [`docs/hardware.md`](docs/hardware.md) for wiring the display to the UNO Q.
- [`docs/firmware.md`](docs/firmware.md) for building and flashing the MCU sketch.
- [`docs/daemon.md`](docs/daemon.md) for installing the Linux daemon.

## Hardware

- [Arduino UNO Q](https://docs.arduino.cc/hardware/uno-q/)
- [WeAct Studio 2.8" TFT-LCD Module](https://github.com/WeActStudio/WeActStudio.TFT-LCD-Module) (ILI9341, 240×320, SPI)
- Optional XPT2046 touch version.

## License

MIT — see [LICENSE](LICENSE).
