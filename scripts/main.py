import utime
from machine import Pin, UART
from NMEA import NMEAparser
from SIM800L import Modem

uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
gps = NMEAparser()
pub_key = "pub-c-448b0aed-e6f8-4536-a1e4-f235af33663b"
sub_key = "sub-c-10e0e350-30c8-4f8c-84dc-659f6954424e"
channel = "h_bus"
callback = "myCallback"
store = 0
uuid = "pico-test"

# from micropyGPS import MicropyGPS
led = Pin(25, Pin.OUT)
modem = Modem(
    MODEM_PWKEY_PIN=None,
    MODEM_RST_PIN=None,
    MODEM_POWER_ON_PIN=None,
    MODEM_TX_PIN=Pin(16),
    MODEM_RX_PIN=Pin(17),
)

modem.initialize()
modem.connect(apn="airtelgprs.com")
print('\nModem IP address: "{}"'.format(modem.get_ip_addr()))

while True:
    if uart.any():
        try:
            if staus := gps.update((uart.read(1)).decode("ASCII")):
                led.value(1)
                payload = (
                    f"%7B%22lat%22%3A%20{gps.lat}%2C%0A%22lng%22%3A%20{gps.lng}%0A%7D"
                )
                base_url = f"https://ps.pndsn.com/publish/{pub_key}/{sub_key}/0/{channel}/{callback}/{payload}?strore={store},uuid={uuid}"
                # Example GET
                print("\nNow running demo http GET...")
                response = modem.http_request(base_url, "GET")
                print("Response status code:", response.status_code)
                print("Response content:", response.content)
                led.value(0)
                utime.sleep(5)
        except UnicodeError:
            pass

modem.disconnect()
