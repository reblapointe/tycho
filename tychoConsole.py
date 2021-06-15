import json, tycho, time, datetime, threading, sys, paho.mqtt.client as paho

broker = '192.168.1.139'
port = 1883

#Start broker : mosquitto -d
#View topic :
# (localhost) mosquitto_sub -d -t testTopic
# mosquitto_sub -L 'mqtt://10.0.0.57:1883/tycho/60'

def on_publish(client, userdata, result):
    print(userdata)

client = paho.Client('control')
client.on_publish = on_publish
client.connect(broker, port)

def publish(s:str) :
    ret = client.publish('tycho/60', s, retain = True)

with open('userSettings.json') as f:
    params = json.load(f)

lat = params["latitude"]
lon = params["longitude"]
bodies = params['bodies']
showISS = False

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

for b in bodies :
    b['led'] = {}
[print(b) for b in bodies]

for b in bodies :
    for i in range(0, nbTicks) :
        b['led'][i] = 1
        
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

def isBetweenLongitudes(l, a, b) :
    return a <= l <= b or l <= b <= a or b <= a <= l
    
def capLongitude(l) :
    if l < -180 : return l + 360
    if l > 180 : return l - 360
    return l;

def writeISS(latISS, lonISS):
    
    for b in bodies :
        if b['name'] == 'ISS' :
            iss = b

    delta = 360 / nbTicks / 2
    for i in range(0, nbTicks) :
        actuelle = float(lon) + i * 360 / nbTicks
        precedente = capLongitude(int(actuelle - delta))
        suivante = capLongitude(int(actuelle + delta))
        if isBetweenLongitudes(float(lonISS), precedente, suivante) :
            iss['led'][i] = tycho.maxi
        else :
            iss['led'][i] = tycho.off
    print(iss)
    
def printLongitudes() :
    delta = 360 / nbTicks / 2
    for i in range(0, nbTicks) :
        actuelle = float(lon) + i * 360 / nbTicks
        precedente = capLongitude(int(actuelle - delta))
        suivante = capLongitude(int(actuelle + delta))
        print(str(precedente) + '->' + str(suivante), end = ',')
    print()
    
def loop() :
    print('LOOP')
    global bodies
    printLongitudes()
    while True:
        for b in bodies :
            if 'horizonNumber' in b.keys() :
                b['led'] = tycho.bodyVisibilityAroundEarth(
                    body = b['horizonNumber'],
                    longitude = lon, latitude = lat,
                    ticks = nbTicks,
                    date = datetime.datetime.utcnow())
        if showISS :
            (latISS, lonISS) = tycho.loadISSAPI()
            writeISS(latISS, lonISS)
        writeStateOfLights(date = datetime.datetime.now())
        couleursJson = json.dumps(bodies)
        #print(couleursJson)
        publish(couleursJson)
        time.sleep(60)
        tycho.deleteOldHorizonFiles(datetime.datetime.now())

def setup() :
    print('SETUP')
    if len(sys.argv) > 1 :
        threading.Thread(target = led.allumer, args=(bodies,)).start()

setup()
loop()
