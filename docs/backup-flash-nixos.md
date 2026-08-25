# Backup da Flash SPI do Display (Ender-3 S1 Pro) via Arduino UNO no NixOS

Guia passo a passo para preparar o ambiente no NixOS, fazer o **dump de backup**
do chip XM25QH128CHIG saudável e só então tentar gravar/recuperar o chip com
defeito. **Nunca pule a etapa de backup e verificação — uma vez apagado, o chip
original não volta.**

---

## Visão geral do fluxo

1. Preparar ambiente Nix (arduino-cli + Python/pyserial)
2. Liberar permissão de acesso à porta serial
3. Compilar e enviar o firmware do Arduino (`spi_flash_programmer.ino`)
4. Testar a comunicação (ler JEDEC ID)
5. **Fazer o dump do chip saudável (doador) — backup obrigatório**
6. Validar que o backup tem 16.777.216 bytes e bate com o esperado
7. Só então: apagar e gravar o chip com defeito
8. Verificar a gravação lendo de volta e comparando

---

## Checklist de segurança antes de começar

- [ ] O chip a ser lido/gravado está em **3,3V** — confirme que o conversor de
      nível lógico (ou divisores resistivos) está entre o Arduino (5V) e as
      linhas CS, MOSI e SCK.
- [ ] GND do Arduino e do circuito da garra SOIC-8 estão **em comum**.
- [ ] WP# (pino 3) e HOLD#/RESET# (pino 7) do chip estão puxados para VCC
      (3,3V).
- [ ] Você tem os dois arquivos gerados anteriormente:
      `spi_flash_programmer.ino` e `spi_tool.py`, na mesma pasta de trabalho.

---

## 1. Preparando o ambiente Nix

Crie uma pasta de trabalho para o projeto e um `shell.nix` reprodutível:

```bash
mkdir -p ~/ender3-flash-recovery
cd ~/ender3-flash-recovery
# copie spi_flash_programmer.ino e spi_tool.py para esta pasta
```

Crie o arquivo `shell.nix`:

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "spi-flash-recovery";

  buildInputs = with pkgs; [
    arduino-cli
    python3
    python3Packages.pyserial
  ];

  shellHook = ''
    echo "Ambiente pronto: arduino-cli $(arduino-cli version)"
    echo "Python: $(python3 --version)"
  '';
}
```

Entre no ambiente:

```bash
nix-shell
```

Isso te dá `arduino-cli` e `python3` com `pyserial` disponíveis sem instalar
nada globalmente no sistema — se preferir algo permanente, adicione os mesmos
pacotes em `environment.systemPackages` no seu `configuration.nix` e rode
`sudo nixos-rebuild switch`, mas o `shell.nix` já resolve para uma sessão de
trabalho pontual.

---

## 2. Permissões de porta serial no NixOS

O Arduino aparece normalmente como `/dev/ttyACM0` (às vezes `/dev/ttyUSB0` se
usar um clone com chip CH340). Por padrão, esse dispositivo pertence ao grupo
`dialout`, e seu usuário provavelmente não está nele.

**Opção declarativa (recomendada, permanente):**

No seu `configuration.nix`:

```nix
users.users.SEU_USUARIO.extraGroups = [ "dialout" ];
```

Depois:

```bash
sudo nixos-rebuild switch
```

Faça **logout/login** (ou reinicie) para o grupo entrar em efeito.

**Opção rápida (só para testar agora, não persiste após reboot):**

```bash
sudo chmod 666 /dev/ttyACM0
```

Confira qual dispositivo apareceu com:

```bash
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
dmesg | tail -20   # deve mostrar o Arduino sendo detectado ao conectar o USB
```

---

## 3. Compilando e enviando o firmware do Arduino

Dentro do `nix-shell`:

```bash
# inicializa a configuração do arduino-cli (primeira vez apenas)
arduino-cli config init

# atualiza o índice de placas/cores
arduino-cli core update-index

# instala o core AVR (necessário para o Uno)
arduino-cli core install arduino:avr

# confirma que o Arduino foi detectado
arduino-cli board list
```

A saída de `board list` deve mostrar algo como:

```
Port         Protocol Type              Board Name  FQBN            Core
/dev/ttyACM0 serial   Serial Port (USB) Arduino Uno arduino:avr:uno arduino:avr
```

Anote a porta (`/dev/ttyACM0` no exemplo) — você vai usar em todos os passos
seguintes.

Compile e envie o sketch:

```bash
arduino-cli compile --fqbn arduino:avr:uno spi_flash_programmer.ino
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno spi_flash_programmer.ino
```

Se o `arduino-cli compile` reclamar que não encontra o `.ino` dentro de uma
pasta com o mesmo nome, mova o arquivo para dentro de uma subpasta chamada
`spi_flash_programmer/spi_flash_programmer.ino` — é uma exigência do formato
de sketch do Arduino, não específica do NixOS.

---

## 4. Ajustando a porta no script Python

Abra `spi_tool.py` e edite a linha:

```python
PORT = 'COM5'
```

Para:

```python
PORT = '/dev/ttyACM0'   # ajuste conforme o que apareceu no board list
```

---

## 5. Testando a comunicação (JEDEC ID)

Com o **chip saudável (doador)** já conectado na garra e o circuito
conferido:

```bash
python3 spi_tool.py id
```

Saída esperada: 3 bytes em hexadecimal. Se vier `ff ff ff` ou `00 00 00`,
**pare aqui** — há um problema de fiação ou nível lógico. Não prossiga para
leitura/gravação até resolver isso.

---

## 6. Fazendo o backup do chip saudável (dump) — etapa obrigatória

```bash
python3 spi_tool.py dump backup_chip_bom.bin
```

Isso vai levar entre 15 e 20 minutos a 250000 baud. O script mostra progresso
a cada 256KB lidos. Não desconecte nada durante a leitura.

---

## 7. Validando o backup antes de continuar

Confira o tamanho exato do arquivo:

```bash
stat -c '%s bytes' backup_chip_bom.bin
# ou
wc -c backup_chip_bom.bin
```

Deve retornar exatamente **16777216** bytes. Se vier diferente, o dump está
incompleto ou corrompido — repita o passo 6 antes de seguir.

Recomendo também tirar um segundo dump e comparar os dois com `diff` ou
`sha256sum`, para garantir que a leitura é estável e repetível:

```bash
python3 spi_tool.py dump backup_chip_bom_2.bin
sha256sum backup_chip_bom.bin backup_chip_bom_2.bin
```

Os dois hashes devem ser idênticos. Só com essa confirmação você tem um
backup em que pode confiar.

---

## 8. Só agora: gravando o chip com defeito

Troque a garra para o chip com problema. **Confirme visualmente o
posicionamento do entalhe/pino 1** antes de prosseguir.

```bash
python3 spi_tool.py id      # confirma que ainda está lendo algo coerente
python3 spi_tool.py erase   # pode levar vários minutos, não interrompa
python3 spi_tool.py write backup_chip_bom.bin
```

---

## 9. Verificação final

```bash
python3 spi_tool.py verify backup_chip_bom.bin
```

Deve retornar `Verificação OK: chip idêntico ao arquivo.` Só depois disso
remonte o display no Ender-3 S1 Pro e teste ligar o printer.

---

## Solução de problemas comuns no NixOS

| Sintoma | Causa provável | Solução |
|---|---|---|
| `Permission denied` ao abrir `/dev/ttyACM0` | Usuário fora do grupo `dialout` | Seção 2 |
| `arduino-cli board list` não mostra nada | Cabo USB só de energia, ou driver CH340 ausente | Troque o cabo; se for clone CH340, `nix-shell -p linuxPackages.ch341` costuma não ser necessário no kernel atual, mas confira `dmesg` |
| Porta muda de nome a cada boot (`ttyACM0` → `ttyACM1`) | Comportamento normal de enumeração USB | Sempre rode `arduino-cli board list` antes de cada sessão |
| `id` retorna `ff ff ff` | Nível lógico incorreto, GND não comum, ou garra mal posicionada | Revise o esquema da etapa anterior |
| Upload trava em "avrdude: stk500_recv()" | Porta errada ou Arduino ocupado por outro processo | Feche monitores seriais abertos, confirme a porta |

---

## Apêndice: estrutura de arquivos esperada

```
ender3-flash-recovery/
├── shell.nix
├── spi_flash_programmer.ino
├── spi_tool.py
├── backup_chip_bom.bin        (gerado no passo 6)
└── backup_chip_bom_2.bin      (gerado no passo 7, opcional)
```
