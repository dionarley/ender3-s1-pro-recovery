# Recuperação da Tela Touch — Creality Ender-3 S1 Pro

Documentação de uma tentativa de recuperar a tela touch do Ender-3 S1 Pro
depois de um brick causado por atualização com firmware do modelo errado
(Ender-3 S1 comum) aplicada via cartão SD.

**Status atual:** tela preta, apenas bipe ao toque. Recuperação via SD
card testada com o pacote correto e não funciona — a área de boot/OS da
flash está corrompida, não apenas os assets de UI. **Kit de recuperação
SD em duas fases completo** (`dcboot.bin` + `firmware.zlib` + assets) —
siga o tutorial em `docs/tutorial-recuperacao-sd.md`. Detalhes técnicos
em `docs/plano-recuperacao-completo.md` (§2.6–§2.7).

Material stock da tela foi localizado no fork ThomasToka/MarlinFirmware
e está versionado aqui nas duas variantes (`DWIN_SET/` e `private/`),
mas **nenhuma resolve o brick diretamente**: são assets de atualização
via SD (não uma imagem de 16 MB) e não contêm a área de boot/OS do
F1C100s. A pasta `private/` (formato DACAI, ~13 MB) é a referência mais
promissora: cabe na flash de 16 MB e seus formatos `.zico`/`.zbmp` são
parcialmente decodificáveis — será usada como assinatura contra um dump
via FEL para identificar a variante e mapear offsets. Detalhes em
`docs/plano-recuperacao-completo.md` (§2.5).

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
| Placa da tela | `4SZCX4800M043` / `V434.HYS` Rev 1.1 (confirmado por silkscreen) |
| SoC da tela | Allwinner F1C100s (QFN88, 10×10mm; silkscreen `F1C100s ALLWINNERTECH`) |
| Flash SPI | XMC XM25QH128CHIG, 128 Mbit / 16 MB / 16.777.216 bytes, SPI simples |
| USB FEL | VID:PID `1f3a:efe8` (padrão Allwinner, modo FEL da boot ROM) |
| Camada de software | Convenções DGUS/K600+ (DWIN) sobre o SoC Allwinner — chamadas de VP em Lua, arquivos `13.bin`/`14.bin`/`22.bin`. **Variante física DWIN vs DACAI ainda não resolvida** |

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
│   ├── tutorial-recuperacao-sd.md     tutorial passo a passo da recuperação via SD (2 fases)
│   ├── backup-flash-nixos.md          guia de ambiente NixOS + backup via clipe SOIC-8
│   ├── 3D Printer User Manual Ender-3 S1 Pro.pdf  manual oficial
│   └── XM25QH128C_Ver2.1.pdf          datasheet da flash SPI
├── DWIN_SET/                          assets stock variante DWIN (referência; não é imagem de flash)
├── private/                           assets stock variante DACAI (referência; ver §2.5 do plano)
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
