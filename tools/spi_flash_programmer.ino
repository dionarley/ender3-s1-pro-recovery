// ============================================================
//  Gravador/Leitor SPI NOR Flash - XM25QH128 (16MB / 128Mbit)
//  Arduino UNO R3
// ============================================================
//  ATENÇÃO: o chip opera em 3.3V. Use conversor de nível lógico
//  (ou divisores resistivos) nas linhas CS, MOSI e SCK antes de
//  ligar ao chip. MISO pode ligar direto ao Arduino.
//
//  Pinagem SOIC-8 (25xx padrão):
//    1 CS#   2 MISO   3 WP#(->VCC)   4 GND
//    5 MOSI  6 CLK    7 HOLD#(->VCC) 8 VCC(3.3V)
//
//  Conexões Arduino (via conversor de nível, exceto MISO):
//    D10 -> CS#
//    D11 -> MOSI
//    D12 <- MISO  (ligação direta)
//    D13 -> CLK
//    3.3V -> VCC, WP#, HOLD#
//    GND  -> GND
//
//  Protocolo serial (controlado pelo script Python no PC):
//    'I' -> lê e devolve 3 bytes do JEDEC ID
//    'R' -> lê o chip inteiro (16.777.216 bytes) e transmite via serial
//    'E' -> apaga o chip inteiro (chip erase, pode levar minutos)
//    'W' -> recebe 16.777.216 bytes via serial e grava página a página
//           (envia 'K' após cada página de 256 bytes gravada com sucesso)
// ============================================================

#include <SPI.h>

const uint8_t PIN_CS = 10;

#define CMD_WRITE_ENABLE    0x06
#define CMD_READ_STATUS1    0x05
#define CMD_READ_DATA       0x03
#define CMD_PAGE_PROGRAM    0x02
#define CMD_CHIP_ERASE      0xC7
#define CMD_JEDEC_ID        0x9F

const uint32_t CHIP_SIZE = 16777216UL; // 16 MB
const uint16_t PAGE_SIZE = 256;

inline void csLow()  { digitalWrite(PIN_CS, LOW); }
inline void csHigh() { digitalWrite(PIN_CS, HIGH); }

uint8_t spiXfer(uint8_t b) {
  return SPI.transfer(b);
}

void writeEnable() {
  csLow();
  spiXfer(CMD_WRITE_ENABLE);
  csHigh();
}

uint8_t readStatus() {
  csLow();
  spiXfer(CMD_READ_STATUS1);
  uint8_t s = spiXfer(0x00);
  csHigh();
  return s;
}

// Aguarda o bit BUSY (bit0) do registrador de status zerar.
// Sem timeout: se o chip não responder, trave é intencional para
// não seguir escrevendo em estado indefinido. Reset manual se travar.
void waitBusy() {
  while (readStatus() & 0x01) {
    delay(1);
  }
}

void readJedecId(uint8_t id[3]) {
  csLow();
  spiXfer(CMD_JEDEC_ID);
  id[0] = spiXfer(0x00);
  id[1] = spiXfer(0x00);
  id[2] = spiXfer(0x00);
  csHigh();
}

void readData(uint32_t addr, uint8_t *buf, uint16_t len) {
  csLow();
  spiXfer(CMD_READ_DATA);
  spiXfer((addr >> 16) & 0xFF);
  spiXfer((addr >> 8) & 0xFF);
  spiXfer(addr & 0xFF);
  for (uint16_t i = 0; i < len; i++) {
    buf[i] = spiXfer(0x00);
  }
  csHigh();
}

void pageProgram(uint32_t addr, uint8_t *buf, uint16_t len) {
  writeEnable();
  csLow();
  spiXfer(CMD_PAGE_PROGRAM);
  spiXfer((addr >> 16) & 0xFF);
  spiXfer((addr >> 8) & 0xFF);
  spiXfer(addr & 0xFF);
  for (uint16_t i = 0; i < len; i++) {
    spiXfer(buf[i]);
  }
  csHigh();
  waitBusy();
}

void chipErase() {
  writeEnable();
  csLow();
  spiXfer(CMD_CHIP_ERASE);
  csHigh();
  waitBusy();
}

void handleRead() {
  uint8_t buf[PAGE_SIZE];
  for (uint32_t addr = 0; addr < CHIP_SIZE; addr += PAGE_SIZE) {
    readData(addr, buf, PAGE_SIZE);
    Serial.write(buf, PAGE_SIZE);
  }
}

void handleWrite() {
  uint8_t buf[PAGE_SIZE];
  for (uint32_t addr = 0; addr < CHIP_SIZE; addr += PAGE_SIZE) {
    uint16_t got = 0;
    while (got < PAGE_SIZE) {
      if (Serial.available()) {
        buf[got++] = Serial.read();
      }
    }
    pageProgram(addr, buf, PAGE_SIZE);
    Serial.write('K');
  }
}

void setup() {
  pinMode(PIN_CS, OUTPUT);
  csHigh();
  SPI.begin();
  SPI.setClockDivider(SPI_CLOCK_DIV8); // ~2MHz, seguro para fiação em protoboard
  SPI.setDataMode(SPI_MODE0);
  SPI.setBitOrder(MSBFIRST);
  Serial.begin(250000);
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'I') {
      uint8_t id[3];
      readJedecId(id);
      Serial.write(id, 3);
    } else if (cmd == 'R') {
      handleRead();
    } else if (cmd == 'E') {
      chipErase();
      Serial.write('K');
    } else if (cmd == 'W') {
      handleWrite();
    }
  }
}
