#include <WiFi.h>
#include <WebSocketsClient.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// WebSocket server details
const char* websocket_server = "YOUR_SERVER_IP";
const int websocket_port = 8000;

// Pin definitions
const int switchPin = 2;  // Digital pin for the switch
const int ledPin = LED_BUILTIN;  // Built-in LED for status indication

// Variables
bool lastSwitchState = false;
bool currentSwitchState = false;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

WebSocketsClient webSocket;

void setup() {
    Serial.begin(115200);
    
    // Initialize pins
    pinMode(switchPin, INPUT_PULLUP);
    pinMode(ledPin, OUTPUT);
    
    // Connect to WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("Connected to WiFi");
    
    // Connect to WebSocket server
    webSocket.begin(websocket_server, websocket_port, "/ws");
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(5000);
}

void loop() {
    webSocket.loop();
    
    // Read the switch state
    int reading = digitalRead(switchPin);
    
    // Debounce the switch
    if (reading != lastSwitchState) {
        lastDebounceTime = millis();
    }
    
    if ((millis() - lastDebounceTime) > debounceDelay) {
        if (reading != currentSwitchState) {
            currentSwitchState = reading;
            
            // Send status update to server
            if (currentSwitchState == LOW) {  // Switch is ON
                webSocket.sendTXT("{\"type\":\"status\",\"value\":true}");
                digitalWrite(ledPin, HIGH);
            } else {  // Switch is OFF
                webSocket.sendTXT("{\"type\":\"status\",\"value\":false}");
                digitalWrite(ledPin, LOW);
            }
        }
    }
    
    lastSwitchState = reading;
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
    switch(type) {
        case WStype_DISCONNECTED:
            Serial.println("WebSocket Disconnected!");
            break;
        case WStype_CONNECTED:
            Serial.println("WebSocket Connected!");
            break;
        case WStype_TEXT:
            Serial.printf("Received text: %s\n", payload);
            break;
    }
} 