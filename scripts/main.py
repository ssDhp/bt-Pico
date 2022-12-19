import utime
from machine import Pin, UART
from NMEA import NMEAparser

gpsModule = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
print(gpsModule)

gps = NMEAparser()

while True:
    while char := gpsModule.read(1).decode("ASCII"):
        if status := gps.update(char):
            print(
                status,  # type
                "lat",  # latitude (ddf)
                gps.lat,
                "lng",  # longitude (ddf)
                gps.lng,
                "utc time",  # gps packet time
                gps.utc_time,
                "fix time",  # system time
                gps.fix_time,
            )
    utime.sleep_ms(1000)
