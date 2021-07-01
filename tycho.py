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
  
def readHorizonDateTime(s) :
    return datetime.datetime.strptime(s, '%Y-%b-%d %H:%M')

def horizonFileName(body, latitude, longitude, date):
    return ('horizonFiles/body' + str(body) +
            'lat' + str(latitude) + 'long'+ str(longitude) +
            'date' + date.strftime('%Y-%m') + '.txt')

def deleteOldHorizonFiles(date) :    
    files = glob.glob("horizonFiles/*.txt")
    for f in files :
        try :
            dateFile = datetime.datetime.strptime(f[len(f)-11:len(f)-4], '%Y-%m')   # ends with 2021-06.txt
            #dateFile = dateFile.replace(hour = 0, minute = 0, day = 1)
            if dateFile < (date - relativedelta(months=+2)) :
                os.remove(f)
                print(f + ' deleted')
        except Exception as e :
            pass

# ne pas paralléliser. La NASA veut pas.
def loadHorizonFile(body, latitude, longitude, date):
    time.sleep(1) # rilaxe un peu
    debut = date.replace(hour = 0, minute = 0, day = 1)
    fin = debut + relativedelta(months=+1)
    debut -= datetime.timedelta(minutes = 2)
    fin += datetime.timedelta(minutes = 2)
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
    
def printLongitudes(nbTicks, lat, lon, pole = -1) :
    delta = 360 / nbTicks / 2
    for i in range(0, nbTicks) :
        actuelle = float(lon) + pole * i * 360 / nbTicks
        precedente = capLongitude(int(actuelle - delta))
        suivante = capLongitude(int(actuelle + delta))
        print(str(precedente) + '->' + str(suivante), end = ',')
    print()
                
def loadISSAPI():
    url = 'http://api.open-notify.org/iss-now.json'
    response = requests.get(url)
    params = json.loads(response.text)
    lat = params['iss_position']['latitude']
    lon = params['iss_position']['longitude']
    return (lat, lon)    
    
def readHorizonFile(body, latitude, longitude, date) :
    bodyStates = {}
    filename  = horizonFileName(body = body,
                                latitude = latitude,
                                longitude = longitude,
                                date = date)
    while not os.path.exists(filename):
        loadHorizonFile(body = body,
                        latitude = latitude,
                        longitude = longitude,
                        date = date)
        deleteOldHorizonFiles(datetime.datetime.now())
    with open(filename) as f :
        for num, line in enumerate(f) :
            try :
                date = readHorizonDateTime(line[1:18])
                bodyStates[date] = line[20]
            except Exception as e :
                print(str(e))
    return bodyStates

def bodyVisibility(body,
                   longitude, latitude,
                   ticks,
                   date):

    bodyStates = readHorizonFile(
        body = body, latitude = latitude,
        longitude = longitude, date = date)
    lastState = ''
    state = ''
    nextState = ''
    visibility = off
    tickBegins = date - datetime.timedelta(minutes = int(24 * 60 / (ticks * 2)))
    tickEnds = date + datetime.timedelta(minutes = int(24 * 60 / (ticks * 2)))
    
    for s in bodyStates :
        if s < tickBegins :
            lastState = bodyStates[s]
        if tickBegins <= s < tickEnds :
            state = bodyStates[s]
        elif s >= tickEnds and nextState == '' :
            nextState = bodyStates[s]
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

    return(visibility)

def bodyVisibilityAroundEarth(body, longitude, latitude,
                              ticks, date = datetime.datetime.utcnow(), pole = -1) :
    visibilities = {}
    for i in range(0, ticks) :
        nextLong = capLongitude(longitude + pole * int((360 / ticks * i)))
        if nextLong > 180 : nextLong -= 360
        visibilities[i] = bodyVisibility(body = body,
                                         longitude = nextLong,
                                         latitude = latitude,
                                         ticks = ticks,
                                         date = date)
    return visibilities

def issVisibilityAroundEarth(longitude, latitude, ticks, pole = -1):
    visibilities = {}
    
    for i in range(0, ticks) :
        visibilities[i] = off
    try :
        (latISS, lonISS) = loadISSAPI()
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
