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
waitTimeSec = 5  # ! For testing set to 5 seconds, Will remove later
print(f'Waiting {waitTimeSec} seconds for hardware to initalise.')
utime.sleep(waitTimeSec)

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
            # ! On startup, when data is read from NEO-6M some hexadecimal characters are in the front of the first NMEA sentence.
            # ! These characters then cause an Unicode error during decoding
            # ! This happens only once during the startup and characters are different everytime.
            # Possible causes:
            #   - Noise
            #   - Characters from last time.
            #   - Some info that module sends on startup.
            #   - Different encoding
            #  TODO: Find out what these random characters are? Check "junk" folder for more.
            # * Updates:
            # Tried different encodings but only 'unicode_escape' seemed to work. Decoded it in python repl, output was random letter.
            print(frame)
