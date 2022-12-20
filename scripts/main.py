import utime
from machine import Pin, UART
from NMEA import NMEAparser

gpsModule = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
print(gpsModule)

