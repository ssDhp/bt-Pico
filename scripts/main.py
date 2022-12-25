from utime import sleep
from machine import Pin, UART
from NMEA import NMEAparser
from SIM800L import Modem

pub_key = "pub-c-448b0aed-e6f8-4536-a1e4-f235af33663b"
sub_key = "sub-c-10e0e350-30c8-4f8c-84dc-659f6954424e"
channel = "h_bus"
callback = "myCallback"
store = 0
uuid = "pico-test"


# Return a fomatted url
def getUrl(lat: float, lng: float) -> str:
    payload = f"%7B%22lat%22%3A%20{lat}%2C%0A%22lng%22%3A%20{lng}%0A%7D"
    return f"https://ps.pndsn.com/publish/{pub_key}/{sub_key}/0/{channel}/{callback}/{payload}?strore={store},uuid={uuid}"


# Led
picoLed = Pin(25, Pin.OUT)

# GPS
gpsModule = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
gpsParserObject = NMEAparser()

# GPRS
simModule = Modem(uart=UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17)))
simModule.initialize()
simModule.connect(apn="airtelgprs.com")
print(f'\nModem IP address: "{simModule.get_ip_addr()}"')

while True:
    if gpsModule.any():
        try:
            if staus := gpsParserObject.update((gpsModule.read(1)).decode()):
                picoLed.value(1)
                print("\nMaking  a HTTP Get request")
                response = simModule.http_request(getUrl(gpsParserObject.lat, gpsParserObject.lng), "GET")
                print("Response Code:", response.status_code)
                print("Response:", response.content)
                picoLed.value(0)
                if response.status_code == 200:
                    sleep(0.3)
                    picoLed.toggle()
                    sleep(0.3)
                    picoLed.toggle()
                sleep(5)
        except UnicodeError:
            pass
