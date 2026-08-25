# AGENTS.md

## What this repo is

Documentation + tooling for recovering the bricked touch display of a Creality Ender-3 S1 Pro (wrong firmware flashed via the screen's SD slot). Not a software product: **no build, test, or lint commands exist**. Verified facts live in:

- `README.md` — confirmed hardware, root cause
- `docs/plano-recuperacao-completo.md` — canonical investigation log; trust this over any prose elsewhere
- `docs/backup-flash-nixos.md` — step-by-step flash dump/write procedure

## Conventions

- All docs and code comments are written in **Portuguese (pt-BR)**. Keep new content consistent.
- `.gitignore` blocks `*.bin` / `dump*.bin` / `backup*.bin`. Never commit flash dumps (16MB each, hardware-specific).
- `DWIN_SET/` is stock display UI assets copied from github.com/ThomasToka/MarlinFirmware — reference material only, don't modify.

## Environment

- Enter with `nix-shell` (uses `nix/shell.nix`): provides `arduino-cli`, `python3` + `pyserial`, `sunxi-fel` (Allwinner FEL mode), `lsusb`.
- Host dev machine is NixOS; serial port permission requires the user in the `dialout` group (see `docs/backup-flash-nixos.md` §2).

## Tooling gotchas

- `tools/spi_tool.py` has a hardcoded `PORT = 'COM5'` near the top — change to `/dev/ttyACM0` before running on Linux. Baud is fixed at 250000; full dump takes ~15–20 min.
- Flash chip is exactly 16 MB (`16777216` bytes). `write` and `verify` refuse files of any other size; validate dumps by exact size + double-dump sha256 comparison before trusting them.
- `arduino-cli compile` requires the `.ino` inside a subfolder of the same name (`spi_flash_programmer/spi_flash_programmer.ino`) — Arduino sketch format requirement, not an error.
- USB serial device name can change between boots (`ttyACM0` → `ttyACM1`); always run `arduino-cli board list` first.

## Safety constraints

- `erase` is irreversible. The documented workflow is always: dump donor chip → verify backup → only then erase/write the bad chip. Never reorder or skip steps when editing these tools or docs.
