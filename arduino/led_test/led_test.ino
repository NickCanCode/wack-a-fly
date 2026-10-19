// Wiring test: lights pins 2-10 one at a time, forever. No computer or Python needed.
// Watch the board's "L" light too: it blinks on pin 13 so you know the sketch is running.

int leds[9] = {2, 3, 4, 5, 6, 7, 8, 9, 10};

void setup() {
  pinMode(13, OUTPUT);
  for (int i = 0; i < 9; i++) {
    pinMode(leds[i], OUTPUT);
  }
}

void loop() {
  for (int i = 0; i < 9; i++) {
    digitalWrite(leds[i], HIGH);
    digitalWrite(13, i % 2);
    delay(400);
    digitalWrite(leds[i], LOW);
  }
}
