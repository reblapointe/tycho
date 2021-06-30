# tycho
Personal project showing transits of celestial bodies for a given latitude on a RBG LED ring (neopixel). Data fetched daily for each celestial bodies and each LED from NASA's [JPL HORIZONS project](https://ssd.jpl.nasa.gov/horizons.cgi). ISS position fetched every minute from http://api.open-notify.org/iss-now.json.

## Material

- Neopixel ring (or ws2812b ring)
- microcontroller w/ wifi (esp8266, esp32, or esp32s2)
- raspberry pi 
- 1000μF capacitor
- 440Ω resistor
- 5V-3.3V bidirectionnal logic Level Shifter
- 5V, 5A Power supply

## Quick start
### Mosquitto broker
Start a mosquitto server. You can [install mosquitto](https://randomnerdtutorials.com/how-to-install-mosquitto-broker-on-raspberry-pi/) and start a mosquitto broker on the pi.

### Pi
Open `userSettings.json`.
- enter longitude, latitude of your position
- enter number of leds in your device (up to 360)
- enter mqtt broker ip adress and port (required for neopixel, but not for console mode)
- enter brightness (0 to 100)
- chose pole (north or south, default north. Determines if the lights go clockwise or counter clockwise)
- enter refresh rate in seconds (rate at which lights are refreshed and ISS data is fetched, minimum 10)
- for each celestial body, pick scope (0 = not visible, 1 = show transit position only, 2 = show from rise to set)
- for each celestial body, pick a RBG color

Install required python packages
`pip3 install -r requirements.txt`

Run `python3 main.py`


### Neopixel ring
- setup ring with controller as shown in circuit.png.
- set SSID, password, ip address and port of the mqtt btoker in sketch_LedRing/wifiParams.h
- flash to microcontroller

The first LED corresponds to the longitude provided by the user
