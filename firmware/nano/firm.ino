#include <Wire.h>

const int IR_sensor_pin = 16;

// DRV8830 motor driver settings
#define DRV8830_ADDR_CH1 0x63
#define DRV8830_ADDR_CH2 0x63
#define CONTROL 0x00
#define FAULT 0x01

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Wire.begin();

  init_drv8830();

  pinMode(IR_sensor_pin, INPUT);

  Serial.println("Humandetect start");
}

void loop() {
  if (is_human_detected()) {
    kubihuri_left();
    delay(700);
    kubihuri_right();
    delay(700);
  }
}

bool is_human_detected() {
  return digitalRead(IR_sensor_pin);
}

void kubihuri_left() {
  // CH1 free
  free_motor(1);
  // CH0 control
  run_motor(0, 0.1);
  delay(30);
  run_motor(0, 0.5);
  delay(50);
  run_motor(0, 0.8);
  delay(2000);
  free_motor(0);
  delay(2000);
  stop_motor(0);
  delay(5000);
}

void kubihuri_right() {
  // CH0 free
  free_motor(0);
  // CH1 control
  run_motor(1, 0.1);
  delay(30);
  run_motor(1, 0.5);
  delay(50);
  run_motor(1, 0.8);
  delay(2000);
  free_motor(1);
  delay(2000);
  stop_motor(1);
  delay(5000);
}

void init_drv8830() {
  // DRV8830
  // CH1
  Wire.beginTransmission(DRV8830_ADDR_CH1);
  Wire.write(CONTROL);
  Wire.write(0x00 << 2 | 0x00);
  Wire.endTransmission();

  Wire.beginTransmission(DRV8830_ADDR_CH1);
  Wire.write(FAULT);
  Wire.write(0x80);
  Wire.endTransmission();

  // CH2
  Wire.beginTransmission(DRV8830_ADDR_CH2);
  Wire.write(CONTROL);
  Wire.write(0x00 << 2 | 0x00);
  Wire.endTransmission();

  Wire.beginTransmission(DRV8830_ADDR_CH2);
  Wire.write(FAULT);
  Wire.write(0x80);
  Wire.endTransmission();
}

/*****************************************/
/*  Motor Control                        */
/*****************************************/

// ch0 or ch1
// speed 0.0 ~ 1.0
void run_motor(int ch, float spd) {
  Wire.beginTransmission(ch ? DRV8830_ADDR_CH2 : DRV8830_ADDR_CH1);
  Wire.write(CONTROL);
  Wire.write(int(0x3F * spd) << 2 | 0x01);
  Wire.endTransmission();
}

// ch0 or ch1
void free_motor(int ch) {
  Wire.beginTransmission(ch ? DRV8830_ADDR_CH2 : DRV8830_ADDR_CH1);
  Wire.write(CONTROL);
  Wire.write(0x00 << 2 | 0x00);
  Wire.endTransmission();
}

// ch0 or ch1
void stop_motor(int ch) {
  Wire.beginTransmission(ch ? DRV8830_ADDR_CH2 : DRV8830_ADDR_CH1);
  Wire.write(CONTROL);
  Wire.write(0x00 << 2 | 0x03);
  Wire.endTransmission();
}
