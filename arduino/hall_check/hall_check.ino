// Simplest hall sensor test. Signal wire on A0 (same as arm.ino).
// Open Serial Monitor at 9600. Prints "MAGNET" or "nothing" 5 times a second,
// plus the raw reading (0-1023) so you can see if the sensor reacts at all.
// The Arduino's built-in light (pin 13) also turns on when it feels a magnet.

const int HALL_PIN = A0;

void setup() {
  Serial.begin(9600);
  pinMode(HALL_PIN, INPUT_PULLUP);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  bool magnet = digitalRead(HALL_PIN) == LOW;
  digitalWrite(LED_BUILTIN, magnet ? HIGH : LOW);
  Serial.print(magnet ? "MAGNET   " : "nothing  ");
  Serial.println(analogRead(HALL_PIN));
  delay(200);
}
