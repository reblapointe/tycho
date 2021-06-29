#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_NeoPixel.h>
#include <ArduinoJson.h>
#include <string>

#include "wifiParams.h"
/* wifiParams defines SSID, PASSWORD, MQTT_SERVER and MQTT_PORT
 *  #ifndef WIFI_PARAMS_H
 *  #define WIFI_PARAMS_H
 *  
 *  #define SSID "Your ssid"
 *  #define PASSWORD "Your wifi password"
 *  #define MQTT_SEVER "192.168.1.133" 
 *  #define MQTT_PORT 1883
 *  
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

#define LED_COUNT 60
#define LED_PIN 3
#define REFRESH_RATE 1000
#define TOPIC "tycho/60" // MQTT Topic
#define MAX_MQTT_MESSAGE_LENGTH 20000

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
WiFiClient espClient;
PubSubClient client(espClient);

struct Body{
  const char* bname;
  int r, g, b;
  int scope;
  int led[LED_COUNT];
};

struct BodiesList{
  Body* bodies;
  int nbBodies;
};

BodiesList constructBodiesList(int nbBodies)
{
  BodiesList list;
  list.nbBodies = nbBodies;
  list.bodies = new Body[list.nbBodies];
  return list;
}

void destructBodiesList(BodiesList list)
{
  delete[] list.bodies;
}

void printBody(Body b){
  Serial.print(b.bname);
  Serial.print(" R");
  Serial.print(b.r);
  Serial.print(" G");
  Serial.print(b.g);
  Serial.print(" B");
  Serial.print(b.b);
  Serial.print(" Scope ");
  Serial.print(b.scope);
  Serial.println();
  for (int i = 0 ; i < LED_COUNT; i++){
    Serial.print(b.led[i]);
    Serial.print(' ');
  }
  Serial.println();
}   

void showBodiesOnPixelStrip(BodiesList list)
{  
  for(int i = 0; i < LED_COUNT; i++) 
  {
    int r = 0, g = 0, b = 0;
    for (int body = 0; body < list.nbBodies; body++)
    {
      if (list.bodies[body].scope == 2 && list.bodies[body].led[i] == 1)
      {
        r += (list.bodies[body].r / 5) % 256;
        g += (list.bodies[body].g / 5) % 256;
        b += (list.bodies[body].b / 5) % 256;
      }
    }

    for (int body = 0; body < list.nbBodies; body++)
    {
      if (list.bodies[body].led[i] == 2)
      {
         r = list.bodies[body].r; 
         g = list.bodies[body].g;
         b = list.bodies[body].b;
      }
    }
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
}

void loadBodies(BodiesList list, DynamicJsonDocument doc)
{
  for(int i = 0; i < list.nbBodies; i++)
  {
    JsonObject o = doc[i];
    list.bodies[i].bname = o["name"];
    list.bodies[i].r = o["r"]; 
    list.bodies[i].g = o["g"]; 
    list.bodies[i].b = o["b"]; 
    list.bodies[i].scope = o["scope"]; 
    JsonObject ledsJson = o["led"];
    
    for (int j = 0; j < LED_COUNT; j++) 
      list.bodies[i].led[j] = ledsJson[std::to_string(j)];
    printBody(list.bodies[i]);
  }
}

void connectToWifi()
{  
  WiFi.begin(SSID, PASSWORD);
  int nbTries = 0;
  while (WiFi.status() != WL_CONNECTED) 
  {
    delay(1000);
    Serial.println("Connecting to WiFi..");
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

  DynamicJsonDocument doc(MAX_MQTT_MESSAGE_LENGTH);
  DeserializationError error = deserializeJson(doc, payload);
  if (error)
  {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
  }
  else
  {
    BodiesList l = constructBodiesList(doc.size());
    loadBodies(l, doc);
    showBodiesOnPixelStrip(l);
    destructBodiesList(l);
  }
}

void setup() 
{
  Serial.begin(9600);

  strip.begin();           // INITIALIZE NeoPixel strip object (REQUIRED)
  strip.setBrightness(25); // Set BRIGHTNESS to about 1/5 (max = 255)
  
  strip.setPixelColor(0, strip.Color(255, 255, 255));
  strip.show(); 

  connectToWifi(); 
  strip.setPixelColor(1, strip.Color(255, 255, 255));
  strip.show();

  connectToMQTT();
  strip.setPixelColor(2, strip.Color(255, 255, 255));
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
