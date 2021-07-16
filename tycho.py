import time, datetime, os, requests, glob, horizonJPLLoader, json
from dateutil.relativedelta import relativedelta

# all time in UTC

class visibility:
    maxi = 2
    off = 0
    on = 1

# Rise Transit and Set times
class RTSTime :
    def __init__(self, d, s) :
        self.d = d
        self.s = s

# list of RTSTimes for body at latitude longitude
rts = {}
loadedMonth = 0

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
            if dateFile < (date - relativedelta(months=+12)) :
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
    #url = 'http://api.open-notify.org/iss-now.json'
    url = 'https://api.wheretheiss.at/v1/satellites/25544'
    response = requests.get(url)
    params = json.loads(response.text)
    #lat = params['iss_position']['latitude']
    #lon = params['iss_position']['longitude']
    lat = params['latitude']
    lon = params['longitude']
    return (lat, lon)    

def determineVisibilityFromStatesAroundDate(lastState, currentState, nextState) :
    v = visibility.off
    if lastState != '' :
        if (lastState == horizonJPLLoader.transits or
            lastState == horizonJPLLoader.rises) :
            v = visibility.on
    if (currentState == horizonJPLLoader.rises or
        currentState == horizonJPLLoader.sets)  :
        v = visibility.on
    elif currentState == horizonJPLLoader.transits:
        v = visibility.maxi
    elif (currentState == '' and lastState == '' and
        (nextState == horizonJPLLoader.transits or
         nextState == horizonJPLLoader.sets)) :
        v = visibility.on
    return v

def loadRTSIfNotAlreadyLoaded(body, latitude, longitude, date) :
    global rts
    global loadedMonth
    if loadedMonth != date.month :
        rts = {}
        loadedMonth = date.month
        deleteOldHorizonFiles(datetime.datetime.now())
        
    if body not in rts :
        rts[body] = {}
        
    if (longitude not in rts[body]) :
        rts[body][longitude] = {}
    
        fileName = horizonFileName(body,
                                   latitude = latitude, longitude = longitude,
                                   date = date)
        while not os.path.exists(fileName) :
            horizonJPLLoader.downloadHorizonFile(body,
                                                 latitude = latitude,
                                                 longitude = longitude,
                                                 date = date,
                                                 fileName = fileName)
            
        with open(horizonFileName(body, latitude, longitude, date)) as f :
            try :
                for num, line in enumerate(f) :
                    rts[body][longitude][num] = RTSTime(
                        horizonJPLLoader.readHorizonDateTime(line[1:18]),
                        line[20])
            except Exception as e:
                print(e)
                
def around(states, i, step) :
    last = ''
    if (i + step in states) :
        last = states[i + step].s
    return last

def statesAroundDateBinarySearch(states, low, high, mini, maxi) :
    mid = (high + low) // 2 # floor
    if high >= low and mid in states:
        if mini <= states[mid].d <= maxi:
            return (around(states, mid, -1),
                    states[mid].s,
                    around(states, mid, 1)) 
        elif states[mid].d > maxi:
            return statesAroundDateBinarySearch(states,
                                                low, mid - 1, mini, maxi)
        else:
            return statesAroundDateBinarySearch(states,
                                                mid + 1, high, mini, maxi)
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
    for i in range(0, ticks) : visibilities[i] = visibility.off
    try :
        (latISS, lonISS) = downloadISSAPI()
        delta = 360 / ticks / 2
        for i in range(0, ticks) :
            actuelle = float(longitude) + pole * i * 360 / ticks
            precedente = capLongitude(int(actuelle - delta))
            suivante = capLongitude(int(actuelle + delta))
            if isBetweenLongitudes(float(lonISS), precedente, suivante) :
                visibilities[i] = visibility.maxi
    except Exception as e :
        print ('Erreur ISS')
    return visibilities
