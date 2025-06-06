#include <WiFi.h>  // For ESP32
#include <WebSocketsClient.h>
#include <Wire.h>
#include <MPU6050.h>

const int FSR_PIN = 34;  // FSR connected to GPIO34 (ADC)
const int LED_PIN = 18;  // LED connected to GPIO21
const int ALERT_LED_PIN = 4;  // Alert LED connected to GPIO4
const int BUTTON_PIN = 19;  // Button connected to GPIO19
const int MOTOR_PIN = 26;    // Motor connected to GPIO26

const float MAX_FORCE_KG = 30.0;  // Max force (30kg)
const float MAX_ADC_VALUE = 4095.0; // ESP32 ADC max reading
const float CALIBRATION_FACTOR = (MAX_FORCE_KG * 1000) / MAX_ADC_VALUE; // grams per ADC unit
const float FORCE_THRESHOLD = MAX_FORCE_KG * 1000; // in grams

#define USER_WEIGHT_KG 70.0  // Set to your user's weight for overreliance/shuffling

bool systemActive = false;  // Tracks system state
WebSocketsClient webSocketClient;
MPU6050 mpu; // Comment out MPU6050 object

static float stepPeakForce = 0;
static float prevStrideTime = 0;
static float prevStepPeakForce = 0;
static float stepDurations[5] = {0}; // For rhythm variance
static int stepDurIdx = 0;
static float axBuffer[20], ayBuffer[20], azBuffer[20]; // For tremor detection
static int imuBufIdx = 0;

// WebSocket event handler
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
    switch(type) {
        case WStype_DISCONNECTED:
            Serial.println("WebSocket disconnected");
            break;
        case WStype_CONNECTED:
            Serial.println("WebSocket connected");
            // Example: Send a message to server on connection
            // webSocketClient.sendTXT("ESP32 Connected");
            break;
        case WStype_TEXT:
            Serial.printf("Received text: %s\n", payload);
            // Check for system status update from server
            if (strstr((char *)payload, "\"type\":\"set_system_status\"")) {
                // Basic parsing, assumes payload is like: {"type":"set_system_status", "active":true}
                if (strstr((char *)payload, "\"active\":true")) {
                    systemActive = true;
                    Serial.println("System activated by server.");
                } else if (strstr((char *)payload, "\"active\":false")) {
                    systemActive = false;
                    Serial.println("System deactivated by server.");
                }
            }
            break;
        case WStype_ERROR:
            Serial.println("WebSocket error");
            break;
        case WStype_BIN:
            Serial.println("WebSocket binary data received");
            break;
        case WStype_PING:
            Serial.println("WebSocket ping");
            break;
        case WStype_PONG:
            Serial.println("WebSocket pong");
            break;
    }
}

unsigned long lastStepTime = 0;
float lastAccelZ = 0;
int stepCount = 0;
float stepLength = 0; // Placeholder, see below for calculation

void sendDeviceStatus(bool status, int userId) {
  String jsonData = "{\"type\":\"device_status\",\"status\":";
  jsonData += status ? "true" : "false";
  jsonData += ",\"user_id\":";
  jsonData += userId;
  jsonData += "}";
  webSocketClient.sendTXT(jsonData);
  Serial.println("Sent device_status: " + jsonData);
}

void blinkAlertLED() {
  for(int i = 0; i < 3; i++) {  // Blink 3 times
    digitalWrite(ALERT_LED_PIN, HIGH);
    delay(200);
    digitalWrite(ALERT_LED_PIN, LOW);
    delay(200);
  }
}

// WiFi and WebSocket Configuration
const char* WIFI_SSID = "your_wifi_ssid";  // Change this to your WiFi name
const char* WIFI_PASSWORD = "your_wifi_password";  // Change this to your WiFi password
const char* WS_SERVER = "your_computer_ip";  // Change this to your computer's IP address
const int WS_PORT = 8000;  // This should match your backend server port

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(ALERT_LED_PIN, OUTPUT);  // Initialize alert LED pin
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(MOTOR_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(ALERT_LED_PIN, LOW);
  digitalWrite(MOTOR_PIN, LOW);

  Serial.begin(115200);
  delay(200); // Give time for Serial to start
  Serial.println(" Booting…");

  Wire.begin(21, 22);  // SDA on GPIO 21, SCL on GPIO 22
  delay(50);
  Serial.println(" I2C up on 21/22");

  mpu.initialize();
  mpu.setSleepEnabled(false);  // make sure it's not in sleep mode
  delay(100);                  // let the registers settle
  Serial.println(" Skipping WHO_AM_I. If accel/gyro data works, you're good.");

  // Wi-Fi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("📶 Joining Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(500);
  }
  Serial.println("\n📶 Connected, IP=" + WiFi.localIP().toString());
  Serial.println("\nConnected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // WebSocket last
  Serial.println("Connecting to WebSocket server...");
  webSocketClient.begin(WS_SERVER, WS_PORT, "/ws");
  webSocketClient.onEvent(webSocketEvent);
  webSocketClient.setReconnectInterval(5000);
  Serial.println("WebSocket client initialized");

  digitalWrite(LED_PIN, HIGH);
  delay(1000);
  digitalWrite(LED_PIN, LOW);
}

void loop() {
  int16_t ax, ay, az;
  mpu.getAcceleration(&ax, &ay, &az);
  Serial.printf("Raw IMU: ax=%d, ay=%d, az=%d\n", ax, ay, az);
  float accelZ = az / 16384.0;
  Serial.printf("accelZ: %.2f\n", accelZ);
  
  webSocketClient.loop();
  
  // Read button state (LOW when pressed)
  if (digitalRead(BUTTON_PIN) == LOW) {
    systemActive = !systemActive;  // Toggle system state
    sendDeviceStatus(systemActive, 2);
    delay(300); // Debounce delay
  }

  if (systemActive) {
    digitalWrite(LED_PIN, HIGH); // LED ON

    int fsrValue = analogRead(FSR_PIN); // Read FSR
    float force = fsrValue * CALIBRATION_FACTOR;  // Convert to grams

    Serial.printf("FSR: %d | Force: %.2f g\n", fsrValue, force);

    // Motor vibration on max force
    if (force >= FORCE_THRESHOLD) {
      digitalWrite(MOTOR_PIN, HIGH);
      blinkAlertLED();  // Blink alert LED when force threshold is exceeded
    } else {
      digitalWrite(MOTOR_PIN, LOW);
    }

    // Step detection (simple peak detection)
    static bool inStep = false;
    static float strideTime = 0; // Move strideTime to static for scope
    if (!inStep && force > 500) {
      Serial.println("[DEBUG] Step condition met (force only)!");
      inStep = true;
      stepCount++;
      unsigned long now = millis();
      strideTime = (now - lastStepTime) / 1000.0; // seconds
      lastStepTime = now;

      // Estimate step length (critical: this is a rough estimate, for real use, calibrate with user height or use IMU integration)
      stepLength = 0.5 * strideTime; // Placeholder: 0.5 m/s walking speed
      float gaitSpeed = stepLength / strideTime; // Calculate gait speed in m/s
      Serial.printf("Step detected! Step count: %d, Gait speed: %.2f m/s\n", stepCount, gaitSpeed);

      // Send step JSON only when a step is detected
      String stepJson = "{\"type\":\"step\",\"peak_force\":" + String(stepPeakForce/1000.0, 2) +
                        ",\"gait_speed\":" + String(gaitSpeed, 2) +
                        ",\"timestamp\":" + String(now) +
                        ",\"user_id\":2}";
      Serial.println(stepJson);
      webSocketClient.sendTXT(stepJson);
      stepPeakForce = 0; // Reset for next step

      // Store current stride time for rhythm analysis
      stepDurations[stepDurIdx++ % 5] = strideTime;

      // Store IMU data for tremor analysis
      axBuffer[imuBufIdx % 20] = ax / 16384.0;
      ayBuffer[imuBufIdx % 20] = ay / 16384.0;
      azBuffer[imuBufIdx % 20] = az / 16384.0;
      imuBufIdx++;

      // ---- POSTURE ANOMALY CHECKS: ONLY HERE ----
      // All anomaly checks and alert sending go here!
      // (as in your latest code, but only in this block)
      // -------------------------------------------

      // 1. Overreliance (high force)
      if (stepPeakForce/1000.0 > 0.3 * USER_WEIGHT_KG) {
        String alertJson = "{\"type\":\"posture_alert\",\"anomaly\":\"overreliance\",\"value\":" + String(stepPeakForce/1000.0, 2) +
                           ",\"timestamp\":" + String(now) + ",\"user_id\":2}";
        webSocketClient.sendTXT(alertJson);
      }

      // 2. Shuffling (low force)
      if (stepPeakForce/1000.0 < 0.1 * USER_WEIGHT_KG) {
        String alertJson = "{\"type\":\"posture_alert\",\"anomaly\":\"shuffling\",\"value\":" + String(stepPeakForce/1000.0, 2) +
                           ",\"timestamp\":" + String(now) + ",\"user_id\":2}";
        webSocketClient.sendTXT(alertJson);
      }

      // 3. Imbalance (high ax/ay variance during step)
      float axMean = 0, ayMean = 0;
      for (int i = 0; i < 20; i++) {
        axMean += axBuffer[i];
        ayMean += ayBuffer[i];
      }
      axMean /= 20; ayMean /= 20;
      float axVar = 0, ayVar = 0;
      for (int i = 0; i < 20; i++) {
        axVar += (axBuffer[i] - axMean) * (axBuffer[i] - axMean);
        ayVar += (ayBuffer[i] - ayMean) * (ayBuffer[i] - ayMean);
      }
      axVar /= 20; ayVar /= 20;
      if (axVar > 0.2 || ayVar > 0.2) { // Tune threshold as needed
        String alertJson = "{\"type\":\"posture_alert\",\"anomaly\":\"imbalance\",\"value\":" + String(max(axVar, ayVar), 2) +
                           ",\"timestamp\":" + String(now) + ",\"user_id\":2}";
        webSocketClient.sendTXT(alertJson);
      }

      // 4. Irregular rhythm (step duration variance)
      float durMean = 0, durVar = 0;
      for (int i = 0; i < 5; i++) durMean += stepDurations[i];
      durMean /= 5;
      for (int i = 0; i < 5; i++) durVar += (stepDurations[i] - durMean) * (stepDurations[i] - durMean);
      durVar /= 5;
      if (durVar > 0.05) { // Tune threshold as needed
        String alertJson = "{\"type\":\"posture_alert\",\"anomaly\":\"irregular_rhythm\",\"value\":" + String(durVar, 2) +
                           ",\"timestamp\":" + String(now) + ",\"user_id\":2}";
        webSocketClient.sendTXT(alertJson);
      }

      // 5. Tremor (high-frequency IMU noise)
      float azMean = 0, azVar = 0;
      for (int i = 0; i < 20; i++) azMean += azBuffer[i];
      azMean /= 20;
      for (int i = 0; i < 20; i++) azVar += (azBuffer[i] - azMean) * (azBuffer[i] - azMean);
      azVar /= 20;
      if (azVar > 0.5) { // Tune threshold as needed
        String alertJson = "{\"type\":\"posture_alert\",\"anomaly\":\"tremor\",\"value\":" + String(azVar, 2) +
                           ",\"timestamp\":" + String(now) + ",\"user_id\":2}";
        webSocketClient.sendTXT(alertJson);
      }

      // 6. Incorrect cane usage (orientation: pitch/roll)
      float pitch = atan2(ax, sqrt(ay*ay + az*az)) * 180.0 / PI;
      float roll = atan2(ay, sqrt(ax*ax + az*az)) * 180.0 / PI;
      if (abs(pitch) > 30 || abs(roll) > 30) {
        String alertJson = "{\"type\":\"posture_alert\",\"anomaly\":\"incorrect_usage\",\"value\":" + String(abs(pitch) > abs(roll) ? pitch : roll, 2) +
                           ",\"timestamp\":" + String(now) + ",\"user_id\":2}";
        webSocketClient.sendTXT(alertJson);
      }
    }
    if (inStep && accelZ - lastAccelZ < 0.2) {
      inStep = false;
    }
    lastAccelZ = accelZ;

    if (force > stepPeakForce) stepPeakForce = force;

    // Create JSON data
    String jsonData = "{\"type\":\"gait\",\"force\":" + String(force) + ",\"user_id\":2}";
    
    // Send data via WebSocket
    if (webSocketClient.isConnected()) {
      webSocketClient.sendTXT(jsonData);
    } else {
      Serial.println("WebSocket not connected, cannot send data");
    }

    Serial.printf("FSR: %d | Force: %.2f g\n", fsrValue, force);
    Serial.printf("[DEBUG] accelZ: %.2f, lastAccelZ: %.2f, diff: %.2f, force: %.2f\n", accelZ, lastAccelZ, accelZ - lastAccelZ, force);

    // Try lower thresholds for testing
    float accelThreshold = 0.15; // Lowered for hand simulation
    float forceThreshold = 300;  // Lowered for hand simulation

    if (!inStep && (accelZ - lastAccelZ > accelThreshold) && (force > forceThreshold)) {
        Serial.println("[DEBUG] Step condition met!");
        // ... rest of step detection code ...
    } else {
        Serial.println("[DEBUG] Step condition NOT met.");
    }
  } else {
    digitalWrite(LED_PIN, LOW); // LED OFF
    digitalWrite(MOTOR_PIN, LOW);
  }

  // Update LED based on systemActive state, regardless of how it was changed
  if (systemActive) {
    digitalWrite(LED_PIN, HIGH);
  } else { 
    digitalWrite(LED_PIN, LOW);
  }

  delay(50); // Update rate
}
