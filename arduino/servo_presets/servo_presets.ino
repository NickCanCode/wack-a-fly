// Two servos moving through preset positions.
// Each preset = {base angle, arm angle}. Edit the numbers to whatever you want (0-180).

#include <Servo.h>

Servo base;   // pin 11: turns around
Servo arm;    // pin 12: up and down

int presets[][2] = {
  {0,   90},
  {45,  90},
  {90,  90},
  {135, 90},
  {180, 90},
};

int count = sizeof(presets) / sizeof(presets[0]);

void setup() {
  base.attach(9);
  arm.attach(10);
}

void loop() {
  for (int i = 0; i < count; i++) {
    base.write(presets[i][0]);
    arm.write(presets[i][1]);
    delay(1000);   // wait 1 second at each preset
  }
}
