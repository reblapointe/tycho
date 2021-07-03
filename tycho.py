import time, datetime, os, requests, glob, horizonJPLLoader, json
from dateutil.relativedelta import relativedelta

# all time in UTC

maxi = 2
off = 0
on = 1

statesOfBodiesAroundLat = {}

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

def loadBodyStatesIfNotAlreadyLoaded(body, latitude, longitude, date) :
    global statesOfBodiesAroundLat
    if body not in statesOfBodiesAroundLat :
        statesOfBodiesAroundLat[body] = {}
        
    if (longitude not in statesOfBodiesAroundLat[body] or
        (statesOfBodiesAroundLat[body][longitude][0]['date'].month != date.month)) :
        
        statesOfBodiesAroundLat[body][longitude] = {}
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
                statesOfBodiesAroundLat[body][longitude][num] = {}
                statesOfBodiesAroundLat[body][longitude][num]['date'] = horizonJPLLoader.readHorizonDateTime(line[1:18])
                statesOfBodiesAroundLat[body][longitude][num]['state'] = line[20]
    

def around(states, i, step) :
    last = ''
    if (i + step in states) :
        last = states[i + step]['state']
    return last

def statesAroundDateBinarySearch(states, low, high, dateMin, dateMax) :
    if high >= low:
        mid = (high + low) // 2
 
        # If element is present at the middle itself
        if dateMin <= states[mid]['date'] <= dateMax:
            return (around(states, mid, -1), states[mid]['state'], around(states, mid, 1))
 
        elif states[mid]['date'] > dateMax:
            return statesAroundDateBinarySearch(states, low, mid - 1, dateMin, dateMax)

        # Else the element can only be present in right subarray
        else:
            return statesAroundDateBinarySearch(states, mid + 1, high, dateMin, dateMax)
 
    else:
        return (around(states, low, -1), '', around(states, high, 1))
    
def bodyVisibilityAtLongitude(body, latitude, longitude, ticks, date):
    tickBegins = date - datetime.timedelta(minutes = int(24 * 60 / (ticks * 2)))
    tickEnds = date + datetime.timedelta(minutes = int(24 * 60 / (ticks * 2)))

    (lastState, currentState, nextState) = statesAroundDateBinarySearch(statesOfBodiesAroundLat[body][longitude],
                                                                        0, len(statesOfBodiesAroundLat[body][longitude]),
                                                                        tickBegins, tickEnds)
    return determineVisibilityFromStatesAroundDate(lastState, currentState, nextState)

def bodyVisibilityAroundEarth(body, latitude, longitude, 
                              ticks, date = datetime.datetime.utcnow(),
                              pole = -1) :
    visibilities = {}
    for i in range(0, ticks) :
        nextLong = capLongitude(longitude + pole * int((360 / ticks * i)))
        loadBodyStatesIfNotAlreadyLoaded(body,
                                         latitude = latitude,
                                         longitude = nextLong,
                                         date = date)
        visibilities[i] = bodyVisibilityAtLongitude(body = body,
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
