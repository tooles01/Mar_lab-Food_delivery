# HX711_Calibration_Arduino.ino 

An Arduino sketch for calibrating a load cell with an HX711 24-bit ADC amplifier. It supports two ways to calibrate:

1. **Automatic estimate.** Place a known weight on the scale and send `weight<grams>`. The sketch calculates the calibration factor for you.
2. **Manual tuning.** Type a calibration factor and watch the live readings. Adjust it until the reading matches your reference weight.

You can also tare the scale at any time. Use the automatic estimate to get close, then fine-tune by hand.

## Features

- Estimates the calibration factor from a single known weight
- Lets you enter a calibration factor at runtime, with no re-flashing
- Re-zeros the scale with a `tare` command
- Streams live readings and the active calibration factor over serial
- Prints the raw "zero factor" at startup. You can use it to skip taring in permanent installations.

## Hardware

### Materials

| Component | Notes |
|---|---|
| Arduino (Uno, Nano, etc.) | Any board supported by the HX711 library |
| [HX711 breakout board](https://www.sparkfun.com/sparkfun-load-cell-amplifier-hx711.html) | Load cell amplifier / ADC |
| Load cell | taken from [WeighGram Top-600](https://www.amazon.com/dp/B000O37TDO?ref=clp_hp_h_pc&th=1) scale |
| Dupont wires| |
| Known reference weight | Any accurately known mass. It must be non-zero. |

### Assembly
- Break load cell out of scale.
- Solder red and black wires to corresponding positions on Sparkfun HX711 amplifier board
    - red wire --> **RED**
    - black wire --> **BLK**
- Solder white and green wires to **opposite** positions on HX711 board
    - green wire --> **WHT**
    - white wire --> **GRN**

### Wiring to Arduino

Jumper VCC/VDD on HX711

#### Scale #1
| HX711 Pin | Arduino Pin |
|---|---|
| `DAT` (data) | `3` |
| `CLK` (SCK) | `2` |
| `VCC` | `3.3V` # TODO check if this should be 5V instead...|
| `GND` | `GND` |

#### Scale #2
| HX711 Pin | Arduino Pin |
|---|---|
| `DAT` (data) | `5` |
| `CLK` (SCK) | `4` |
| `VCC` | `3.3V` # TODO check if this should be 5V instead...|
| `GND` | `GND` |

<!--
To use different pins, edit these lines:

```cpp
#define DOUT  3
#define CLK   2
```
-->
<br>

---
## Firmware

### Install HX711 Arduino package
- Download .zip file from [HX711 Github](https://github.com/bogde/HX711).
- In Arduino, go to **Sketch** --> **Include Library** --> **Add .ZIP Library**
- Select **HX711-master.zip** from your downloads folder

### Upload sketch
- Remove all weight from scale
- Plug in Arduino via USB
- Upload sketch
    - Open [```HX711_Calibration_Arduino.ino```](HX711_Calibration_Arduino) in the Arduino IDE
    - Select:
        - **Tools** --> **Board** --> Board type you are using
        - **Port** --> Port the board is connected to
        - **Sketch** --> **Upload**
    - Scale will tare and reset to zero

<br>

---
## Getting Started

1. Wire the hardware as shown above.
2. Open the sketch in the Arduino IDE and upload it to your board.
3. Open the **Serial Monitor** and set the baud rate to **9600**.
4. Set the line ending to **Newline** or **Both NL & CR**.
5. **Remove all weight** from the scale during startup. The sketch tares automatically.
6. Wait for the "Place a weight on the scale" prompt.

<br>

---
## Calibration Procedure

### Option A: Automatic estimate (recommended first step)

1. Place a known weight on the scale and let it settle.
2. Send the weight in grams in the form `weight<grams>`. For a 50 g weight, send:
   ```
   weight50
   ```
3. The sketch takes the average of 10 raw readings, divides it by the weight you entered, and applies the result as the new calibration factor.
4. The reading should now be close to the known weight.

### Option B: Manual fine-tuning

1. With the known weight still on the scale, type a new calibration factor (for example `-1883`) and press Enter.
2. Compare the `Reading:` value to the known weight.
   - If the reading is **too high**, increase the factor's magnitude.
   - If the reading is **too low**, decrease it.
3. Repeat until the reading matches.

### Save your result

Hard-code the final factor in your own project:

```cpp
scale.set_scale(YOUR_CALIBRATION_FACTOR);
scale.tare();
```

## Serial Commands

| Input | Action |
|---|---|
| `tare` | Resets the scale to zero and re-applies the current calibration factor |
| `weight<grams>` (e.g. `weight50`, `weight102.5`) | Estimates the calibration factor from the known weight currently on the scale |
| A number (e.g. `-1883`, `2280.5`) | Sets it directly as the calibration factor |

## Example Output

```
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
HX711 calibration combo
Remove all weight from scale
After readings begin, place known weight on scale
Enter any value (must be 2+ digits long) to update the calibration factor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Also provides estimated calibration factor
Zero factor: 8421937
Place a weight on the scale
Enter the weight by sending 'weight50' (for 50g)
Reading: inf g	calibration_factor: 0.00
received weight: 50 g
estimated calibration factor: -1879.42
Reading: 50.02 g	calibration_factor: -1879.42
```

The values above are only an illustration. Your numbers will differ.

## How It Works

- **`setup()`** starts serial communication and initializes the HX711. It calls `set_scale()` with no argument, then `tare()` to zero the scale. It prints a baseline "zero factor" and prompts you to place a weight.
- **`loop()`** applies the current `calibration_factor`, reads the weight with `get_units()`, and prints the reading and the factor. It then checks the serial buffer for one of three inputs:
  - **`tare`:** re-zeros the scale.
  - **`weight<N>`:** reads the average of 10 raw values with `get_value(10)`. The tare offset is already subtracted. It sets `calibration_factor = raw / N`.
  - **Anything else:** parsed as a float and used as the calibration factor.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DOUT` | `3` | HX711 data pin |
| `CLK` | `2` | HX711 clock pin |
| `calibration_factor` | `0` | Starting scale factor. It is replaced when you run a calibration. |

## Notes and Troubleshooting

- **Initial readings show `inf` or `nan`:** The calibration factor starts at `0`, and the library divides by it. This is expected. It resolves after you send a `weight` command or enter a factor.
- **The weight cannot be 0:** Sending `weight0`, or `weight` followed by non-numeric text, causes a divide-by-zero. The factor becomes `inf` or `nan`. Send a valid `weight<N>` or number to recover.
- **Put the weight on first:** The estimate uses the raw reading at the moment you send the command. Make sure the weight is on the scale and stable.
- **Tare with an empty scale:** Run `tare` before placing the weight, not after.
- **Non-numeric input:** Any text that isn't `tare` or doesn't contain `weight` is parsed with `toFloat()`. Non-numeric input becomes `0`, which sets the factor to 0.
- **Input length:** The startup message says values must be 2+ digits, but the code doesn't enforce this.
- **Match for "weight":** The sketch looks for `weight` anywhere in the input and reads the number that follows it.
- **Line endings:** If the Serial Monitor is set to "No line ending", `Serial.readString()` waits for its timeout (about 1 second) before returning. Using Newline avoids this.
- **Units:** The sketch labels readings as grams. The real unit depends on the reference weight you calibrate with.
- **Sign of the factor:** The sign depends on load cell orientation and wiring. If readings go negative as you add weight, flip the sign of the factor.
- **Drift or unstable readings:** Let the HX711 warm up for a few minutes. Keep wiring short, use a stable power supply, and place the scale on a rigid, level surface.
- **Accuracy:** For best results, use a reference weight near the range you plan to measure. Use the automatic estimate as a starting point, then fine-tune manually.
- **Zero factor:** In a permanent project, you can pass the printed zero factor to `scale.set_offset()` instead of calling `tare()` on every boot.

## Acknowledgments

- Built on the [HX711 Arduino Library](https://github.com/bogde/HX711) by bogde
- Based on the common SparkFun HX711 calibration example