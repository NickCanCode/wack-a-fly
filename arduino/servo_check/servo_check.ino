// Simplest servo test. One servo, signal wire on pin 11.
// A normal servo: goes to 3 spots and STOPS at each one for 2 seconds.
// A continuous (360) servo: spins one way, stops in the middle, spins the other way.

#include <Servo.h>

Servo s;

void setup() {
  s.attach(11);
}

void loop() {
  s.write(45);    // spot 1
  delay(2000);
  s.write(90);    // middle
  delay(2000);
  s.write(135);   // spot 2
  delay(2000);
}
