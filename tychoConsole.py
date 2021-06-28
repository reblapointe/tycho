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
# mosquitto_sub -h 192.168.1.101 -t tycho/60

params = {}
client = 0

def paramsDefault(paramName, default) :
    global params
    if paramName not in params :
        print(paramName + ' undefined')
        params[paramName] = default
    print(paramName + ' ' + str(params[paramName]))
    
def initParams() :
    global params
    global client
    
    with open('userSettings.json') as f:
        params = json.load(f)

    paramsDefault('latitude', 0)
    paramsDefault('longitude', 0)
    paramsDefault('nbLeds', 60)
    paramsDefault('standingOnPole', 'north')
    paramsDefault('secondsBetweenRefresh', 60)
    params['standingOnPole'] = 1 if params['standingOnPole'] == 'south' else -1
    if params['secondsBetweenRefresh'] < 10 : params['secondsBetweenRefresh'] = 60
    params['bodies'][:] = [b for b in params['bodies'] if b['scope'] != 0]

    if 'mqtt_ip' in params :
        client = initMQTT(params['mqtt_ip'], 1883 if 'mqtt_port' not in params else params['mqtt_port'])
        print('mqtt broker ip ' + params['mqtt_ip'])
        print('mqtt port ' + params['mqtt_port'])
    else :
        print('no mqtt broker')

    # init celestial params['bodies']' leds
    for b in params['bodies'] :
        b['led'] = {}
        print(b)
        for i in range(0, params['nbLeds']) :
            b['led'][i] = 0
        
        
def publish(s:str) :
    if 'mqtt_ip' in params : 
        ret = client.publish('tycho/' + str(params['nbLeds']), s, retain = True)

def initMQTT(broker, port) :
    def on_publish(client, userdata, result):
        print(userdata)
    client = paho.Client()
    client.on_publish = on_publish
    client.connect(broker, port, 3600)
    return client

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
    for b in params['bodies'] :
        if nameWidth < len(b['name']) :
            nameWidth = len(b['name'])

    for b in params['bodies'] :
        print((b['name'] + ' : |').rjust(nameWidth + len(' : |')), end = '')
        for l in range(0, params['nbLeds']):
            if b['led'][l] == tycho.maxi :
                printRGBBlock(b['r'], b['g'], b['b'])
            elif b['led'][l] == tycho.on:
                printRGBBlock(b['r'] / 2, b['g'] / 2, b['b'] / 2)
            else :
                print(' ', end = '') 
        print('|')

def loop() :
    print('LOOP')
    tycho.printLongitudes(params['nbLeds'], params['latitude'], params['longitude'], params['standingOnPole'])
    while True:
        for b in params['bodies'] :
            if 'horizonNumber' in b.keys() :
                b['led'] = tycho.bodyVisibilityAroundEarth(
                    body = b['horizonNumber'],
                    longitude = params['longitude'], latitude = params['latitude'],
                    ticks = params['nbLeds'],
                    date = datetime.datetime.utcnow(),
                    pole = params['standingOnPole'])
            else : # ISS
                b['led'] = tycho.issVisibilityAroundEarth(
                    longitude = params['longitude'],
                    latitude = params['latitude'],
                    ticks = params['nbLeds'],
                    pole = params['standingOnPole'])
        writeStateOfLights(date = datetime.datetime.now())
        couleursJson = json.dumps(params['bodies'])
        publish(couleursJson)
        time.sleep(params['secondsBetweenRefresh'])

def setup() :
    print('SETUP')
    initParams()
    if len(sys.argv) > 1 :
        threading.Thread(target = led.allumer, args=(params['bodies'],)).start()

setup()
loop()


