import utime
import time
from machine import Pin, UART
from NMEA import NMEAparser
from SIM800L import Modem
from helper import env, getUrl


# Led
picoLed = Pin(env.pico.led, Pin.OUT)
# SIM reset pulled high
simModuleRST = Pin(env.pico.sim.rst, Pin.OUT)
simModuleRST.high()
# GPS
gpsModule = UART(
    env.pico.gps.uart, baudrate=9600, tx=Pin(env.pico.gps.tx), rx=Pin(env.pico.gps.rx)
)
gpsParserObject = NMEAparser()
# GSM/GPRS
simModule = Modem(
    uart=UART(
        env.pico.sim.uart,
        baudrate=9600,
        tx=Pin(env.pico.sim.tx),
        rx=Pin(env.pico.sim.rx),
    )
)
simModule.initialize()

while True:
    try:
        simModule.connect(apn="airtelgprs.net")
        break
    except Exception as e:
        print("Unable to connect to internet, retrying...", e)

print(f'\nModem IP address: "{simModule.get_ip_addr()}"')

# Blink if modem ready
picoLed.toggle()
utime.sleep(0.3)
picoLed.toggle()

while True:
    if gpsModule.any():
        try:
            if staus := gpsParserObject.update((gpsModule.read(1)).decode("ASCII")):
                if gpsParserObject.lat and gpsParserObject.lng:
                    print(
                        f"\nLat: {gpsParserObject.lat}, Long: {gpsParserObject.lng}, UTC: {gpsParserObject.utc_time}"
                    )
                    try:
                        picoLed.value(1)
                        print("Now making HTTP GET request")
                        t = time.ticks_ms()
                        response = simModule.http_request(
                            getUrl(
                                gpsParserObject.lat,
                                gpsParserObject.lng,
                                gpsParserObject.utc_time,
                            ),
                            "GET",
                        )

                        print(
                            f"Time taken to make the request: {time.ticks_diff(time.ticks_ms(),t)/1000} sec"
                        )
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
