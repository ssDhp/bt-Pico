import utime
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
        try:
            if staus := gpsParserObject.update((gpsModule.read(1)).decode("ASCII")):
                picoLed.value(1)
                print("\nNow running GET command")
                response = simModule.http_request(
                    getUrl(
                        gpsParserObject.lat,
                        gpsParserObject.lng,
                        gpsParserObject.utc_time,
                    ),
                    "GET",
                )
                print("Response status code:", response.status_code)
                print("Response content:", response.content)
                picoLed.value(0)
                utime.sleep(5)
        except UnicodeError:
            pass
