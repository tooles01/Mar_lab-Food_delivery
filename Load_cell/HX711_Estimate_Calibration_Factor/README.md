# HX711_Estimate_Calibration_Factor.ino

Uses known weights to provide an estimated calibration factor. Calibration factor is needed for acquiring accurate readings from the load cell.


1. Remove all weight from the scale and upload the sketch
2. Open the serial monitor at 9600 baud
3. Place a known weight on the scale and enter the value via the serial monitor  
    - *Example:* for a 50g weight, enter ```weight50```
4. The sketch will display the current reading and an estimated calibration factor

Entering a number via the serial monitor will update the calibration factor to that number.  
*Example:* Entering ```1950``` will update the calibration factor to 1950

---

The estimated calibration factor is useful when first getting started with the HX711 amplifier/any new load cell, as calibration factors can range greatly. This estimated value provides a starting point for further tweaking and debugging.  

--- 

Note: Scale must be correctly tared. If the weights are being weird:
- Remove everything from the scale
- Enter "tare"
- Place a known weight and do it again