/*
 * Prototipo académico IoT — motor eléctrico monofásico.
 * ESP32 lee temperatura, vibración (MPU6050), corriente (ACS712) y tensión (ZMPT101B)
 * y envía el JSON por Wi-Fi a POST /api/mediciones.
 *
 * Ajuste pines, sensibilidades y calibración según el montaje de laboratorio.
 */
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <math.h>

const char* WIFI_SSID = "TU_SSID";
const char* WIFI_PASS = "TU_PASSWORD";
const char* SERVIDOR  = "http://192.168.1.10:5000/api/mediciones";
const char* API_KEY   = "cambia-esta-clave";

const int PIN_CORRIENTE = 34;   // ACS712 (ADC)
const int PIN_TENSION   = 35;   // ZMPT101B (ADC)
const int PIN_TEMP      = 32;   // analogico / OneWire según sensor

const float ACS712_SENSIBILIDAD = 0.185;  // V/A  (módulo 5 A)
const float ACS712_OFFSET       = 1.65;   // V    (punto medio ~3.3 V / 2)
const float ZMPT_ESCALA         = 225.0;  // calibrar con multímetro
const uint32_t PERIODO_MS       = 1000;

float leerAdcVoltios(int pin) {
  const int n = 64;
  uint32_t acc = 0;
  for (int i = 0; i < n; i++) acc += analogRead(pin);
  return (acc / float(n)) * (3.3f / 4095.0f);
}

float leerCorrienteRms() {
  const int n = 200;
  float acc = 0;
  for (int i = 0; i < n; i++) {
    float v = leerAdcVoltios(PIN_CORRIENTE) - ACS712_OFFSET;
    float a = v / ACS712_SENSIBILIDAD;
    acc += a * a;
    delayMicroseconds(200);
  }
  return sqrtf(acc / n);
}

float leerTensionRms() {
  const int n = 200;
  float acc = 0;
  for (int i = 0; i < n; i++) {
    float v = leerAdcVoltios(PIN_TENSION) - 1.65f;
    acc += v * v;
    delayMicroseconds(200);
  }
  return sqrtf(acc / n) * ZMPT_ESCALA;
}

// Sustituir por DS18B20 / DHT si el laboratorio lo usa.
float leerTemperatura() {
  float v = leerAdcVoltios(PIN_TEMP);
  return 25.0f + (v - 0.5f) * 20.0f;
}

// MPU6050 en I2C (SDA=21, SCL=22). Lectura cruda convertida a g.
bool mpuOk = false;

bool iniciarMpu() {
  Wire.begin(21, 22);
  Wire.beginTransmission(0x68);
  Wire.write(0x6B);
  Wire.write(0);
  return Wire.endTransmission() == 0;
}

bool leerAceleracion(float& ax, float& ay, float& az) {
  Wire.beginTransmission(0x68);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(0x68, 6) != 6) return false;
  int16_t x = (Wire.read() << 8) | Wire.read();
  int16_t y = (Wire.read() << 8) | Wire.read();
  int16_t z = (Wire.read() << 8) | Wire.read();
  ax = x / 16384.0f;
  ay = y / 16384.0f;
  az = z / 16384.0f;
  return true;
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  mpuOk = iniciarMpu();
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(400);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi listo");
}

void loop() {
  float ax = 0, ay = 0, az = 1;
  if (mpuOk) leerAceleracion(ax, ay, az);

  char body[320];
  snprintf(body, sizeof(body),
           "{\"temperatura\":%.2f,\"aceleracion_x\":%.4f,\"aceleracion_y\":%.4f,"
           "\"aceleracion_z\":%.4f,\"corriente\":%.3f,\"tension\":%.2f}",
           leerTemperatura(), ax, ay, az, leerCorrienteRms(), leerTensionRms());

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(SERVIDOR);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-Key", API_KEY);
    int code = http.POST(body);
    Serial.printf("%d %s\n", code, body);
    http.end();
  }
  delay(PERIODO_MS);
}
