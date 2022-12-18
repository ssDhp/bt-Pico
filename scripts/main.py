import utime
from machine import Pin, UART
from micropyGPS import MicropyGPS

gpsModule = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
print(gpsModule)

buff = bytearray(255)
gps = MicropyGPS()

while True:
    gpsModule.readline()
    buff = str(gpsModule.readline())
    parts = buff.split(',')
    print(buff)
    utime.sleep_ms(1000)
