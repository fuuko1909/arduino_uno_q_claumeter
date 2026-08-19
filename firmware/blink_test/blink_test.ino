// Minimal Arduino UNO Q (STM32U585) blink + serial test.
// Build: arduino-cli compile -b arduino:zephyr:unoq -p .
// Flash:  arduino-cli upload -b arduino:zephyr:unoq -p /dev/ttyACMx

#define LED_PIN LED_BUILTIN

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 2000) { }
  Serial.println("Hello from UNO Q MCU");

  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  Serial.println("LED ON");
  delay(500);
  digitalWrite(LED_PIN, LOW);
  Serial.println("LED OFF");
  delay(500);
}
