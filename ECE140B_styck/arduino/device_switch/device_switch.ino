#include <WiFi.h>  // For ESP32
#include <WebSocketsClient.h>
#include <Wire.h>
#include <MPU6050.h>

const int FSR_PIN = 34;  // FSR connected to GPIO34 (ADC)
const int LED_PIN = 18;  // LED connected to GPIO21
const int BUTTON_PIN = 19;  // Button connected to GPIO19
const int MOTOR_PIN = 26;    // Motor connected to GPIO26

const float MAX_FORCE_KG = 30.0;  // Max force (30kg)
const float MAX_ADC_VALUE = 4095.0; // ESP32 ADC max reading
const float CALIBRATION_FACTOR = (MAX_FORCE_KG * 1000) / MAX_ADC_VALUE; // grams per ADC unit
const float FORCE_THRESHOLD = MAX_FORCE_KG * 1000; // in grams

bool systemActive = false;  // Tracks system state
WebSocketsClient webSocketClient;
MPU6050 mpu; // Comment out MPU6050 object

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

void setup() {
  
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(MOTOR_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(MOTOR_PIN, LOW);


  Serial.begin(115200);
  delay(200); // Give time for Serial to start
  Serial.println(" Booting…");

  Wire.begin(21, 22);
  delay(50);
  Serial.println(" I2C up on 21/22");


  mpu.initialize();
  mpu.setSleepEnabled(false);  // make sure it's not in sleep mode
  delay(100);                  // let the registers settle
  Serial.println(" Skipping WHO_AM_I. If accel/gyro data works, you're good.");



  // Wi-Fi
  WiFi.begin("ironandfire", "252189200");
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
  webSocketClient.begin("172.20.10.2", 8000, "/ws");
  webSocketClient.onEvent(webSocketEvent);
  webSocketClient.setReconnectInterval(5000);
  Serial.println("WebSocket client initialized");

  digitalWrite(LED_PIN, HIGH);
  delay(1000);
  digitalWrite(LED_PIN, LOW);
}

void loop() {

    // Now test reading once:
  int16_t ax, ay, az;
  mpu.getAcceleration(&ax, &ay, &az);
  Serial.printf("Accel sample: %d, %d, %d\n", ax, ay, az);
  
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
    } else {
      digitalWrite(MOTOR_PIN, LOW);
    }

     //MPU6050 Reading
     int16_t ax, ay, az;
     mpu.getAcceleration(&ax, &ay, &az);
     float accelZ = az / 16384.0; // Convert to g

    // Step detection (simple peak detection)
    static bool inStep = false;
     if (!inStep && accelZ - lastAccelZ > 0.5 && force > 1000) { // threshold and force to confirm stance
       inStep = true;
       stepCount++;
       unsigned long now = millis();
       float strideTime = (now - lastStepTime) / 1000.0; // seconds
       lastStepTime = now;

       // Estimate step length (critical: this is a rough estimate, for real use, calibrate with user height or use IMU integration)
       stepLength = 0.5 * strideTime; // Placeholder: 0.5 m/s walking speed
       Serial.printf("Step detected! Step count: %d, Step length: %.2f m\n", stepCount, stepLength);
     }
     if (inStep && accelZ - lastAccelZ < 0.2) {
       inStep = false;
     }
     lastAccelZ = accelZ;

    // Create JSON data
    String jsonData = "{\"type\":\"gait\",\"force\":" + String(force) + "}";
    
    // Send data via WebSocket
    if (webSocketClient.isConnected()) {
      webSocketClient.sendTXT(jsonData);
    } else {
      Serial.println("WebSocket not connected, cannot send data");
    }

    Serial.printf("FSR: %d | Force: %.2f g\n", fsrValue, force);
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
