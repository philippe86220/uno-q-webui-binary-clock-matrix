#include <Arduino.h>
#include <Arduino_RouterBridge.h>

// C API Matrix for the UNO-Q  
extern "C" void matrixWrite(const uint32_t *buf);
extern "C" void matrixBegin();

// Matrix geometry
const int MATRIX_WIDTH  = 13;
const int MATRIX_HEIGHT = 8;

// 3x5 font for the numbers 0 to 9
// Each line consists of 3 bits (b2 b1 b0), 1 = LED on, 0 = LED off.
const uint8_t DIGITS[10][5] = {
    // 0
    { 0b111, 0b101, 0b101, 0b101, 0b111 }, 
    // 1
    { 0b001, 0b001, 0b001, 0b001, 0b001 },
    // 2
    { 0b111, 0b001, 0b111, 0b100, 0b111 },
    // 3
    { 0b111, 0b001, 0b111, 0b001, 0b111 },
    // 4
    { 0b101, 0b101, 0b111, 0b001, 0b001 },
    // 5
    { 0b111, 0b100, 0b111, 0b001, 0b111 },
    // 6
    { 0b111, 0b100, 0b111, 0b101, 0b111 },
    // 7
    { 0b111, 0b001, 0b001, 0b001, 0b001 },
    // 8
    { 0b111, 0b101, 0b111, 0b101, 0b111 },
    // 9
    { 0b111, 0b101, 0b111, 0b001, 0b111 }
};

// signing of functions
void updateTime(int32_t hour, int32_t minute, int32_t second);
void buildClockBitmap(int hour, int minute, bool showColon, uint32_t frame[4]);
void drawDigit(int digit, int xOffset, uint32_t frame[4]);
void setPixelBit(uint32_t frame[4], int x, int y);
void clearMatrix();


void setup() {
    Bridge.begin();
    matrixBegin();
    Bridge.provide("updateTime", updateTime);
    Bridge.provide("clearMatrix", clearMatrix);


}

void loop() {
    delay(10);
}

void clearMatrix() {
  uint32_t frame[4] = {0, 0, 0, 0};
  matrixWrite(frame);
}


// RPC function called from Python
void updateTime(int32_t hour, int32_t minute, int32_t second) {
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59 || second < 0 || second > 59) {
    return;
  }

  bool showColon = (second % 2 == 0);

  uint32_t frame[4];
  buildClockBitmap((int)hour, (int)minute, showColon, frame);

  matrixWrite(frame);
}


void buildClockBitmap(int hour, int minute, bool showColon, uint32_t frame[4]) {

    // Reset all output bits
    frame[0] = frame[1] = frame[2] = frame[3] = 0;

    int hTens  = hour   / 10;
    int hUnits = hour   % 10;
    int mTens  = minute / 10;
    int mUnits = minute % 10;

    // Hours
   if (hour >= 10) drawDigit(hTens, 0, frame);
   drawDigit(hUnits, 3, frame);

    // Two points: flashing
    if (showColon) {
        setPixelBit(frame, 6, 2);
        setPixelBit(frame, 6, 4);
    }

    // Minutes
   drawDigit(mTens, 7, frame); 
   drawDigit(mUnits, 10, frame);
    
    
}

void drawDigit(int digit, int xOffset, uint32_t frame[4]) {
    if (digit < 0 || digit > 9) return;

    const int yOffset = 1; // chiffres tirés des lignes 1 à 5

    for (int row = 0; row < 5; row++) {
        uint8_t pattern = DIGITS[digit][row];

        for (int col = 0; col < 3; col++) {
            if (pattern & (1u << (2 - col))) {
                setPixelBit(frame, xOffset + col, yOffset + row);
            }
        }
    }
}


void setPixelBit(uint32_t frame[4], int x, int y) {
    if (x < 0 || x >= MATRIX_WIDTH) return;
    if (y < 0 || y >= MATRIX_HEIGHT) return;

    int index = y * MATRIX_WIDTH + x;  // 0 à 103
    int word  = index / 32;            // 0 à 3
    int bit   = index % 32;            // 0 à 31

    frame[word] |= (1u << bit);
}

