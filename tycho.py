import time, datetime, os, requests, glob, json
from dateutil.relativedelta import relativedelta

# all time in UTC

beginning = "$$SOE"
ending = "$$EOE"

sets = 's'
rises = 'r'
transits = 't'
maxi = 2
off = 0
on = 1

statesOfBodiesAroundLat = {}

def readHorizonDateTime(s) :
    return datetime.datetime.strptime(s, '%Y-%b-%d %H:%M')

def horizonFileName(body, latitude, longitude, date):
    return ('horizonFiles/body' + str(body) +
            'lat' + str(latitude) + 'long'+ str(longitude) +
            'date' + date.strftime('%Y-%m') + '.txt')

def horizonFileExists(body, latitude, longitude, date):
    return os.path.exists(horizonFileName(body = body,
                                          latitude = latitude,
                                          longitude = longitude,
                                          date = date))

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
bodyStates = {}

# ne pas paralléliser. La NASA veut pas.
def downloadHorizonFile(body, latitude, longitude, date):
    time.sleep(1) # rilaxe un peu
    debut = date.replace(hour = 0, minute = 0, day = 1)
    fin = debut + relativedelta(months = +1)
    url = ('https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1&'
           'COMMAND=\'' + str(body) + '\'&'
           'CENTER=\'coord@399\'&'
           'COORD_TYPE=\'GEODETIC\'&'
           'SITE_COORD=\'' + str(longitude) + ',' + str(latitude) + ',0\'&'
           'MAKE_EPHEM=\'YES\'&'
           'TABLE_TYPE=\'OBSERVER\'&'
           'START_TIME=\'' + debut.strftime('%Y-%m-%d') + '%20' +
           debut.strftime('%H:%M') + '\'&'
           'STOP_TIME=\'' + fin.strftime('%Y-%m-%d') + '%20' +
           fin.strftime('%H:%M') + '\'&'
           'STEP_SIZE=\'1%20m\'&'
           'CAL_FORMAT=\'CAL\'&'
           'TIME_DIGITS=\'MINUTES\'&'
           'ANG_FORMAT=\'HMS\'&'
           'OUT_UNITS=\'KM-S\'&'
           'RANGE_UNITS=\'AU\'&'
           'APPARENT=\'AIRLESS\'&'
           'SUPPRESS_RANGE_RATE=\'NO\'&'
           'SKIP_DAYLT=\'NO\'&'
           'EXTRA_PREC=\'NO\'&'
           'REF_SYSTEM=\'J2000\'&'
           'CSV_FORMAT=\'NO\'&'
           'OBJ_DATA=\'NO\'&'
           'QUANTITIES=\'10\'&' + 
           'R_T_S_ONLY=\'TVH\'')
    print(url)
    try :
        response = requests.get(url)
        lines = response.text.split('\n')
        f = open(horizonFileName(body = body,
                                 latitude = latitude, longitude = longitude,
                                 date = date), 'w')        
        began = False
        read = False
        for line in lines :
            if began : read = True
            if beginning in line : began = True
            if ending in line :
                read = False
                began = False
            if read:
                f.write(line + '\n')
    except Exception as e :
        print ('Erreur JPL Horizon')

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

def determineVisibilityFromStatesAroundDate(lastState, state, nextState) :
    visibility = off
    if lastState != '' :
        if lastState == transits or lastState == rises :
            visibility = on
    if state == rises or state == sets  :
        visibility = on
    elif state == transits:
        visibility = maxi
    elif (state == '' and lastState == '' and
        (nextState == transits or nextState == sets)) :
        visibility = on
    return visibility

def loadBodyStatesIfNotAlreadyLoaded(body, latitude, longitude, date) :
    global statesOfBodiesAroundLat
    if body not in statesOfBodiesAroundLat :
        statesOfBodiesAroundLat[body] = {}
        
    if (longitude not in statesOfBodiesAroundLat[body] or
        (statesOfBodiesAroundLat[body][longitude][0]['date'].month != date.month)) :
        
        statesOfBodiesAroundLat[body][longitude] = {}

        while not horizonFileExists(body,
                                    latitude = latitude, longitude = longitude,
                                    date = date):
            downloadHorizonFile(body,
                                latitude = latitude, longitude = longitude,
                                date = date)
            deleteOldHorizonFiles(datetime.datetime.now())
            
        with open(horizonFileName(body, latitude, longitude, date)) as f :
            for num, line in enumerate(f) :
                statesOfBodiesAroundLat[body][longitude][num] = {}
                statesOfBodiesAroundLat[body][longitude][num]['date'] = readHorizonDateTime(line[1:18])
                statesOfBodiesAroundLat[body][longitude][num]['state'] = line[20]
    
def bodyVisibilityAtLongitude(body,
                   latitude, longitude,
                   ticks, date):
    lastState = ''
    state = ''
    nextState = ''
    tickBegins = date - datetime.timedelta(minutes = int(24 * 60 / (ticks * 2)))
    tickEnds = date + datetime.timedelta(minutes = int(24 * 60 / (ticks * 2)))

    states = statesOfBodiesAroundLat[body][longitude] 
    for k in states : # Un personne intelligente ferait un binary search
        d = states[k]['date']
        s = states[k]['state']
        if d < tickBegins :
            lastState = s
        if tickBegins <= d < tickEnds :
            state = s
        elif d >= tickEnds and nextState == '' :
            nextState = s
    return determineVisibilityFromStatesAroundDate(lastState, state, nextState)

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
    
    for i in range(0, ticks) :
        visibilities[i] = off
    try :
        (latISS, lonISS) = downloadISSAPI()
        delta = 360 / ticks / 2
        # changer la direction pour pole nord
        for i in range(0, ticks) :
            actuelle = float(longitude) + pole * i * 360 / ticks
            precedente = capLongitude(int(actuelle - delta))
            suivante = capLongitude(int(actuelle + delta))
            if isBetweenLongitudes(float(lonISS), precedente, suivante) :
                visibilities[i] = maxi 
    except Exception as e :
        print ('Erreur ISS')
    return visibilities
