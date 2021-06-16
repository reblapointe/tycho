#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_NeoPixel.h>
#include <ArduinoJson.h>
#include <string>

#define LED_COUNT 60
#define LED_PIN 3
#define REFRESH_RATE 1000



Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

const char* ssid = "SSID***";
const char* password =  "****";
const char* mqttServer = "192.168.1.133";
const int mqttPort = 1883;

struct body{
  const char* bname;
  int r, g, b;
  int scope;
  int led[LED_COUNT];
};

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

DynamicJsonDocument doc(20000);

body* bodies;
int nbBodies;

int elapsed = 0;

void parseJsonBodies()
{
  //JsonArray bodiesJson = doc[0];
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

/*
 * nbBodies
 * Chaque corps a une couleur (rgb),
 * une portée 0 (ignorer) 1 (transit seulement) 2 (visibilité et transit)
 * un tableau de 60 cases avec 0 (non visible) 1 (visible) 2 (transit/midi)
 * une visibilité 0 (montrer tout le temps) 1 (alterner/scintiller)
 * 
 */

WiFiClient espClient;
PubSubClient client(espClient);
 
void setup() {
  Serial.begin(9600);

  strip.begin();           // INITIALIZE NeoPixel strip object (REQUIRED)
  strip.show();            // Turn OFF all pixels ASAP
  strip.setBrightness(25); // Set BRIGHTNESS to about 1/5 (max = 255)

 
  WiFi.begin(ssid, password);
 
  while (WiFi.status() != WL_CONNECTED) 
  {
    delay(500);
    Serial.println("Connecting to WiFi..");
  }
  Serial.println("Connected to the WiFi network");
  
  strip.setPixelColor(0, strip.Color(255, 255, 255));
  strip.show();

  client.setBufferSize(20000);
  client.setServer(mqttServer, mqttPort);
  client.setCallback(callback);
 
  while (!client.connected()) 
  {
    Serial.println("Connecting to MQTT...");
 
    if (client.connect("ESP32s2Client")) 
    {
      Serial.println("connected");  
    } 
    else 
    {
      Serial.print("failed with state ");
      Serial.print(client.state());
      delay(2000);
    }
  }

  client.subscribe("tycho/60"); 
  client.setCallback(callback);
  
  strip.setPixelColor(1, strip.Color(255, 255, 255));
  strip.show();
}

void callback(char* topic, byte* payload, unsigned int length) {
 
  Serial.print("Message arrived in topic: ");
  Serial.println(topic);
 
//  Serial.print("Message:");
//  for (int i = 0; i < length; i++) {
//    Serial.print((char)payload[i]);
//  }
 
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
    if (WiFi.status() != WL_CONNECTED)
    {
      Serial.println("Reconnecting to Wifi...");
      WiFi.disconnect();
      WiFi.reconnect();  
    }
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
