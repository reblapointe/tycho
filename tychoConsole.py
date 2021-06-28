# install pipenv (for dev environment)
#python3 -m pip install --user pipenv

# install all packages (for dev environment)
#pipenv install requests (....)

# load requirements (before running, on new install, w or w/o pipenv)
#pipenv lock -r > requirements.txt

# Run app no hanup (termine pas même après logout)
# nohup python3 tychoConsole.py

import json, tycho, time, datetime, threading, sys, paho.mqtt.client as paho


#Start broker : mosquitto -d
#View topic :
# (localhost) mosquitto_sub -d -t testTopic
# mosquitto_sub -L 'mqtt://10.0.0.57:1883/tycho/60'

with open('userSettings.json') as f:
    params = json.load(f)

lat = params["latitude"]
lon = params["longitude"]
bodies = params['bodies']
pole = 1 if "standingOnPole" in params and params["standingOnPole"] == "south" else -1
showISS = False
publishToMQTT = False
refreshRate = 60
if 'secondsBetweenRefresh' not in params or params['secondsBetweenRefresh'] < 10 :
    params['secondsBetweenRefresh'] = 60

for b in params["bodies"]:
    if b["scope"] != 0 :
        if 'horizonNumber' not in b.keys() :
            showISS = True
bodies[:] = [b for b in bodies if b['scope'] != 0]

if len(sys.argv) > 1:
    import tychoLEDBarGraph as led
    nbTicks = led.nbTicks # number of leds
else:
    nbTicks = params["nbLeds"]

if 'mqtt_ip' in params :
    publishToMQTT = True
    def on_publish(client, userdata, result):
        print(userdata)
    broker = params["mqtt_ip"]
    if 'mqtt_port' in params :
        port = params["mqtt_port"]
    else :
        port = 1883

    client = paho.Client()
    client.on_publish = on_publish
    client.connect(broker, port, 3600)

def publish(s:str) :
    if publishToMQTT : 
        ret = client.publish('tycho/' + str(nbTicks), s, retain = True)

for b in bodies :
    b['led'] = {}
[print(b) for b in bodies]

for b in bodies :
    for i in range(0, nbTicks) :
        b['led'][i] = 0
        
tickMinutes = 24 * 60 / nbTicks # in minutes

def rgbfy(c):
    if c > 255 : c = 255
    if c < 0 : c = 0
    return int(c)

def printRGBBlock(r, g, b):
    r = rgbfy(r)
    g = rgbfy(g)
    b = rgbfy(b)
    print('\033[;38;2;' +
          str(r) + ';' + str(g) + ';' + str(b) +
          'm\u25a0\033[0m', end = '')

def writeStateOfLights(date = datetime.datetime.now()) :
    print()
    print(date.strftime('%Y-%m-%d %H:%M'))
    nameWidth = 1    
    for b in bodies :
        if nameWidth < len(b['name']) :
            nameWidth = len(b['name'])

    for b in bodies :
        print((b['name'] + ' : |').rjust(nameWidth + len(' : |')), end = '')
        for l in b['led']:
            if b['led'][l] == tycho.maxi :
                printRGBBlock(b['r'], b['g'], b['b'])
            elif b['led'][l] == tycho.on:
                printRGBBlock(b['r'] / 2, b['g'] / 2, b['b'] / 2)
            else :
                print(' ', end = '') 
        print('|')

def loop() :
    print('LOOP')
    global bodies
    tycho.printLongitudes(nbTicks, lat, lon, pole)
    while True:
        for b in bodies :
            if 'horizonNumber' in b.keys() :
                b['led'] = tycho.bodyVisibilityAroundEarth(
                    body = b['horizonNumber'],
                    longitude = lon, latitude = lat,
                    ticks = nbTicks,
                    date = datetime.datetime.utcnow(),
                    pole = pole)
            else : # ISS
                b['led'] = tycho.issVisibilityAroundEarth(
                    longitude = lon,
                    latitude = lat,
                    ticks = nbTicks,
                    pole = pole)
        writeStateOfLights(date = datetime.datetime.now())
        couleursJson = json.dumps(bodies)
        #print(couleursJson)
        publish(couleursJson)
        time.sleep(params['secondsBetweenRefresh'])

def setup() :
    print('SETUP')
    if len(sys.argv) > 1 :
        threading.Thread(target = led.allumer, args=(bodies,)).start()

setup()
loop()


