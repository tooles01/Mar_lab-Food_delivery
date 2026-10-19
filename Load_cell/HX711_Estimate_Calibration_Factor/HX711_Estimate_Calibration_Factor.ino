/*
 * HX711_Estimate_Calibration_Factor.ino
 * 
 * Get estimated calibration factor using HX711 package (https://github.com/bogde/HX711)
 * 
 * 
 * 1. Remove all weight from the scale and upload the sketch
 * 2. Place a known weight on the scale and enter the value
 *    ex: for 50g weight, enter "weight50"
 * 3. The sketch will calculate an estimated calibration factor
 * 
 * 
 * Note: Scale must be correctly tared. If the weights are being weird:
 *  - Remove everything from the scale
 *  - Enter "tare"
 *  - Place a known weight and do it again
 * 
 * Calibration factor should be somewhere around -1800
 * 
 * 
 * Arduino pin 2 -> HX711 CLK
 * 3 -> DOUT
 * 5V -> VCC
 * GND -> GND
 * 
 * 
 *  
 * ST 2026 
*/

#include "HX711.h"

#define DOUT  3
#define CLK  2

HX711 scale;

float calibration_factor = 0;
float current_reading;
String inString;

int idx_start;
int idx_number_start;
String number_string;
float weight_value;

void setup() {
  Serial.begin(9600);
  Serial.println("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~");
  Serial.println("HX711 calibration sketch");
  Serial.println("Provides estimated calibration factor");
  
  scale.begin(DOUT, CLK);
  scale.set_scale();
  scale.tare();
  
  Serial.println("Place a weight on the scale");
  Serial.println("Enter the weight by sending 'weight50' (for 50g)");
}

void loop() {

  scale.set_scale(calibration_factor); //Adjust to this calibration factor
  current_reading = scale.get_units();

  Serial.print("Reading: ");
  Serial.print(current_reading);
  Serial.print(" g");
  Serial.print("\tcalibration_factor: ");
  Serial.println(calibration_factor);
  
  if (Serial.available()) {
    inString = Serial.readString();
    inString.trim();  // remove leading/trailing whitespaces
    if (inString.equals("tare")) {
      Serial.println("Resetting scale to zero");
      scale.tare();
      // NOTE: this does not adjust calibration factor, it just does the offset
    }
    else if (inString.indexOf("weight") != -1) {
      // Get the weight that was entered CANNOT BE 0
      idx_start = inString.indexOf("weight");
      idx_number_start = idx_start + 6; // length of "weight"
      number_string = inString.substring(idx_number_start);
      weight_value = number_string.toFloat();

      Serial.print("received weight: ");
      Serial.print(number_string);
      Serial.println(" g");

      // Call get_value (raw units, not affected by previous caliration)
      current_reading = scale.get_value(10);  // average of 10 raw readings
      Serial.print("current reading: ");
      Serial.println(current_reading);

      // Divide by known weight
      calibration_factor = current_reading / weight_value;  // units are grams      
    }
    else {
      // set the calibration factor to this number
      calibration_factor = inString.toFloat();
      Serial.print("Setting calibration factor to ");
      Serial.println(calibration_factor);
    }
  }
}
