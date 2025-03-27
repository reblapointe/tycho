import time, datetime, requests
from dateutil.relativedelta import relativedelta
beginning = "$$SOE"
ending = "$$EOE"

sets = 's'
rises = 'r'
transits = 't'

def readHorizonDateTime(s) :
    return datetime.datetime.strptime(s, '%Y-%b-%d %H:%M')

# ne pas paralléliser. La NASA veut pas.
def downloadHorizonFile(body, latitude, longitude, date, fileName):
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
        response = requests.get(url, verify=False)
        lines = response.text.split('\n')
        f = open(fileName, 'w')        
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
        print (f'Erreur JPL Horizon : {e}')
