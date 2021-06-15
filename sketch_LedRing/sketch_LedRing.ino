#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_NeoPixel.h>
#include <ArduinoJson.h>
#include <string>

#define LED_COUNT 60
#define LED_PIN 3

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

const char* ssid = "SSID";
const char* password =  "PASS";
const char* mqttServer = "192.168.1.*****";
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
  Serial.print(b.b);
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

DynamicJsonDocument doc(6144);

body* bodies;
int nbBodies;

void parseJsonBodies()
{
  //JsonArray bodiesJson = doc[0];
  nbBodies = doc.size();
  bodies = (body*) malloc(nbBodies*sizeof(body));
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

  client.setBufferSize(6144);
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

  char data[] = "[{\"name\": \"Sun\", \"horizonNumber\": 10, \"scope\": 2, \"r\": 255, \"g\": 255, \"b\": 255, \"led\": {\"0\": 0, \"1\": 0, \"2\": 0, \"3\": 0, \"4\": 1, \"5\": 1, \"6\": 1, \"7\": 1, \"8\": 1, \"9\": 1, \"10\": 1, \"11\": 1, \"12\": 1, \"13\": 1, \"14\": 1, \"15\": 1, \"16\": 1, \"17\": 1, \"18\": 1, \"19\": 1, \"20\": 1, \"21\": 1, \"22\": 1, \"23\": 1, \"24\": 2, \"25\": 1, \"26\": 1, \"27\": 1, \"28\": 1, \"29\": 1, \"30\": 1, \"31\": 1, \"32\": 1, \"33\": 1, \"34\": 1, \"35\": 1, \"36\": 1, \"37\": 1, \"38\": 1, \"39\": 1, \"40\": 1, \"41\": 1, \"42\": 1, \"43\": 1, \"44\": 0, \"45\": 0, \"46\": 0, \"47\": 0, \"48\": 0, \"49\": 0, \"50\": 0, \"51\": 0, \"52\": 0, \"53\": 0, \"54\": 0, \"55\": 0, \"56\": 0, \"57\": 0, \"58\": 0, \"59\": 0}}, {\"name\": \"Moon\", \"horizonNumber\": 301, \"scope\": 1, \"r\": 0, \"g\": 0, \"b\": 255, \"led\": {\"0\": 0, \"1\": 0, \"2\": 0, \"3\": 0, \"4\": 0, \"5\": 0, \"6\": 0, \"7\": 0, \"8\": 0, \"9\": 0, \"10\": 0, \"11\": 0, \"12\": 0, \"13\": 0, \"14\": 0, \"15\": 0, \"16\": 0, \"17\": 0, \"18\": 0, \"19\": 0, \"20\": 0, \"21\": 0, \"22\": 0, \"23\": 0, \"24\": 0, \"25\": 0, \"26\": 0, \"27\": 0, \"28\": 0, \"29\": 0, \"30\": 0, \"31\": 0, \"32\": 0, \"33\": 0, \"34\": 0, \"35\": 1, \"36\": 1, \"37\": 1, \"38\": 1, \"39\": 1, \"40\": 1, \"41\": 1, \"42\": 1, \"43\": 1, \"44\": 2, \"45\": 1, \"46\": 1, \"47\": 1, \"48\": 1, \"49\": 1, \"50\": 1, \"51\": 1, \"52\": 1, \"53\": 1, \"54\": 1, \"55\": 0, \"56\": 0, \"57\": 0, \"58\": 0, \"59\": 0}}, {\"name\": \"ISS\", \"apiURL\": \"http://api.open-notify.org/iss-now.json\", \"scope\": 1, \"r\": 0, \"g\": 255, \"b\": 0, \"led\": {\"0\": 0, \"1\": 0, \"2\": 0, \"3\": 0, \"4\": 0, \"5\": 0, \"6\": 0, \"7\": 0, \"8\": 0, \"9\": 0, \"10\": 0, \"11\": 0, \"12\": 0, \"13\": 0, \"14\": 0, \"15\": 0, \"16\": 0, \"17\": 0, \"18\": 0, \"19\": 0, \"20\": 0, \"21\": 0, \"22\": 0, \"23\": 0, \"24\": 0, \"25\": 0, \"26\": 0, \"27\": 0, \"28\": 0, \"29\": 0, \"30\": 0, \"31\": 0, \"32\": 0, \"33\": 0, \"34\": 0, \"35\": 0, \"36\": 0, \"37\": 0, \"38\": 0, \"39\": 0, \"40\": 2, \"41\": 0, \"42\": 0, \"43\": 0, \"44\": 0, \"45\": 0, \"46\": 0, \"47\": 0, \"48\": 0, \"49\": 0, \"50\": 0, \"51\": 0, \"52\": 0, \"53\": 0, \"54\": 0, \"55\": 0, \"56\": 0, \"57\": 0, \"58\": 0, \"59\": 0}}, {\"name\": \"Venus\", \"horizonNumber\": 299, \"scope\": 1, \"r\": 255, \"g\": 255, \"b\": 0, \"led\": {\"0\": 1, \"1\": 1, \"2\": 1, \"3\": 1, \"4\": 1, \"5\": 1, \"6\": 1, \"7\": 1, \"8\": 1, \"9\": 1, \"10\": 1, \"11\": 1, \"12\": 1, \"13\": 1, \"14\": 1, \"15\": 1, \"16\": 1, \"17\": 1, \"18\": 1, \"19\": 1, \"20\": 1, \"21\": 2, \"22\": 1, \"23\": 1, \"24\": 1, \"25\": 1, \"26\": 1, \"27\": 1, \"28\": 1, \"29\": 1, \"30\": 1, \"31\": 1, \"32\": 1, \"33\": 1, \"34\": 1, \"35\": 1, \"36\": 1, \"37\": 1, \"38\": 1, \"39\": 1, \"40\": 1, \"41\": 1, \"42\": 0, \"43\": 0, \"44\": 0, \"45\": 0, \"46\": 0, \"47\": 0, \"48\": 0, \"49\": 0, \"50\": 0, \"51\": 0, \"52\": 0, \"53\": 0, \"54\": 0, \"55\": 0, \"56\": 0, \"57\": 0, \"58\": 0, \"59\": 0}}]";
  deserializeJson(doc, data);
  parseJsonBodies();
 
  client.subscribe("tycho/60"); 
  client.setCallback(callback);
}

void callback(char* topic, byte* payload, unsigned int length) {
 
  Serial.print("Message arrived in topic: ");
  Serial.println(topic);
 
  Serial.print("Message:");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
 
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
    
  for(int i = 0; i < strip.numPixels(); i++) 
  {
    int r = 0, g = 0, b = 0;
    strip.setPixelColor(i, strip.Color(0, 0, 0));
    for (int b = 0; b < nbBodies; b++)
    {
      if (bodies[b].scope == 2 && bodies[b].led[i] == 1)
      {
        strip.setPixelColor(i, strip.Color(bodies[b].r / 10, bodies[b].g / 10, bodies[b].b / 10));
      }
      else if (bodies[b].led[i] == 2)
      {
         strip.setPixelColor(i, strip.Color(0, 0, 0));
         strip.setPixelColor(i, strip.Color(bodies[b].r, bodies[b].g, bodies[b].b));
      }
    }
    /*Serial.print(r);
    Serial.print(g);
    Serial.print(b);
    Serial.println();*/
  }
  
 // strip.setPixelColor(0, strip.Color(255, 0, 255));
  strip.show();
}
