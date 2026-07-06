/*
 * SilentSpeak: 4-channel Grove EMG streamer for ESP32-S3
 *
 * Samples 4 analog channels at SAMPLE_RATE_HZ and outputs CSV:
 *   timestamp_ms,ch0,ch1,ch2,ch3
 *
 * Grove EMG SIG pins -> GPIO 1, 2, 3, 4 (ADC1)
 * Reference electrode on earlobe -> Grove REF/GND
 */

#define USE_WIFI 0

#if USE_WIFI
#include <WiFi.h>
#include <WiFiUdp.h>
const char *WIFI_SSID = "YOUR_SSID";
const char *WIFI_PASS = "YOUR_PASSWORD";
const uint16_t UDP_PORT = 5005;
const char *UDP_HOST = "192.168.1.100";
WiFiUDP udp;
#endif

static const int EMG_PINS[4] = {1, 2, 3, 4};
static const int NUM_CHANNELS = 4;
static const int SAMPLE_RATE_HZ = 1000;
static const int ADC_BITS = 12;
static const int ADC_MAX = 4095;

hw_timer_t *sampleTimer = nullptr;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;

volatile bool sampleReady = false;
uint16_t sampleBuffer[NUM_CHANNELS];

void IRAM_ATTR onSampleTimer() {
  portENTER_CRITICAL_ISR(&timerMux);
  sampleReady = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}

void readAdcChannels() {
  for (int i = 0; i < NUM_CHANNELS; i++) {
    sampleBuffer[i] = analogRead(EMG_PINS[i]);
  }
}

void emitSampleCsv(unsigned long timestampMs) {
  Serial.print(timestampMs);
  for (int i = 0; i < NUM_CHANNELS; i++) {
    Serial.print(',');
    Serial.print(sampleBuffer[i]);
  }
  Serial.println();
}

#if USE_WIFI
void emitSampleUdp(unsigned long timestampMs) {
  char line[64];
  int n = snprintf(line, sizeof(line), "%lu,%u,%u,%u,%u",
                   timestampMs,
                   sampleBuffer[0], sampleBuffer[1],
                   sampleBuffer[2], sampleBuffer[3]);
  udp.beginPacket(UDP_HOST, UDP_PORT);
  udp.write((const uint8_t *)line, n);
  udp.endPacket();
}
#endif

void setupAdc() {
  analogReadResolution(ADC_BITS);
  for (int i = 0; i < NUM_CHANNELS; i++) {
    pinMode(EMG_PINS[i], INPUT);
  }
}

void setupTimer() {
  sampleTimer = timerBegin(1000000);
  timerAttachInterrupt(sampleTimer, &onSampleTimer);
  timerAlarm(sampleTimer, 1000000 / SAMPLE_RATE_HZ, true, 0);
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {
    delay(10);
  }

  setupAdc();
  setupTimer();

#if USE_WIFI
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  udp.begin(UDP_PORT);
  Serial.println("# wifi_connected");
#endif

  Serial.println("# silentspeak_emg_v1");
  Serial.println("# format: timestamp_ms,ch0,ch1,ch2,ch3");
}

void loop() {
  if (!sampleReady) {
    return;
  }

  portENTER_CRITICAL(&timerMux);
  sampleReady = false;
  portEXIT_CRITICAL(&timerMux);

  readAdcChannels();
  unsigned long t = millis();
  emitSampleCsv(t);

#if USE_WIFI
  emitSampleUdp(t);
#endif
}
