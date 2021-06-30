#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_NeoPixel.h>
#include <string>

#include "wifiParams.h"
/* wifiParams defines SSID, PASSWORD, MQTT_SERVER, MQTT_PORT, TOPIC and
 * LED_COUNT : 
 *  #ifndef WIFI_PARAMS_H
 *  #define WIFI_PARAMS_H
 *  
 *  #define SSID "Your ssid"
 *  #define PASSWORD "Your wifi password"
 *  #define MQTT_SEVER "192.168.1.133" 
 *  #define MQTT_PORT 1883
 *  #define TOPIC "tycho/60"
 *  #define LED_COUNT 60
 *  #endif
*/

/*
 * Des fois serial chie. il faut s'assurer d'avoir python3 et non python2
 * sudo apt install python-is-python3
 * sudo apt-mark hold python2 python2-minimal python2.7 python2.7-minimal libpython2-stdlib libpython2.7-minimal libpython2.7-stdlib 
 *
 * https://github.com/espressif/arduino-esp32
 * If you want to test ESP32-S2 and/or ESP32-C3 through the board manager, please use the development release link: https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_dev_index.json and install the latest 2.0.0 version.
*/

#define LED_PIN 3
#define REFRESH_RATE 1000
#define MAX_MQTT_MESSAGE_LENGTH 20000

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
WiFiClient espClient;
PubSubClient client(espClient);

void connectToWifi()
{  
  WiFi.begin(SSID, PASSWORD);
  int nbTries = 0;
  while (WiFi.status() != WL_CONNECTED) 
  {
    delay(1000);
    if (++nbTries == 10)
    {
      Serial.println("Restarting ESP");
      ESP.restart();    
    }
  }
  Serial.println("Connected to the WiFi network");
}

void checkWifi()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("Lost Wifi connection. Restarting ESP....");
    ESP.restart();
  }
}

void connectToMQTT()
{
  client.setBufferSize(MAX_MQTT_MESSAGE_LENGTH);
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setKeepAlive(3600);
 
  while (!client.connected()) 
  {
    Serial.println("Connecting to MQTT..."); 
    if (client.connect("ESP32s2Client")) 
      Serial.println("connected");  
    else 
    {
      Serial.print("failed with state ");
      Serial.print(client.state());
      delay(2000);
    }
  }
  client.subscribe(TOPIC); 
  client.setCallback(callbackNewMQTTMessage);
}

void callbackNewMQTTMessage(char* topic, byte* payload, unsigned int length) 
{
  Serial.print("Message arrived in topic: ");
  Serial.println(topic);
  Serial.println();
  Serial.println("-----------------------");
  Serial.println((char*)payload);


  char* c = strtok((char*)payload, " ");
  int rgb = 0;
  int r = 0, g = 0, b = 0, i = 0;
  while(c != 0 && i < strip.numPixels())
  {
    if (rgb == 0)
    {
      r = atoi(c);
    }
    else if (rgb == 1)
    {
      g = atoi(c);
    }
    else
    {
      b = atoi(c);
/*      Serial.print(i);
      Serial.print(" r");
      Serial.print(r);
      Serial.print(" g");
      Serial.print(g);
      Serial.print(" b");
      Serial.print(b);
      Serial.println();*/
      strip.setPixelColor(i++, r, g, b);
    }
    rgb = (rgb + 1) % 3;
    c = strtok(0, " ");
  }
  strip.show();
}

void setup() 
{
  Serial.begin(9600);

  strip.begin();           // INITIALIZE NeoPixel strip object (REQUIRED)
  strip.setBrightness(255); // Set BRIGHTNESS to about 1/5 (max = 255)
  
  strip.setPixelColor(0, strip.Color(25, 25, 25));
  strip.show(); 

  connectToWifi(); 
  strip.setPixelColor(1, strip.Color(25, 25, 25));
  strip.show();

  connectToMQTT();
  strip.setPixelColor(2, strip.Color(25, 25, 25));
  strip.show();
}

int elapsed = 0;

void loop() 
{
  client.loop(); // MQTT

  if (millis() - elapsed > REFRESH_RATE)
  {
    elapsed = millis();
    checkWifi();
  }
}
