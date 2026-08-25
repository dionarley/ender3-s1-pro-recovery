#!/usr/bin/env python3
"""
Ferramenta host (PC) para controlar o Arduino programador de flash SPI.
Requer: pip install pyserial

Uso:
    python spi_tool.py id
    python spi_tool.py dump saida.bin
    python spi_tool.py erase
    python spi_tool.py write imagem.bin
"""

import serial
import time
import sys

PORT = 'COM5'          # Windows: 'COM5', 'COM7', etc. Linux/Mac: '/dev/ttyACM0' ou '/dev/ttyUSB0'
BAUD = 250000
CHIP_SIZE = 16 * 1024 * 1024  # 16.777.216 bytes
PAGE_SIZE = 256


def open_serial():
    ser = serial.Serial(PORT, BAUD, timeout=5)
    time.sleep(2)  # aguarda o Arduino resetar após abrir a porta serial
    ser.reset_input_buffer()
    return ser


def read_id(ser):
    ser.write(b'I')
    idbytes = ser.read(3)
    if len(idbytes) != 3:
        print("ERRO: não recebeu 3 bytes do JEDEC ID. Verifique as conexões.")
        return None
    print("JEDEC ID recebido:", idbytes.hex())
    print("(Compare esses 3 bytes com o datasheet do XM25QH128 antes de prosseguir)")
    return idbytes


def dump_chip(ser, outpath):
    print(f"Iniciando leitura completa ({CHIP_SIZE} bytes)...")
    ser.write(b'R')
    total = 0
    with open(outpath, 'wb') as f:
        while total < CHIP_SIZE:
            chunk = ser.read(PAGE_SIZE)
            if len(chunk) != PAGE_SIZE:
                print(f"AVISO: recebido {len(chunk)} bytes (esperado {PAGE_SIZE}) no offset {total}")
                if len(chunk) == 0:
                    print("Sem dados chegando — abortando. Verifique a conexão.")
                    break
            f.write(chunk)
            total += len(chunk)
            if total % (256 * 1024) < PAGE_SIZE:
                pct = 100.0 * total / CHIP_SIZE
                print(f"Lido {total}/{CHIP_SIZE} bytes ({pct:.1f}%)")
    print("Dump concluído:", outpath)
    print("Tamanho final:", total, "bytes (esperado 16777216)")
    if total != CHIP_SIZE:
        print("*** ATENÇÃO: tamanho não bate com o esperado. Não confie neste dump. ***")


def erase_chip(ser):
    print("Apagando chip inteiro — isso pode levar vários minutos, não desligue.")
    ser.write(b'E')
    resp = ser.read(1)
    if resp == b'K':
        print("Chip apagado com sucesso.")
    else:
        print("Falha ao confirmar apagamento. Resposta:", resp)


def write_chip(ser, inpath):
    with open(inpath, 'rb') as f:
        data = f.read()
    if len(data) != CHIP_SIZE:
        print(f"ERRO: arquivo tem {len(data)} bytes, esperado exatamente {CHIP_SIZE} bytes.")
        print("Abortando — grave apenas imagens do tamanho exato do chip.")
        return
    print("Iniciando gravação... (lembre-se de apagar o chip antes, com 'erase')")
    ser.write(b'W')
    total = 0
    for i in range(0, CHIP_SIZE, PAGE_SIZE):
        page = data[i:i + PAGE_SIZE]
        ser.write(page)
        ack = ser.read(1)
        if ack != b'K':
            print(f"ERRO na página offset {i}: sem confirmação (recebido {ack!r})")
            return
        total += len(page)
        if total % (256 * 1024) < PAGE_SIZE:
            pct = 100.0 * total / CHIP_SIZE
            print(f"Gravado {total}/{CHIP_SIZE} bytes ({pct:.1f}%)")
    print("Gravação concluída.")


def verify_chip(ser, inpath):
    """Lê o chip de volta e compara com o arquivo, sem gravar nada."""
    with open(inpath, 'rb') as f:
        expected = f.read()
    if len(expected) != CHIP_SIZE:
        print("Arquivo de referência não tem o tamanho esperado.")
        return
    ser.write(b'R')
    total = 0
    mismatches = 0
    while total < CHIP_SIZE:
        chunk = ser.read(PAGE_SIZE)
        if len(chunk) != PAGE_SIZE:
            break
        exp_chunk = expected[total:total + PAGE_SIZE]
        if chunk != exp_chunk:
            mismatches += 1
            if mismatches <= 5:
                print(f"Diferença no offset {total}")
        total += len(chunk)
    if mismatches == 0 and total == CHIP_SIZE:
        print("Verificação OK: chip idêntico ao arquivo.")
    else:
        print(f"Verificação FALHOU: {mismatches} blocos diferentes, {total} bytes lidos.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]
    ser = open_serial()

    if action == 'id':
        read_id(ser)
    elif action == 'dump':
        outpath = sys.argv[2] if len(sys.argv) > 2 else 'dump.bin'
        dump_chip(ser, outpath)
    elif action == 'erase':
        erase_chip(ser)
    elif action == 'write':
        if len(sys.argv) < 3:
            print("Especifique o arquivo .bin para gravar")
            sys.exit(1)
        write_chip(ser, sys.argv[2])
    elif action == 'verify':
        if len(sys.argv) < 3:
            print("Especifique o arquivo .bin para comparar")
            sys.exit(1)
        verify_chip(ser, sys.argv[2])
    else:
        print("Ação desconhecida:", action)
        print(__doc__)

    ser.close()
