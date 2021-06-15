import time, datetime, RPi.GPIO as GPIO, tycho

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
# TODO : soleil et lune différent
# TODO : Permettre le sens antihoraire
lumieresGPIO = [17, 27, 22, 5, 6, 13, 26, 16, 23, 24]
for l in lumieresGPIO:
    GPIO.setup(l, GPIO.OUT, initial=GPIO.LOW)

nbTicks = 10 # nb de leds

for l in lumieresGPIO:
    GPIO.output(l, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(l, GPIO.LOW)

def allumer(lightLED) :
    while len(lightLED['Sun']['led']) != nbTicks:
        time.sleep(0.3)
    while True :
        sunlightLED = lightLED['Sun']['led']
        for i in range(0, nbTicks) :
            if sunlightLED[i] == tycho.maxi:
                GPIO.output(lumieresGPIO[i], GPIO.HIGH)
            elif sunlightLED[i] == tycho.off :
                GPIO.output(lumieresGPIO[i], GPIO.LOW)
            elif sunlightLED[i] == tycho.on:
                GPIO.output(lumieresGPIO[i], GPIO.HIGH)
                sunlightLED[i] = -tycho.on
            elif sunlightLED[i] == -tycho.on:
                GPIO.output(lumieresGPIO[i], GPIO.LOW)
                sunlightLED[i] = tycho.on
            
        time.sleep(0.001)
