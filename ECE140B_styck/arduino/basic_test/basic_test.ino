#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

const int FSR_PIN = 34;  // FSR connected to GPIO34 (ADC)
const int LED_PIN = 18;  // LED connected to GPIO21 (now controlled by the button)
const int ALERT_LED_PIN = 4;  // Alert LED connected to GPIO4
const int BUTTON_PIN = 19;  // Button connected to GPIO19
const int MOTOR_PIN = 26;  // Motor connected to GPIO26

void setup() {
//  Serial.begin(115200);
//  delay(500);
  pinMode(LED_PIN, OUTPUT);
  pinMode(ALERT_LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP); // Enables internal pull-up resistor for button
//  Wire.begin(23, 22);
//  mpu.initialize();
//  if (mpu.testConnection()) {
//    Serial.println("MPU6050 connected!");
//  } else {
//    Serial.println("MPU6050 connection failed!");
//  }
}

void loop() {
//  int16_t ax, ay, az;
//  mpu.getAcceleration(&ax, &ay, &az);
//  Serial.print("aX = "); Serial.print(ax);
//  Serial.print(" | aY = "); Serial.print(ay);
//  Serial.print(" | aZ = "); Serial.println(az);
//  delay(500);

  // LED controlled by the button
  if (digitalRead(BUTTON_PIN) == LOW) {  // Button is pressed
    digitalWrite(LED_PIN, HIGH);
  } else {  // Button is released
    digitalWrite(LED_PIN, LOW);
  }

  // Keep the alert LED blinking
  digitalWrite(ALERT_LED_PIN, LOW);
  delay(500);
  digitalWrite(ALERT_LED_PIN, HIGH);
  delay(500);
}
