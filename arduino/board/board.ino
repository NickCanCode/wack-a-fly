// Game board Arduino: 9 LEDs, one per hole.
//
// Commands from the computer (9600 baud):
//   '0'-'8'   light that hole's LED (others off)
//   'x'       all LEDs off

int leds[9] = {2, 3, 4, 5, 6, 7, 8, 9, 10};

void ledsOff() {
  for (int i = 0; i < 9; i++) {
    digitalWrite(leds[i], LOW);
  }
}

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 9; i++) {
    pinMode(leds[i], OUTPUT);
  }
}

void loop() {
  if (!Serial.available()) {
    return;
  }
  char c = Serial.read();

  if (c >= '0' && c <= '8') {
    ledsOff();
    digitalWrite(leds[c - '0'], HIGH);
  } else if (c == 'x') {
    ledsOff();
  }
  // anything else (newlines) is ignored
}
