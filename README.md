# tycho
Personal project showing transits of celestial bodies for a given latitude on a RBG LED ring (neopixel). Data fetched monthly for each celestial bodies and each LED from NASA's [JPL HORIZONS project](https://ssd.jpl.nasa.gov/horizons.cgi). ISS position fetched every minute from http://api.open-notify.org/iss-now.json.

## Quick start
Tycho can run in console mode if you don't have a Neopixel ring.

Open `userSettings.json`.
- enter desired longitude and latitude (default 0, 0)
- enter number of leds of your device (up to 360, default 60)
- enter mqtt broker ip address and port (required for neopixel, but not for console mode)
- enter brightness (0 to 100, default 25)
- chose pole 
  - north or south, default north. Determines if the lights go clockwise or counter clockwise
- enter refresh rate in seconds 
  - rate at which lights are refreshed and ISS data is fetched, minimum 10, default 60
- for each celestial body, pick scope 
  - 0 = not visible
  - 1 = show transit only
  - 2 = show from rise to set with maximum brightness on transit
- for each celestial body, pick a RBG color (0 to 255)

Install required python packages `pip3 install -r requirements.txt`

Run `python3 mainTycho.py`

## How to build w/ neopixel ring
### Material
- Raspberry pi (or any computer)
- Neopixel ring (or ws2812b ring)
- microcontroller w/ wifi (I tested with esp8266 and esp32s2)
- 1000μF capacitor
- 440Ω resistor
- 5V-3.3V bidirectionnal logic Level shifter
- 5V, 5A Power supply (as explained in [Adafruit's Neopixel Überguide](https://learn.adafruit.com/adafruit-neopixel-uberguide/powering-neopixels)

### Set up a MQTT broker
You can [install mosquitto](https://randomnerdtutorials.com/how-to-install-mosquitto-broker-on-raspberry-pi/) and start a mosquitto broker on the Raspberry pi that runs the main script.

### Run main script on the Raspberry pi
Follow Quick Start instructions

### Neopixel ring
- setup ring with controller as shown in [drawing](circuit.png).
- set SSID, password, ip address and port of the mqtt broker in new file sketch_LedRing/wifiParams.h as detailed in [sketch](sketch_LedRing/sketchLedRing.ino)
- flash to microcontroller (I use Arduino IDE)

The first LED corresponds to the longitude provided by the user
