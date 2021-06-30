# tycho
Personal project showing transits of celestial bodies for a given latitude on a RBG LED ring (neopixel). Data fetched monthly for each celestial bodies and each LED from NASA's [JPL HORIZONS project](https://ssd.jpl.nasa.gov/horizons.cgi). ISS position fetched every minute from http://api.open-notify.org/iss-now.json.

![Ring](img/Ring.jpg?raw=true "Ring")

## Quick start
Tycho can run in console mode if you don't have a Neopixel ring.

Open `userSettings.json`.
- Enter desired longitude and latitude (default 0, 0)
- Enter number of leds of your device (up to 360, default 60)
- For each celestial body, pick scope 
  - 0 = not shown
  - 1 = light up on transit ('noon') only
  - 2 = light up from rise to set with maximum brightness on transit
- For each celestial body, pick a RBG color (0 to 255)
- Enter brightness (0 to 100, default 25)
- Chose pole (north or sougth, default north)
  - Determines if the lights go clockwise or counter clockwise
- Enter refresh rate in seconds 
  - Rate at which lights are refreshed and ISS data is fetched, minimum 10, default 60
- Enter MQTT parameters (required for neopixel, but not for console mode)
  - IP address and port (default port 1883)
  - MQTT topics (default tycho/60 and tycho/json/60)

Install required python packages `pip3 install -r requirements.txt`

Run `python3 mainTycho.py`


![Console](img/console.png?raw=true "Console")

## How to build w/ neopixel ring
### Material
- Raspberry pi (or any computer)
- Neopixel ring (or ws2812b ring)
- Microcontroller w/ wifi (I tested with esp8266 and esp32s2)
- 1000μF capacitor
- 440Ω resistor
- 5V-3.3V bidirectionnal logic Level shifter
- 5V, 5A Power supply (as explained in [Adafruit's Neopixel Überguide](https://learn.adafruit.com/adafruit-neopixel-uberguide/powering-neopixels)

### Set up a MQTT broker
You can [install mosquitto](https://randomnerdtutorials.com/how-to-install-mosquitto-broker-on-raspberry-pi/) and start a mosquitto broker on the Raspberry pi that runs the main script.

### Run main script on the Raspberry pi
Follow Quick Start instructions

### Neopixel ring
- Setup ring with controller :

![Circuit](img/circuit.png?raw=true "circuit")

[Here](img/circuitPhoto.jpg) is a little protoboard I build with my limited skills.

- Open [sketch](sketch_LedRing/sketchLedRing.ino).
  - Set number of leds in the device (LED_COUNT)
  - Set IP address (MQTT_BROKER), port (MQTT_PORT) and topic (MQTT_TOPIC) of the MQTT broker
  - Validate pixel type flags are comptatible with your neopixel ring (default NEO_GRB + NEO_KHZ800)
- Create new file sketch_LedRing/wifiParams.h as detailed in [sketch](sketch_LedRing/sketchLedRing.ino) to set :
  - SSID
  - Password,
- Flash to microcontroller (I use Arduino IDE)

The first LED corresponds to the longitude provided by the user
