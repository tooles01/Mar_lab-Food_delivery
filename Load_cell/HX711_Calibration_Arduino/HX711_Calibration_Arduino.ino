/*
 * HX711_Calibration_Arduino_2scales.ino
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
 * 3 -> DOUT_1
 * 5V -> VCC
 * GND -> GND
 * 
 * 
 * 
 * ST 2026
 */

#include "HX711.h"

#define DOUT_1  3
#define CLK_1  2

#define DOUT_2 5
#define CLK_2 4

HX711 scale_1;
HX711 scale_2;

float calibration_factor = 0;
float current_reading_1;
float current_reading_2;
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
  
  scale_1.begin(DOUT_1, CLK_1);
  scale_1.set_scale();
  scale_1.tare();
  scale_2.begin(DOUT_2, CLK_2);
  scale_2.set_scale();
  scale_2.tare();
  
  long zero_factor_1 = scale_1.read_average(); //Get a baseline reading
  long zero_factor_2 = scale_2.read_average(); //Get a baseline reading
  Serial.print("Zero factor_1: "); //This can be used to remove the need to tare the scale. Useful in permanent scale1 projects.
  Serial.println(zero_factor_1);
  Serial.print("Zero factor_2: "); //This can be used to remove the need to tare the scale. Useful in permanent scale1 projects.
  Serial.println(zero_factor_2);

  Serial.println("Place a weight on the scale1");
  Serial.println("Enter the weight by sending 'weight50' (for 50g)");
}

void loop() {

  scale_1.set_scale(calibration_factor); //Adjust to this calibration factor
  current_reading_1 = scale_1.get_units();
  scale_2.set_scale(calibration_factor); //Adjust to this calibration factor
  current_reading_2 = scale_2.get_units();

  Serial.print("Scale1: ");
  Serial.print(current_reading_1);
  Serial.print(" g\t");
  Serial.print("Scale2: ");
  Serial.print(current_reading_2);
  Serial.print(" g");
  Serial.print("\tcalibration_factor: ");
  Serial.println(calibration_factor);
  
  if (Serial.available()) {
    inString = Serial.readString();
    inString.trim();  // remove leading/trailing whitespaces
    if (inString.equals("tare")) {
      Serial.println("Resetting scale1 to zero");
      scale_1.tare();
      scale_1.set_scale(calibration_factor); //Adjust to this calibration factor
      scale_2.tare();
      scale_2.set_scale(calibration_factor); //Adjust to this calibration factor
    }
    
    // Estimate calibration factor
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
      current_reading_1 = scale_1.get_value(10);  // average of 10 raw readings

      // Divide by known weight
      calibration_factor = current_reading_1 / weight_value;  // units are grams

      Serial.print("estimated calibration factor: ");
      Serial.println(calibration_factor);

    }
    // Set calibration factor
    else {
      // set the calibration factor to this number
      calibration_factor = inString.toFloat();
      Serial.print("Setting calibration factor to ");
      Serial.println(calibration_factor);
    }
  }
}
