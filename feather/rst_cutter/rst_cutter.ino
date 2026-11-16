// AI-assisted: drafted with Claude, checked by the author.
// RST cutter for the Nano 33 BLE. Feather M0 pin A1 only ever pulls the
// Nano's RST low or lets it go. It never drives the pin up.
// Commands, one per line at 115200 baud: PING, RESET, BOOTLOADER, CUT <us>

const int RST_PIN = A1;
const unsigned long PULSE_MS = 20;
const unsigned long TAP_GAP_MS = 150;

void rstRelease() {
  pinMode(RST_PIN, INPUT);
}

void rstPulse() {
  digitalWrite(RST_PIN, LOW);
  pinMode(RST_PIN, OUTPUT);
  delay(PULSE_MS);
  rstRelease();
}

void setup() {
  Serial.begin(115200);
  rstRelease();
}

void loop() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line == "PING") {
    Serial.println("PONG");
  } else if (line == "RESET") {
    rstPulse();
    Serial.println("OK");
  } else if (line == "BOOTLOADER") {
    rstPulse();
    delay(TAP_GAP_MS);
    rstPulse();
    Serial.println("OK");
  } else if (line.startsWith("CUT ")) {
    unsigned long us = line.substring(4).toInt();
    rstPulse();  // boot starts when this pulse ends
    unsigned long t0 = micros();
    while (micros() - t0 < us) { }
    rstPulse();  // the power cut
    Serial.println("OK");
  } else {
    Serial.println("ERR");
  }
}
