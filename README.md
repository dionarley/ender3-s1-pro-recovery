# Recuperação da Tela Touch — Creality Ender-3 S1 Pro

Documentação de uma tentativa de recuperar a tela touch do Ender-3 S1 Pro
depois de um brick causado por atualização com firmware do modelo errado
(Ender-3 S1 comum) aplicada via cartão SD.

**Status atual:** tela preta, apenas bipe ao toque. Recuperação via SD
card testada com o pacote correto e não funciona — a área de boot/OS da
flash está corrompida, não apenas os assets de UI. Duas frentes de
recuperação em andamento (ver `docs/plano-recuperacao-completo.md`).

Material stock da tela foi localizado (`DWIN_SET/`, do fork
ThomasToka/MarlinFirmware), mas **não resolve o brick diretamente**: são
assets de atualização via SD (não uma imagem de 16 MB) e não contêm a
área de boot/OS do F1C100s. Serve como referência para mapear offsets
contra um dump futuro. Detalhes em `docs/plano-recuperacao-completo.md`.

## Causa raiz

O slot de SD da placa-mãe original quebrou fisicamente. Na tentativa de
contornar isso, foi aplicado pelo slot de SD **da tela** um pacote de
firmware pensado para o Ender-3 S1 comum (não Pro), incompatível com o
hardware real da tela do S1 Pro.

## Hardware confirmado

| Item | Valor |
|---|---|
| Impressora | Creality Ender-3 S1 Pro |
| Placa-mãe | CR-FDM-v2.4.S1_v301 (STM32F401) |
| SoC da tela | Allwinner F1C100s (QFN88, 10×10mm) |
| Flash SPI | XMC XM25QH128CHIG, 16MB |
| Camada de software | Formato DACAI (pasta `private/`), com scripts em Lua |

Pinos relevantes do F1C100s para acesso via modo FEL (USB):

| Pino | Nome |
|---|---|
| 67 | UVCC (3,3V) |
| 68 | USB-DM |
| 69 | USB-DP |
| 70 | RESET# |

Detalhes completos, incluindo o processo de investigação e descarte de
hipóteses (DWIN T5L, TJC), estão em `docs/plano-recuperacao-completo.md`.

## Estrutura do repositório

```
.
├── README.md                          este arquivo
├── docs/
│   ├── plano-recuperacao-completo.md  plano atualizado com todos os dados confirmados
│   ├── backup-flash-nixos.md          guia de ambiente NixOS + backup via clipe SOIC-8
│   └── XM25QH128C_Ver2.1.pdf          datasheet da flash SPI
├── DWIN_SET/                          assets stock de tela (referência; não é imagem de flash)
├── images/                            fotos da placa/chip para documentação
├── tools/
│   ├── spi_flash_programmer.ino       firmware Arduino (leitura/gravação SPI via clipe)
│   ├── spi_tool.py                    script Python de controle (dump/erase/write/verify)
└── nix/
    └── shell.nix                      ambiente reprodutível (arduino-cli, sunxi-tools, python)
```

## Duas frentes de recuperação

1. **FEL via USB** — usa o modo de recuperação de fábrica do SoC Allwinner
   (não pode ser corrompido por firmware). Requer localizar/acessar os
   pinos 67–70 do F1C100s fisicamente.
2. **Backup físico via CH341A/Arduino** — útil quando houver um chip
   doador ou dump de outro usuário para comparar/gravar.

Em ambos os casos, ainda falta uma imagem de 16MB confiável para gravar
— esse é o gargalo atual do projeto.

## Como contribuir / linha do tempo

Este repositório documenta o processo em tempo real, incluindo becos sem
saída (ex.: hipótese inicial de que a tela seria DWIN T5L clássico, depois
descartada com a identificação física do Allwinner F1C100s). Issues e PRs
com dumps, informações de pinout confirmadas por continuidade, ou relatos
de recuperação bem-sucedida em hardware equivalente são bem-vindos.

## Aviso

Este é um projeto de engenharia reversa em andamento, não um guia com
solução garantida. Procedimentos aqui podem danificar permanentemente o
hardware se executados incorretamente — veja os checklists de segurança
em `docs/plano-recuperacao-completo.md` antes de reproduzir qualquer
passo.
