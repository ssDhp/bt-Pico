import utime
import time
from machine import Pin, UART
from NMEA import NMEAparser
from SIM800L import Modem
from helper import getUrl

# GPS
gpsModule = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
gpsParserObject = NMEAparser()
# Led
picoLed = Pin(25, Pin.OUT)
# SIM
simModule = Modem(uart=UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17)))
simModule.initialize()
simModule.connect(apn="airtelgprs.com")
print(f'\nModem IP address: "{simModule.get_ip_addr()}"')

while True:
    if gpsModule.any():
        # Init a byte array to store serial data
        frame = bytearray(1024)
        # Store the read data into byte array
        gpsModule.readinto(frame)
        # Decode bytearray into string
        try:
            data = frame.decode()
            # Update gps data
            for x in data:
                gpsParserObject.update(x)
        except UnicodeError:
            pass
        print(f"\nLat: {gpsParserObject.lat}, Long: {gpsParserObject.lng}, UTC: {gpsParserObject.utc_time}")
        picoLed.value(1)
        try:
            print("Now running GET command")
            t = time.ticks_ms()

            response = simModule.http_request(getUrl(gpsParserObject.lat, gpsParserObject.lng, gpsParserObject.utc_time), "GET",)
            print(f"Time taken to make the  request:{time.ticks_diff(time.ticks_ms(),t)/1000} sec")
            print("Response status code:", response.status_code)
            print("Response content:", response.content)
        except Exception:
            print("Request Failed!")
            pass
        picoLed.value(0)
        # Blink if request was sucessfull
        if response.status_code == 200:
            utime.sleep(0.3)
            picoLed.toggle()
            utime.sleep(0.3)
            picoLed.toggle()
        # utime.sleep(5)
