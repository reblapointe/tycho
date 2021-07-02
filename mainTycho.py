# IN DEV ENV :
#    install pipenv (for dev environment)
#        python3 -m pip install --user pipenv
#    install all packages (for dev environment) and export to requirements.txt
#        pipenv install requests (....)
#        pipenv lock -r > requirements.txt
#
# INSTALL
#     load requirements
#         pip3 install -r requirements.txt
#
# RUN
#    python3 mainTycho.py
#    or (no hangup)
#    python3 mainTycho.py

# START MQTT BROKER
#     mosquitto -d
# VIEW MQTT TOPIC
#     mosquitto_sub -h 192.168.1.100 -t tycho/60

import json, tycho, time, datetime, threading, paho.mqtt.client as paho, os

params = {}   # simulation parameters
client = 0    # mqtt client

def paramsDefault(paramName, default) :
    global params
    if paramName not in params :
        print(paramName + ' undefined')
        params[paramName] = default
    print(paramName + ' ' + str(params[paramName]))
    
def on_publish(client, userdata, result):
    print(userdata)

def initMQTT() :
    global client
    try :
        if 'mqtt_ip' in params :
            paramsDefault('mqtt_port', 1883)
            client = paho.Client()
            client.on_publish = on_publish
            client.connect(params['mqtt_ip'], params['mqtt_port'], 3600)
            print('mqtt broker ' + params['mqtt_ip'] + ':' + str(params['mqtt_port']))
        else :
            print('no mqtt broker')
    except Exception as e :
        print(str(e))
    
def initParams() :
    global params
    
    with open('userSettings.json') as f :
        params = json.load(f)
    paramsDefault('brightness', 25)
    paramsDefault('latitude', 0)
    paramsDefault('longitude', 0)
    paramsDefault('nbLeds', 60)
    paramsDefault('secondsBetweenRefresh', 60)
    paramsDefault('standingOnPole', 'north')
    paramsDefault('led_topic', 'tycho/' + str(params['nbLeds']))
    paramsDefault('json_topic', 'tycho/json/' + str(params['nbLeds']))
    
    params['standingOnPole'] = 1 if params['standingOnPole'] == 'south' else -1 
    if params['secondsBetweenRefresh'] < 10 : params['secondsBetweenRefresh'] = 60

    params['bodies'][:] = [b for b in params['bodies'] if b['scope'] != 0]
    print(params)
    for b in params['bodies'] :
        b['led'] = {}
        for i in range(0, params['nbLeds']) : b['led'][i] = 0

def publish(channel:str, s:str) :
    if 'mqtt_ip' in params : 
        ret = client.publish(channel, s, retain = True)


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
    print(date.strftime('%Y-%m-%d %H:%M'))
    nameWidth = 1    
    for b in params['bodies'] :
        if nameWidth < len(b['name']) :
            nameWidth = len(b['name'])

    for b in params['bodies'] :
        print((b['name'] + ' : |').rjust(nameWidth + len(' : |')), end = '')
        for l in range(0, params['nbLeds']) :
            if b['led'][l] == tycho.maxi :
                printRGBBlock(b['r'], b['g'], b['b'])
            elif b['led'][l] == tycho.on:
                printRGBBlock(b['r'] / 2, b['g'] / 2, b['b'] / 2)
            else :
                print(' ', end = '') 
        print('|')

def buildLEDRing() :
    strip = ''
    dim = params['brightness'] / 100.0
    for i in range(0, params['nbLeds'])  :
        r = 0
        g = 0
        b = 0
        for body in params['bodies'] :
            if (body['scope'] == 2 and body['led'][i] == 1) :
                r += (body['r'] / 5) % 256
                g += (body['g'] / 5) % 256
                b += (body['b'] / 5) % 256
    
        for body in params['bodies'] :
            if (body['led'][i] == 2) :
                r = body['r']
                g = body['g']
                b = body['b']
        strip += str(int(r * dim)) + ' ' + str(int(g * dim)) + ' ' + str(int(b * dim)) + ' '
    return strip

def loop() :
    print('LOOP')
    tycho.printLongitudesPoleWise(params['nbLeds'],
                                  longitude = params['longitude'],
                                  pole = params['standingOnPole'])
    while True:
        for b in params['bodies'] :
            if 'horizonNumber' in b.keys() :
                b['led'] = tycho.bodyVisibilityAroundEarth(
                    body = b['horizonNumber'],
                    latitude = params['latitude'],
                    longitude = params['longitude'],
                    ticks = params['nbLeds'],
                    date = datetime.datetime.utcnow(),
                    pole = params['standingOnPole'])
            else : # ISS
                b['led'] = tycho.issVisibilityAroundEarth(
                    latitude = params['latitude'],
                    longitude = params['longitude'],
                    ticks = params['nbLeds'],
                    pole = params['standingOnPole'])
        writeStateOfLights()
        publish(params['led_topic'], buildLEDRing())
        publish(params['json_topic'], json.dumps(params['bodies']))
        time.sleep(params['secondsBetweenRefresh'])

def setup() :
    print('SETUP')
    initParams()
    initMQTT()

def demo() :
    print('DEMO')
    d = datetime.datetime.utcnow().replace(day = 1, hour = 0, minute = 0, second = 0)
    nextMonth = d.replace(day = 28) + datetime.timedelta(days = 4)
    nbDays = (nextMonth - datetime.timedelta(days = nextMonth.day)).day
    for i in range(0,  (nbDays - 1) * 24 - 1) :
        d = d + datetime.timedelta(hours = 1)
        for b in params['bodies'] :
            if 'horizonNumber' in b.keys() :
                b['led'] = tycho.bodyVisibilityAroundEarth(
                    body = b['horizonNumber'],
                    latitude = params['latitude'],
                    longitude = params['longitude'],
                    ticks = params['nbLeds'],
                    date = d,
                    pole = params['standingOnPole'])
        os.system('clear')
        print('UTC ', end = '')
        writeStateOfLights(d)
        time.sleep(0.01)

setup()
demo()
loop()


