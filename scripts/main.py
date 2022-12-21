import utime
from machine import Pin, UART
from micropyGPS import MicropyGPS

gpsModule = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
print(gpsModule)

gps = MicropyGPS()

# ? What is positon fix?
# "Position Fix" means that module can communicate with enough satellites to calculate its position.

# Need to wait for NEO-6M to get position fix
# For a cold start time to first fix is 30 seconds but it might take longer (depends upon signal strength)
# So, I recommmed minimum wait time of 60 seconds.
waitTime = 60
print(f'Waiting {waitTime} seconds for hardware to initalise.')
utime.sleep(waitTime)

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
            # ! On startup sometimes "Junk" is read which causes UnicodeError during decoding
            # ? My best guess is that it is noise but it is also possible that sim800l might be sending some info on startup (most likely in chinese)
            # TODO: Find out what is going on. Check the junk folder.
            print(frame)
