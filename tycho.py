import time, datetime, os, requests, glob, horizonJPLLoader, json
from dateutil.relativedelta import relativedelta

# all time in UTC

maxi = 2
off = 0
on = 1

rts = {}

def horizonFileName(body, latitude, longitude, date):
    return ('horizonFiles/body' + str(body) +
            'lat' + str(latitude) + 'long'+ str(longitude) +
            'date' + date.strftime('%Y-%m') + '.txt')

def deleteOldHorizonFiles(date) :    
    files = glob.glob("horizonFiles/*.txt")
    for f in files :
        try :
            dateFile = datetime.datetime.strptime(f[len(f)-11:len(f)-4], '%Y-%m')
            # ends with 2021-06.txt
            if dateFile < (date - relativedelta(months=+2)) :
                os.remove(f)
                print(f + ' deleted')
        except Exception as e :
            pass

def isBetweenLongitudes(l, a, b) :
    return a <= l <= b or l <= b <= a or b <= a <= l
    
def capLongitude(l) :
    if l < -180 : return l + 360
    if l > 180 : return l - 360
    return l;

def printLongitudesPoleWise(nbTicks, longitude, pole = -1) :
    # North : descending. South : ascending
    delta = 360 / nbTicks / 2
    for i in range(0, nbTicks) :
        actuelle = float(longitude) + pole * i * 360 / nbTicks
        precedente = capLongitude(int(actuelle - delta))
        suivante = capLongitude(int(actuelle + delta))
        print(str(precedente) + '->' + str(suivante), end = ',')
    print()

def downloadISSAPI():
    url = 'http://api.open-notify.org/iss-now.json'
    response = requests.get(url)
    params = json.loads(response.text)
    lat = params['iss_position']['latitude']
    lon = params['iss_position']['longitude']
    return (lat, lon)    

def determineVisibilityFromStatesAroundDate(lastState, currentState, nextState) :
    visibility = off
    if lastState != '' :
        if lastState == horizonJPLLoader.transits or lastState == horizonJPLLoader.rises :
            visibility = on
    if currentState == horizonJPLLoader.rises or currentState == horizonJPLLoader.sets  :
        visibility = on
    elif currentState == horizonJPLLoader.transits:
        visibility = maxi
    elif (currentState == '' and lastState == '' and
        (nextState == horizonJPLLoader.transits or nextState == horizonJPLLoader.sets)) :
        visibility = on
    return visibility

def loadRTSIfNotAlreadyLoaded(body, latitude, longitude, date) :
    global rts
    if body not in rts :
        rts[body] = {}
        
    if (longitude not in rts[body] or
        (rts[body][longitude][0]['date'].month != date.month)) :
        
        rts[body][longitude] = {}
        fileName = horizonFileName(body,
                                   latitude = latitude, longitude = longitude,
                                   date = date)
        while not os.path.exists(fileName) :
            horizonJPLLoader.downloadHorizonFile(body,
                                                 latitude = latitude, longitude = longitude,
                                                 date = date,
                                                 fileName = fileName)
            deleteOldHorizonFiles(datetime.datetime.now())
            
        with open(horizonFileName(body, latitude, longitude, date)) as f :
            for num, line in enumerate(f) :
                rts[body][longitude][num] = {}
                rts[body][longitude][num]['date'] = horizonJPLLoader.readHorizonDateTime(line[1:18])
                rts[body][longitude][num]['state'] = line[20]

def around(states, i, step) :
    last = ''
    if (i + step in states) :
        last = states[i + step]['state']
    return last

def statesAroundDateBinarySearch(states, low, high, mini, maxi) :
    if high >= low:
        mid = (high + low) // 2 # floor
        if mini <= states[mid]['date'] <= maxi:
            return (around(states, mid, -1), states[mid]['state'], around(states, mid, 1)) 
        elif states[mid]['date'] > maxi:
            return statesAroundDateBinarySearch(states, low, mid - 1, mini, maxi)
        else:
            return statesAroundDateBinarySearch(states, mid + 1, high, mini, maxi)
    else:
        return (around(states, low, -1), '', around(states, high, 1))
    
def visibilityAtLongitude(body, latitude, longitude, ticks, date):
    mini = date - datetime.timedelta(minutes = int(24 * 60 / (ticks * 2)))
    maxi = date + datetime.timedelta(minutes = int(24 * 60 / (ticks * 2)))
    
    (l, c, n) = statesAroundDateBinarySearch(rts[body][longitude],
                                             0, len(rts[body][longitude]),
                                             mini, maxi)
    return determineVisibilityFromStatesAroundDate(l, c, n)

def visibilityAroundEarth(body, latitude, longitude, 
                              ticks, date = datetime.datetime.utcnow(),
                              pole = -1) :
    visibilities = {}
    for i in range(0, ticks) :
        nextLong = capLongitude(longitude + pole * int((360 / ticks * i)))
        loadRTSIfNotAlreadyLoaded(body,
                                  latitude = latitude,
                                  longitude = nextLong,
                                  date = date)
        visibilities[i] = visibilityAtLongitude(body = body,
                                                latitude = latitude,
                                                longitude = nextLong,
                                                ticks = ticks,
                                                date = date)
    return visibilities

def issVisibilityAroundEarth(latitude, longitude, ticks, pole = -1):
    visibilities = {}    
    for i in range(0, ticks) : visibilities[i] = off
    try :
        (latISS, lonISS) = downloadISSAPI()
        delta = 360 / ticks / 2
        for i in range(0, ticks) :
            actuelle = float(longitude) + pole * i * 360 / ticks
            precedente = capLongitude(int(actuelle - delta))
            suivante = capLongitude(int(actuelle + delta))
            if isBetweenLongitudes(float(lonISS), precedente, suivante) :
                visibilities[i] = maxi 
    except Exception as e :
        print ('Erreur ISS')
    return visibilities
