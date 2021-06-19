#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_NeoPixel.h>
#include <ArduinoJson.h>
#include <string>

#include "wifiParams.h"
/* wifiParams.sets SSID, PASSWORD, MQTT_SERVER and MQTT_PORT
 * #define SSID "Your ssid"
 * #define PASSWORD "Your wifi password"
 * #define MQTT_SEVER "192.168.1.133" 
 * #define MQTT_PORT 1883
*/

#define LED_COUNT 60
#define LED_PIN 3
#define REFRESH_RATE 1000
#define TOPIC "tycho/60" // MQTT Topic
#define MAX_MQTT_MESSAGE_LENGTH 20000

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
DynamicJsonDocument doc(MAX_MQTT_MESSAGE_LENGTH);
WiFiClient espClient;
PubSubClient client(espClient);

int elapsed = 0;

struct body{
  const char* bname;
  int r, g, b;
  int scope;
  int led[LED_COUNT];
};

body* bodies;
int nbBodies;

void printBody(body b){
  Serial.println(b.bname);
  Serial.print("R");
  Serial.print(b.r);
  Serial.print(" G");
  Serial.print(b.g);
  Serial.print(" B");
  Serial.print(b.b);
  Serial.print(" Scope");
  Serial.print(b.scope);
  Serial.println();
  for (int i = 0 ; i < LED_COUNT; i++){
    Serial.print(b.led[i]);
    Serial.print(' ');
  }
  Serial.println();
}   

void parseJsonBodies()
{
  nbBodies = doc.size();
  bodies = (body*) malloc(nbBodies * sizeof(body));
  for(int i = 0; i < nbBodies; i++)
  {
    JsonObject o = doc[i];
    bodies[i].bname = o["name"];
    bodies[i].r = o["r"]; 
    bodies[i].g = o["g"]; 
    bodies[i].b = o["b"]; 
    bodies[i].scope = o["scope"]; 
    JsonObject ledsJson = o["led"];
    
    for (int j = 0; j < LED_COUNT; j++) 
        bodies[i].led[j] = ledsJson[std::to_string(j)];
    printBody(bodies[i]);
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

void checkWifi()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("Lost Wifi connection. Restarting ESP....");
    ESP.restart();
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

void callbackNewMQTTMessage(char* topic, byte* payload, unsigned int length) 
{
  Serial.print("Message arrived in topic: ");
  Serial.println(topic);
  Serial.println();
  Serial.println("-----------------------");

  DeserializationError error = deserializeJson(doc, payload);
  if (error)
  {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
  }
  else
    parseJsonBodies();
}

void loop() {
  client.loop();

  if (millis() - elapsed > REFRESH_RATE)
  {
    elapsed = millis();
    checkWifi();
    
    for(int i = 0; i < strip.numPixels(); i++) 
    {
      int r = 0, g = 0, b = 0;
      for (int body = 0; body < nbBodies; body++)
      {
        if (bodies[body].scope == 2 && bodies[body].led[i] == 1)
        {
          r += (bodies[body].r / 5) % 256;
          g += (bodies[body].g / 5) % 256;
          b += (bodies[body].b / 5) % 256;
        }
      }

      for (int body = 0; body < nbBodies; body++)
      {
        if (bodies[body].led[i] == 2)
        {
           r = bodies[body].r; 
           g = bodies[body].g;
           b = bodies[body].b;
        }
      }
      strip.setPixelColor(i, strip.Color(r, g, b));
    }
    strip.show();
  }
}
