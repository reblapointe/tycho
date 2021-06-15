# tycho
Personal project showing transits of celestial bodies for a given latitude on a RBG LED ring (neopixel). Data fetched daily for each celestial bodies and each LED from NASA's [JPL HORIZONS project](https://ssd.jpl.nasa.gov/horizons.cgi). ISS position fetched every minute from http://api.open-notify.org/iss-now.json.

## Quick start
Open `userSettings.json`.
- enter longitude, latitude of your position
- enter number of leds in your device (up to 360)
- for each celestial body, pick visibility (1 = visible)
- for each celestial body, pick a RBG color

To run in console mode :

`python3 tychoConsole.py`


To run in LED mode :

`python3 tychoConsole.py led`

The first LED corresponds to the longitude provided by the user.

## Major TODOs
At the moment, the code can display lights on a 10 segment LED Bargraph. It will be updated soon for a neopixel ring.
