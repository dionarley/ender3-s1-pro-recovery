{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "spi-flash-recovery";

  buildInputs = with pkgs; [
    arduino-cli
    python3
    python3Packages.pyserial
    sunxi-tools     # fornece sunxi-fel (modo FEL do Allwinner F1C100s)
    libusb1
    pkg-config
    usbutils        # lsusb, útil para diagnóstico
  ];

  shellHook = ''
    echo "Ambiente pronto."
    echo "arduino-cli: $(arduino-cli version 2>&1 | head -1)"
    echo "sunxi-fel:   $(sunxi-fel --version 2>&1 | head -1)"
  '';
}
