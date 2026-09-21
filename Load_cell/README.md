# Load cell reading


## Materials:
- Arduino UNO
- Load cell (taken from [WeighGram Top-600](https://www.amazon.com/dp/B000O37TDO?ref=clp_hp_h_pc&th=1) scale)
- [HX711 Amplifier](https://www.sparkfun.com/sparkfun-load-cell-amplifier-hx711.html#content-features)
- Dupont wires


## Setup

- Break load cell out of scale. Connect female crimp pins to red, black, green, and white wires
- Connect load cell to Sparkfun HX711 amplifier board
    - Swap white and green wire positions
- Connect DX711 to Arduino UNO
    - Jumper VCC/VDD
    - VCC ---> 3.3V # TODO check if this should be 5V instead...
    - DAT ---> 3
    - CLK ---> 2
    - GND ---> GND

### Install HX711 package

- Download .zip file from [HX711 Github](https://github.com/bogde/HX711).
- In Arduino, go to Sketch --> Include Library --> Add .ZIP Library
- Select HX711-master.zip

## Calibration

Determine the calibration factor using ```HX711_Calibration.ino```.
- Remove all weight from scale
- Upload sketch
    - Scale will tare and reset to zero
- Open serial monitor at 9600 baud


To be continued...


