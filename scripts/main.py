import utime
from machine import Pin, UART
from micropyGPS import MicropyGPS

gpsModule = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
print(gpsModule)

gps = MicropyGPS()

while True:
    while gpsModule.any():
        # Init a byte array to store serial data
        frame = bytearray(1024)
        # Store the read data into byte array
        gpsModule.readinto(frame)
        # Decode bytearray into string
        try:
            data = frame.decode()
            for line in data.splitlines():
                if line[3:6] in ['RMC', 'GGA']:
                    # Update gps data
                    for x in line:
                        gps.update(x)
                    print(gps.latitude_string(), ",", gps.longitude_string())

        except UnicodeError:
            # Soemtimes noise is read which causes UnicodeError during decoding
            print(frame)
