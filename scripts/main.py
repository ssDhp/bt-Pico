import utime
import time
from machine import Pin, UART
from NMEA import NMEAparser
from SIM800L import Modem
from helper import getUrl

# Led
picoLed = Pin(25, Pin.OUT)
# GPS
gpsModule = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
gpsParserObject = NMEAparser()
# GSM/GPRS
simModule = Modem(uart=UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17)))
simModule.initialize()
simModule.connect(apn="airtelgprs.com")
print(f'\nModem IP address: "{simModule.get_ip_addr()}"')

while True:
    if gpsModule.any():
        try:
            if staus := gpsParserObject.update((gpsModule.read(1)).decode("ASCII")):
                print(f"\nLat: {gpsParserObject.lat}, Long: {gpsParserObject.lng}, UTC: {gpsParserObject.utc_time}")
                try:
                    picoLed.value(1)
                    print("Now making HTTP GET request")
                    t = time.ticks_ms()
                    response = simModule.http_request(getUrl(gpsParserObject.lat, gpsParserObject.lng, gpsParserObject.utc_time,), "GET")
                    print(f"Time taken to make the request: {time.ticks_diff(time.ticks_ms(),t)/1000} sec")
                    print("Response code:", response.status_code)
                    print("Response:", response.content)
                    # Blink if request was sucessfull
                    if response.status_code == 200:
                        utime.sleep(0.3)
                        picoLed.toggle()
                        utime.sleep(0.3)
                        picoLed.toggle()
                except Exception as error:
                    print("Request Failed!", error)
                    pass
        except UnicodeError:
            pass
        picoLed.value(0)
