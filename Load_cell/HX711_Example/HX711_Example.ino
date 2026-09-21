/*
 * HX711_Calibration.ino
 * 
 * 
 * Modified version of Sparkfun example script found at:
 * https://github.com/sparkfun/HX711-Load-Cell-Amplifier/blob/master/firmware/SparkFun_HX711_Example/SparkFun_HX711_Example.ino
 * 
 * 
 * Example using the SparkFun HX711 breakout board with a scale
 * 
 * ST 2026
 * 

 This example demonstrates basic scale output. See the calibration sketch to get the calibration_factor for your
 specific load cell setup.

 The HX711 does one thing well: read load cells. The breakout board is compatible with any wheat-stone bridge
 based load cell which should allow a user to measure everything from a few grams to tens of tons.
 Arduino pin 2 -> HX711 CLK
 3 -> DAT
 5V -> VCC
 GND -> GND

 The HX711 board can be powered from 2.7V to 5V so the Arduino 5V power should be fine.

*/

#include "HX711.h"

//#define calibration_factor -7050.0 //This value is obtained using the SparkFun_HX711_Calibration sketch
#define calibration_factor -1860.0

#define DOUT  3
#define CLK  2

HX711 scale;

float current_reading = 0.0;

void setup() {
  Serial.begin(9600);
  Serial.println("HX711 scale demo");

  scale.begin(DOUT, CLK);
  scale.set_scale(calibration_factor); //This value is obtained by using the SparkFun_HX711_Calibration sketch
  scale.tare(); //Assuming there is no weight on the scale at start up, reset the scale to 0

  Serial.println("Readings:");
}

void loop() {
  current_reading = scale.get_units();
  
  Serial.print("Reading: ");
  Serial.print(current_reading);
  //Serial.print(scale.get_units(), 1); //scale.get_units() returns a float
  //Serial.print(" lbs"); //You can change this to kg but you'll need to refactor the calibration_factor
  Serial.println(" g");
  //Serial.println();
}
