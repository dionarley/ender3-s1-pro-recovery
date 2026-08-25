# Plano de Recuperação Completo — Tela Touch Ender-3 S1 Pro
### (Versão atualizada com todos os dados confirmados)

---

## 0. Resumo executivo

A tela touch do Ender-3 S1 Pro está com a área de boot/OS da flash corrompida.
A recuperação padrão via cartão SD **não funciona** (testado e confirmado).
Existem duas frentes viáveis de recuperação, que podem ser tocadas em
paralelo:

- **Frente A — Modo FEL via USB**: usa um recurso de fábrica do chip
  Allwinner que roda direto da ROM interna (não pode ser corrompido por
  firmware). Tecnicamente mais elegante, mas exige solda fina em
  encapsulamento QFN88.
- **Frente B — Backup físico via CH341A/Arduino**: só é útil quando
  houver uma imagem de referência real (chip doador ou dump de outro
  usuário) para copiar. Sem isso, serve apenas para diagnóstico.

Em ambos os casos, **ainda falta uma imagem de 16MB confiável para gravar**
— isso não foi resolvido, apenas o caminho técnico para usá-la ficou mais
claro.

---

## 1. Causa raiz confirmada

O slot de cartão SD da placa-mãe original (Ender-3 S1 Pro, `CR-FDM-v2.4.S1_v301`,
STM32F401) se desprendeu fisicamente da placa. O dono anterior, tentando
contornar isso, comprou por engano uma placa-mãe do **Ender-3 S1 comum**
(não Pro) e, na tentativa de fazer as coisas funcionarem, usou o slot de SD
**da própria tela touch** para aplicar um pacote de firmware/recursos
pensado para o **Ender-3 S1 comum** — que não é compatível com o hardware
real da tela do S1 Pro.

Isso sobrescreveu a área de boot/OS da flash da tela (não apenas os assets
de interface), resultando no estado atual: tela preta, apenas bipe ao
toque, sem resposta ao processo normal de atualização via SD.

---

## 2. Hardware confirmado

### 2.1 Placa da tela
- Silkscreen: `4SZCX4800M043`, `V434.HYS`, Rev 1.1
- Conectores: `SD_CARD` (slot microSD), `J1` (FPC para o painel LCD), `J4`/`J5`
  (alimentação/comunicação com a placa-mãe, rotulado `VCC=5V`), `RP` (FPC do
  touch)

### 2.2 Chip principal: Allwinner F1C100s
- **Não é DWIN T5L nem DACAI** — é um SoC ARM926EJ-S da Allwinner
- Encapsulamento: **QFN88, 10×10mm**
- Confirmado visualmente pelo silkscreen `F1C100s ALLWINNERTECH MB160BA`
- Confirmado por relato independente de terceiro (fórum elektroda.com)
  descrevendo exatamente esse chip na tela do Ender-3 S1 Pro
- Pinos relevantes para recuperação (Datasheet oficial Allwinner
  F1C100s Rev 1.0):

| Pino | Nome | Função |
|---|---|---|
| 67 | UVCC | Alimentação 3,3V do USB |
| 68 | USB-DM | Dado USB D− |
| 69 | USB-DP | Dado USB D+ |
| 70 | RESET# | Reset do chip |

- O boot ROM interno do F1C100s suporta boot via SPI NOR **e** carregamento
  de código via USB OTG nativamente — recurso de fábrica, gravado em ROM,
  não pode ser apagado por um firmware incorreto.

### 2.3 Flash SPI: XM25QH128CHIG
- 128Mbit / 16MB / 16.777.216 bytes, SPI simples, 1–3MHz
- Serve como memória de boot + armazenamento de sistema para o F1C100s
- Confirmado fisicamente (fotos de perto do chip `XMC 25QH128CHIG`)

### 2.4 Camada de software: DGUS / K600+ (DWIN)
- O `main.lua` extraído do pacote oficial usa chamadas como
  `set_uint16(0x110e, ...)` e `set_auto_notify(...)` — convenções de
  endereço de VP (Variable Pointer) do DGUS da DWIN
- Isso indica que a Creality/DWIN roda o kernel DGUS (plataforma "K600+")
  sobre o SoC Allwinner, em vez do ASIC próprio da DWIN (T5L)
- Arquivos `13.bin`, `14.bin`, `22.bin` em `private/bin/` batem exatamente
  com a convenção documentada da DWIN (touch config / show config / config
  geral)
- **Não existe tabela de offsets pública** para como esses arquivos viram
  a imagem final de 16MB — os tamanhos variam (alguns acima de 2MB),
  descartando a hipótese de slots fixos de 256KB por ID

### 2.5 Análise do material stock local — pasta `private/` (formato DACAI)

Inventário completo (101 arquivos, **13.700.189 bytes ≈ 13 MB** — cabe
na flash de 16 MB, ao contrário do DWIN_SET com seus 28,8 MB):

| Conteúdo | Detalhes |
|---|---|
| `icon/*.zico` | 16 contêineres de ícones; maior: `25.zico` (4 MB) |
| `image/*.zbmp` | 77 bitmaps comprimidos |
| `bin/22.bin` | Config geral, exatamente 131.076 bytes |
| `bin/13.bin`, `14.bin`, `pinyin.bin` | Touch config / show config / método de entrada |
| `truefont/font.ttf` + `truefont.ini` | Fonte TTF (190 KB) |
| `main.lua`, `config.txt` | `set_uint16(0x110e, ...)` / `set_auto_notify(1)`; UART 115200 |

Achados técnicos:

- **`.zico` é um contêiner parseável**: magic ASCII `ZICO` seguido de
  tabela de entradas com offsets/tamanhos em texto claro.
- **`.zbmp` é cabeçalho pequeno + stream zlib padrão** (`789c`) —
  descomprimível direto.
- O `main.lua` usa as mesmas chamadas DGUS-style da §2.4, confirmando a
  camada K600+ também na pilha DACAI.
- Os `22.bin` das duas pilhas têm o mesmo tamanho (131.076) mas hashes
  SHA-256 diferentes — são stacks genuinamente distintas.
- Nenhum binário de boot/OS aqui também — só assets.

**Implicação estratégica:** se a unidade for da variante DACAI/F1C100s,
este é o material de referência correto (13 MB compatíveis com flash de
16 MB com espaço para OS+boot). No dump diagnóstico via FEL (§4.1.4),
procurar os bytes de `truefont/font.ttf` ou de uma entrada do
`25.zico` no dump: match exato confirma a variante **e** revela os
offsets do empacotamento.

### 2.6 Análise do `firmware.zlib` — procedimento oficial em duas fases

O arquivo `firmware.zlib` (394.835 bytes) e o Readme oficial de
atualização (`docs/Readme_firmware_update_CN_EN.txt`, originalmente em
GBK) foram adicionados ao repositório. Análise:

- Formato: magic ASCII `ZLIB` + cabeçalho little-endian com tamanho
  descomprimido (758.252) e comprimido (394.819); stream zlib padrão a
  partir do offset 16.
- Descomprimido, contém **758 KB de código ARM**: o sistema operacional
  da tela. Strings confirmam drivers diretos da flash SPI
  (`read_flash`, `write_flash`, `flash_init`, `spinor_wrsr`), máquina
  de estados `UPDATE_BOOT!` / `UPDATE_FIRMWARE!`, carregamento dos
  formatos da pilha DACAI (`3:/icon/%d.zico`, `3:/image/%d.zbmp`) e
  interpretador Lua 5.3.4 embutido (bate com o `main.lua`).

O Readme documenta o **procedimento oficial de atualização da tela em
duas fases via SD**:

1. **Fase 1:** apenas `dcboot.bin` no cartão → reiniciar → regrava a
   **área de boot**
2. **Fase 2:** remover `dcboot.bin`; colocar `private/`, `TJC_SET`,
   `DWIN_SET` e `firmware.zlib` → reiniciar → regrava OS + assets

Implicações críticas:

- O teste SD anterior (§3) usou o pacote V2.0.8.26F4 **sem
  `dcboot.bin`**. Para área de boot corrompida, o procedimento oficial
  começa justamente pelo `dcboot.bin` — o único arquivo que regrava o
  setor de boot pela via SD, sem solda nem FEL.
- **`dcboot.bin` não está no repositório** — precisa ser obtido do
  pacote oficial completo. É a peça faltante mais importante agora.
- **Ressalva de compatibilidade:** o Readme diz "Ender-3 S1 升级版"
  (versão atualizada do S1) e lista as três pastas de tela
  (TJC_SET/DWIN_SET/private). Antes de qualquer uso, confirmar que este
  pacote é mesmo do S1 **Pro** — aplicar pacote do modelo errado foi a
  causa raiz do brick (§1).

### 2.7 Análise do `dcboot.bin` — kit de recuperação SD completo

O `dcboot.bin` (101.888 bytes) foi obtido e adicionado ao repositório.
Análise confirma que é a peça da fase 1:

- **Cabeçalho `eGON.EXE`** — formato oficial de imagem de boot da
  Allwinner (mesmo formato do boot0 do F1C100s); primeira instrução é
  um branch ARM pulando o cabeçalho. É código de boot para o SoC da
  tela, sem ambiguidade.
- Strings internas: `BOOT_DC48270M043.bin` / `DC48270M043.zlib`
  (compatíveis com o silkscreen da tela `...M043`), `flash_erase_sector`,
  `spinor_wrsr`, `'3:/firmware.zlib'`, `zlib_size=%d`,
  `update finished!` — é o bootloader que lê o `firmware.zlib` do SD e
  grava na flash SPI.
- Os drivers de flash são os mesmos do OS descomprimido em §2.6 —
  mesma pilha, peças coerentes entre si.

**Status: kit completo da via SD**, agora todo versionado no repo:

| Fase | Arquivo | Função |
|---|---|---|
| 1 | `dcboot.bin` | regrava a área de boot |
| 2 | `firmware.zlib` | regrava o OS |
| 2 | `private/` (+ `DWIN_SET/`) | assets (a tela escolhe a pasta da sua variante) |

Procedimento do Readme oficial (§2.6): formatar cartão FAT32 com
unidade de alocação **4096 bytes**; fase 1 = apenas `dcboot.bin`;
fase 2 = remover `dcboot.bin` e colocar os demais.

Descartado no processo: um `Ender-3S1_Pro_..._F103_FDM_LASER.bin` que
chegou a ser baixado junto — é firmware de **placa-mãe STM32F103**
(vetores em `0x08000000`), não da tela; a placa local é F401. Não usar,
não versionado.

---

## 3. O que já foi tentado e descartado

| Tentativa | Resultado |
|---|---|
| Recuperação via SD card com pacote errado (S1 comum) | Causou o brick |
| Recuperação via SD card com pacote correto (S1 Pro, V2.0.8.26F4) | Tela continua preta, só bipe — **confirma que a área de boot/OS está corrompida**, não só os assets |
| Busca por dump de 16MB público (GitHub, Reddit, fóruns DWIN, Creality) | Nenhum encontrado |
| Inspeção do branch `Firmware-Binaries` de ThomasToka/MarlinFirmware (2026-08) | Sem imagem de 16MB. `Stock_Creality_F28_105_...DWIN_SET.zip` contém exatamente o mesmo DWIN_SET já no repo (2.241 arquivos, 28.832.565 bytes). `T5L_OS_DGUS2_V10.BIN` tem só 11 KB — patch de kernel para T5L real via SD, não aplicável ao F1C100s confirmado fisicamente |
| Assets stock do fork ThomasToka (`DWIN_SET/`) como solução direta | Descartado: são assets de SD (~28,8 MB em 2.219 arquivos soltos), não imagem de flash; não contêm boot/OS do F1C100s; e o caminho SD já está confirmado morto (§3, linha acima). Servem como referência para mapear offsets contra um dump futuro |
| Análise da pasta `private/` (formato DACAI) como solução direta | Sem binário de boot/OS também — não resolve sozinha. Mas é a referência mais promissora: 13 MB compatíveis com a flash, `.zico` parseável e `.zbmp` em zlib (ver §2.5). Usar no dump FEL para identificar variante + offsets |
| Reconstrução manual da imagem a partir dos arquivos oficiais | Inviável sem o algoritmo de empacotamento proprietário da DWIN/Creality |

---

## 4. Duas frentes de recuperação (podem rodar em paralelo)

### 4.1 Frente A — Modo FEL via USB (recomendada tentar primeiro)

#### 4.1.1 Preparar ambiente no NixOS

Atualize o `shell.nix` do projeto (o mesmo criado antes, com adição do
`sunxi-tools`):

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "spi-flash-recovery";

  buildInputs = with pkgs; [
    arduino-cli
    python3
    python3Packages.pyserial
    sunxi-tools     # fornece o comando sunxi-fel
    libusb1
    pkg-config
    usbutils        # fornece lsusb, útil para diagnosticar
  ];

  shellHook = ''
    echo "Ambiente pronto: sunxi-fel $(sunxi-fel --version 2>&1 | head -1)"
  '';
}
```

Permissão de USB para o modo FEL (dispositivo aparece como
`1f3a:efe8`). Adicione ao `configuration.nix`:

```nix
services.udev.extraRules = ''
  SUBSYSTEM=="usb", ATTR{idVendor}=="1f3a", ATTR{idProduct}=="efe8", MODE="0666", GROUP="dialout"
'';
```

```bash
sudo nixos-rebuild switch
nix-shell
```

#### 4.1.2 Teste de continuidade — ANTES de qualquer solda

Com a placa **desenergizada**, use um multímetro em modo de continuidade/
diodo:

1. Localize o pino 1 do chip F1C100s (ponto/marca no canto do
   encapsulamento QFN88).
2. Conte os pinos até 67, 68, 69, 70 (UVCC, USB-DM, USB-DP, RESET#).
3. Teste continuidade desses pinos até qualquer via, pad de teste, ou
   componente próximo (resistor pull-up, diodo ESD) que pareça ser rota
   de USB.
4. **Se não houver continuidade para nenhum ponto acessível**, essas
   trilhas provavelmente não foram roteadas para lugar nenhum na placa —
   nesse caso, a única opção seria soldar diretamente no pino do chip
   ("dead bug"), o que é significativamente mais arriscado.

Documente o que encontrar (foto com anotações) antes de decidir se
solda.

#### 4.1.3 Conexão USB e primeiro teste com sunxi-fel

Depois de identificar/soldar os pontos de acesso:

```bash
# Com o cabo USB conectado e a tela energizada
lsusb | grep -i 1f3a
```

Se aparecer algo como `1f3a:efe8 Allwinner Technology`, o chip está em
modo FEL e visível. Teste básico:

```bash
sunxi-fel version
```

Isso deve retornar informações do chip (SID, versão de boot ROM) sem
precisar de nenhuma imagem ainda — é um teste de comunicação puro.

#### 4.1.4 Dump de diagnóstico da flash atual

Antes de gravar qualquer coisa, leia o que já está lá (mesmo corrompido)
— isso ajuda a entender a estrutura real da flash e serve de "estado
antes" para comparação:

```bash
sunxi-fel spiflash-read 0 16777216 dump_atual_corrompido.bin
```

#### 4.1.5 Gravação (somente quando houver uma imagem confiável)

```bash
sunxi-fel spiflash-write 0 imagem_confiavel_16mb.bin
```

**Esse passo só deve ser executado quando a Frente B (abaixo) tiver
produzido uma imagem em que se possa confiar.** Gravar uma imagem errada
por essa via tem o mesmo risco de piorar as coisas — a vantagem do FEL é
a segurança do transporte (USB, sem risco de desalinhamento físico de
garra), não uma garantia sobre o conteúdo gravado.

---

### 4.2 Frente B — Backup físico via CH341A/Arduino (se/quando houver doador)

Mantém-se o que já foi preparado nas etapas anteriores desta conversa:

- Firmware Arduino (`spi_flash_programmer.ino`) e script Python
  (`spi_tool.py`) já prontos e testados na estrutura
- Útil em dois cenários:
  1. Você encontra um doador físico (outra tela do mesmo modelo/revisão)
     e quer extrair o dump dela
  2. Você quer ler a flash da tela com defeito via clipe (sem precisar do
     FEL), como alternativa/comparação

O procedimento completo (ambiente, permissões, uso) está no documento
anterior desta conversa (`backup-flash-nixos.md`) e continua válido sem
alterações — a única mudança é que agora sabemos que a arquitetura por
trás dos bytes é F1C100s + DGUS, o que ajuda a interpretar o que for lido.

### 4.3 Frente C — Híbrida: gravar o `dcboot.bin` direto na flash

Combina o transporte da Frente A ou B com o conteúdo oficial do
procedimento de duas fases (§2.6–§2.7). Em vez de depender do SD —
que exige algum código vivo na tela para ler o cartão e aplicar a
fase 1 — grava-se o `dcboot.bin` diretamente na flash, restaurando o
bootloader sem depender de nada sobrevivente no chip.

Viabilidade confirmada pela análise do cabeçalho:

- Instrução inicial `ea000006` (branch ARM pulando o cabeçalho) +
  magic `eGON.EXE` + tamanho declarado = tamanho real (101.888 bytes).
- É uma imagem de boot autocontida, pronta para execução direta pelo
  F1C100s a partir da flash.

Duas formas de transporte:

**Via FEL (preferível):**

```bash
sunxi-fel spiflash-write 0 dcboot.bin
```

Escreve no offset 0 (posição padrão de boot em SPI NOR para sunxi),
sem exigir arquivo de 16 MB. Depois conferir lendo de volta:

```bash
sunxi-fel spiflash-read 0 101888 dcboot_verificado.bin
sha256sum dcboot.bin dcboot_verificado.bin   # devem bater
```

**Via clipe SOIC-8:** o `spi_tool.py` exige arquivos de exatamente
16 MB — padar o `dcboot.bin` com `0xFF` antes:

```bash
python3 - <<'EOF'
data = open('dcboot.bin','rb').read()
assert len(data) <= 16777216 - 0x1000
open('dcboot_padded_16mb.bin','wb').write(data + b'\xff' * (16777216 - len(data)))
EOF
# então: python3 tools/spi_tool.py write dcboot_padded_16mb.bin
```

Ressalvas e segurança:

- **Offset 0 é hipótese padrão sunxi**; um dump diagnóstico prévio
  (§4.1.4 / §4.2) confirma, comparando os primeiros 32 bytes do dump
  atual com o formato eGON.
- Workflow obrigatório se mantém: **dump → backup verificado → só
  então escrever → ler de volta e comparar sha256 dos primeiros
  101.888 bytes.**
- Risco incremental baixo: a área alvo já está corrompida.
- Com o bootloader restaurado, a fase 2 (OS + assets) volta a ser
  possível pela via normal do SD (`firmware.zlib`), seguindo o
  `docs/tutorial-recuperacao-sd.md`.

---

## 5. Busca por imagem de referência confiável

Com os termos corretos agora identificados, vale reabrir a busca —
específica e diferente da anterior:

- **`dcboot.bin` oficial do S1 Pro** — prioridade máxima (ver §2.6):
  buscar no site da Creality, nos releases ZIP do fork ThomasToka e em
  repositórios/fóruns que espelhem os pacotes de tela oficiais
- `"F1C100s" "Ender 3 S1 Pro" screen dump`
- `"K600+" DGUS Creality touchscreen recovery`
- Fóruns de eletrônica hobbista (elektroda.com, linux-sunxi forums,
  EEVblog) em vez de fóruns de impressão 3D — porque essa combinação de
  hardware atrai um público diferente (hackers de Allwinner), não o
  público tradicional de reparo de impressora
- GitHub: buscar por repositórios que mencionem `F1C100s` + `Creality`
  ou `DGUS` + `sunxi-fel`

Se alguém já fez essa recuperação por FEL em outra unidade, é bem
provável que tenha publicado o dump justamente porque o modo FEL torna
isso trivial de compartilhar (`sunxi-fel spiflash-read` gera o arquivo
pronto).

---

## 6. Ordem de execução recomendada

1. **Tentar o procedimento SD em duas fases (§2.7) — o kit está
   completo e versionado no repo (`dcboot.bin` + `firmware.zlib` +
   `private/` + `DWIN_SET/`).** Fase 1 = apenas `dcboot.bin`; fase 2 =
   remover `dcboot.bin` e colocar os demais. É o único caminho que pode
   resolver **sem solda**. Se falhar, obter alternativa: buscar outra
   fonte do `dcboot.bin` oficial do S1 Pro e confirmar compatibilidade
2. Preparar ambiente NixOS atualizado (Seção 4.1.1) — baixo risco, faça
   já
3. Teste de continuidade nos pinos 67–70 (Seção 4.1.2) — baixo risco,
   sem solda ainda
4. Busca direcionada por dump da comunidade (Seção 5) — em paralelo,
   custo zero
5. Decisão: se achar trilha acessível sem solda em componente próximo →
   conectar USB e testar `sunxi-fel version` (Seção 4.1.3)
6. **Se o SD falhar (passo 1) e houver acesso FEL → Frente C (§4.3):
   gravar `dcboot.bin` direto na flash** (`sunxi-fel spiflash-write 0
   dcboot.bin`), depois fase 2 via SD. Alternativa sem FEL: mesma
   gravação via clipe SOIC-8 com a imagem padada para 16 MB (§4.3)
7. Se não houver ponto acessível → avaliar se vale soldar direto no
   QFN88 (considerar buscar ajuda de alguém com experiência em retrabalho
   fino, se você não tiver)
8. Assim que houver imagem confiável (doador via Frente B, ou dump da
   comunidade) → gravar via FEL (mais seguro) ou via clipe SOIC-8
   (alternativa)
9. Verificar sempre lendo de volta e comparando hash antes de remontar

---

## 7. Checklist de segurança consolidado

- [ ] Nunca grave nada na flash sem ter uma imagem cujo tamanho bate
      exatamente com 16.777.216 bytes
- [ ] Sempre leia o estado atual antes de qualquer gravação (diagnóstico
      e possibilidade de reverter)
- [ ] Teste de continuidade antes de soldar
- [ ] Confirme alimentação 3,3V em todo o circuito de solda (chip é
      3,3V, USB do PC fornece 5V em VBUS — não ligue VBUS diretamente
      em UVCC sem regulador, a tela já tem sua própria alimentação)
- [ ] Verifique (`sha256sum`) qualquer imagem obtida da comunidade contra
      pelo menos uma segunda fonte antes de gravar, se possível

---

## Apêndice A: Dados técnicos de referência

```
Impressora:        Creality Ender-3 S1 Pro
Placa-mãe:         CR-FDM-v2.4.S1_v301 (STM32F401)
Tela:              4SZCX4800M043 / V434.HYS Rev 1.1
SoC da tela:       Allwinner F1C100s (QFN88, 10x10mm)
  Pino 67:         UVCC (3.3V)
  Pino 68:         USB-DM
  Pino 69:         USB-DP
  Pino 70:         RESET#
Flash SPI:         XMC XM25QH128CHIG, 16MB, SPI simples, 1-3MHz
Camada de SW:      DGUS (DWIN) sobre kernel "K600+"
USB FEL VID:PID:   1f3a:efe8 (Allwinner padrão)
Firmware testado:  Ender-3 S1_Pro_HWv24S1_301_SWV2.0.8.26F4_FDM_LASER
                   (não requer dcboot.bin nesta versão)
```

## Apêndice B: Inventário de arquivos do repositório

### Ferramentas

- `tools/spi_flash_programmer.ino` — firmware Arduino para
  leitura/gravação via clipe SOIC-8 (Frente B)
- `tools/spi_tool.py` — script Python de controle (dump/erase/write/verify)
- `nix/shell.nix` — ambiente NixOS (arduino-cli, python3+pyserial,
  sunxi-tools, lsusb)

### Kit de recuperação SD (§2.6–§2.7)

- `dcboot.bin` — bootloader eGON/Allwinner da tela; fase 1 (regrava a
  área de boot); também usado direto na flash na Frente C (§4.3)
- `firmware.zlib` — OS da tela comprimido (magic `ZLIB` + zlib);
  fase 2
- `private/` — assets stock variante DACAI (fase 2; referência
  primária de offsets, §2.5)
- `DWIN_SET/` — assets stock variante DWIN (fase 2; a tela escolhe a
  pasta da sua variante)

### Documentação

- `README.md` — visão geral e hardware confirmado
- Este documento — plano consolidado e log de investigação canônico
- `docs/tutorial-recuperacao-sd.md` — tutorial passo a passo da
  recuperação SD em duas fases
- `docs/backup-flash-nixos.md` — guia detalhado de ambiente NixOS para
  a Frente B
- `docs/Readme_firmware_update_CN_EN.txt` — Readme oficial Creality do
  pacote de atualização (GBK), com o procedimento em duas fases
- `docs/XM25QH128C_Ver2.1.pdf` — datasheet da flash SPI
- `docs/3D Printer User Manual Ender-3 S1 Pro.pdf` — manual oficial da
  impressora
- `AGENTS.md` — orientações para sessões de agente
- `images/` — fotos da placa/chip
