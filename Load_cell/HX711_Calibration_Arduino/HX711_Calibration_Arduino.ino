/*
 * HX711_Calibration_Arduino.ino
 * 
 * 
 * Modified version of Sparkfun example calibration script found at:
 * https://github.com/sparkfun/HX711-Load-Cell-Amplifier/blob/master/firmware/SparkFun_HX711_Calibration/SparkFun_HX711_Calibration.ino
 * 
 * 
 * Example using the SparkFun HX711 breakout board with a scale
 *

 This is the calibration sketch. Use it to determine the calibration_factor that the main example uses. It also
 outputs the zero_factor useful for projects that have a permanent mass on the scale in between power cycles.

 Setup your scale and start the sketch WITHOUT a weight on the scale
 Once readings are displayed place the weight on the scale
 Press +/- or a/z to adjust the calibration_factor until the output readings match the known weight
 Use this calibration_factor on the example sketch

 This example assumes pounds (lbs). If you prefer kilograms, change the Serial.print(" lbs"); line to kg. The
 calibration factor will be significantly different but it will be linearly related to lbs (1 lbs = 0.453592 kg).

 Your calibration factor may be very positive or very negative. It all depends on the setup of your scale system
 and the direction the sensors deflect from zero state
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
  Serial.println("HX711 calibration combo");
  Serial.println("Remove all weight from scale");
  Serial.println("After readings begin, place known weight on scale");
  Serial.println("Enter any value (must be 2+ digits long) to update the calibration factor");
  Serial.println("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~");
  Serial.println("Also provides estimated calibration factor");
  
  scale.begin(DOUT, CLK);
  scale.set_scale();
  scale.tare();
  
  long zero_factor = scale.read_average(); //Get a baseline reading
  Serial.print("Zero factor: "); //This can be used to remove the need to tare the scale. Useful in permanent scale projects.
  Serial.println(zero_factor);

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
      scale.set_scale(calibration_factor); //Adjust to this calibration factor
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

      // Divide by known weight
      calibration_factor = current_reading / weight_value;  // units are grams

      Serial.print("estimated calibration factor: ");
      Serial.println(calibration_factor);

    }
    else {
      // set the calibration factor to this number
      calibration_factor = inString.toFloat();
      Serial.print("Setting calibration factor to ");
      Serial.println(calibration_factor);
    }
  }
}
