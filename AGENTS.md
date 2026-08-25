# AGENTS.md

## What this repo is

Documentation + tooling for recovering the bricked touch display of a Creality Ender-3 S1 Pro (wrong firmware flashed via the screen's SD slot). Not a software product: **no build, test, or lint commands exist**. Verified facts live in:

- `README.md` — confirmed hardware, root cause
- `docs/plano-recuperacao-completo.md` — canonical investigation log; trust this over any prose elsewhere
- `docs/backup-flash-nixos.md` — step-by-step flash dump/write procedure
- `docs/tutorial-recuperacao-sd.md` — two-phase SD recovery walkthrough (dcboot.bin + firmware.zlib + assets)

## Confirmed hardware

Verified facts (do not guess or "fix" these when editing docs):

- Printer: Creality Ender-3 S1 Pro; mainboard `CR-FDM-v2.4.S1_v301` (STM32F401).
- Display board: `4SZCX4800M043` / `V434.HYS` Rev 1.1 (silkscreen).
- Display SoC: **Allwinner F1C100s** (QFN88) — NOT a DWIN T5L ASIC, NOT DACAI silicon. FEL mode over USB appears as `1f3a:efe8`; relevant pins: 67 UVCC (3.3V), 68 USB-DM, 69 USB-DP, 70 RESET#.
- SPI flash: XMC XM25QH128CHIG — 128 Mbit / 16 MB / exactly `16777216` bytes.
- Software layer: DGUS/K600+ conventions (Lua VP calls; `13.bin`/`14.bin`/`22.bin`) running over the Allwinner SoC. Whether this unit is the DWIN or DACAI display *variant* is an open question — never state it as settled.
- No public algorithm exists to pack the stock asset folders (`DWIN_SET/`, `private/`) into the final 16 MB flash image — this remains the project's bottleneck.

## Conventions

- All docs and code comments are written in **Portuguese (pt-BR)**. Keep new content consistent.
- `.gitignore` blocks `*.bin` / `dump*.bin` / `backup*.bin`. Never commit flash dumps (16MB each, hardware-specific).
- `DWIN_SET/` is stock display UI assets copied from github.com/ThomasToka/MarlinFirmware — reference material only, don't modify.
- `private/` is the stock DACAI-variant assets from the same fork — also reference material only. It is the primary offset-mapping reference (13 MB, parseable `.zico`/`.zbmp` formats; see plano §2.5). Don't modify.
- `dcboot.bin` (eGON/Allwinner screen bootloader) + `firmware.zlib` (zlib-compressed screen OS) are the official two-phase SD recovery kit; `dcboot.bin` is also written raw at flash offset 0 in the "Frente C" hybrid approach (plano §4.3). Don't modify or re-encode them.

## Environment

- Enter with `nix-shell` (uses `nix/shell.nix`): provides `arduino-cli`, `python3` + `pyserial`, `sunxi-fel` (Allwinner FEL mode), `lsusb`.
- Host dev machine is NixOS; serial port permission requires the user in the `dialout` group (see `docs/backup-flash-nixos.md` §2).

## Tooling gotchas

- `tools/spi_tool.py` has a hardcoded `PORT = 'COM5'` near the top — change to `/dev/ttyACM0` before running on Linux. Baud is fixed at 250000; full dump takes ~15–20 min.
- Flash chip is exactly 16 MB (`16777216` bytes). `write` and `verify` refuse files of any other size; validate dumps by exact size + double-dump sha256 comparison before trusting them. Exception: the "Frente C" flow pads `dcboot.bin` with `0xFF` to 16 MB before writing (see plano §4.3).
- `arduino-cli compile` requires the `.ino` inside a subfolder of the same name (`spi_flash_programmer/spi_flash_programmer.ino`) — Arduino sketch format requirement, not an error.
- USB serial device name can change between boots (`ttyACM0` → `ttyACM1`); always run `arduino-cli board list` first.

## Safety constraints

- `erase` is irreversible. The documented workflow is always: dump donor chip → verify backup → only then erase/write the bad chip. Never reorder or skip steps when editing these tools or docs.
