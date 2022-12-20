import utime
from machine import Pin, UART
from micropyGPS import MicropyGPS

gpsModule = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
print(gpsModule)

gps = MicropyGPS()

while True:
    while char := gpsModule.read(1):
        if status := gps.update(char):
            print()
    utime.sleep_ms(1000)
