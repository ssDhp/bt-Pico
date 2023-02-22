# I know this is very buggy and poorly written

import utime
from machine import Pin, UART, I2C
from NMEA import NMEAparser
from SIM800L import Modem
from helper import env, getUrl
from imu import MPU6050
from ssd1306 import SSD1306_I2C
import _thread

crash = False
oled_state = 1
pix_res_x = 128  # SSD1306 horizontal resolution
pix_res_y = 32   # SSD1306 vertical resolution

i2c_dev = I2C(1, scl=Pin(15), sda=Pin(14), freq=200000)  # start I2C on I2C1 (GPIO 26/27)
try:
    oled = SSD1306_I2C(pix_res_x, pix_res_y, i2c_dev)  # oled controller
except:
    oled_state = 0
i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=400000)
imu = MPU6050(i2c)

def display(text: str, x=0, y=0, color=1):
    print(text)
    if oled_state:
        oled.fill(0)  # clear the display
        # 128 Horizontal resolution
        # Each char is 8 X 8
        # So 16 char in one line
        if len(text) > 16:
            text = text[:16]+"\n"+text[16:]
        lines = text.splitlines()
        for line in lines:
            oled.text(line.strip(), x, y, 1)
            y += 8    # draw some text at x=0, y=0, colour=1
            oled.show()  # show the new text and image


display("Bt-Pico MK-IV \n Booting... ")

""" Testing
# while True:
#     ax = round(imu.accel.x, 2)
#     ay = round(imu.accel.y, 2)
#     az = round(imu.accel.z, 2)
#     if ax >= 1.5 or ay >= 5 or az >= 5:
#         crash = True
#         display("Crash")

"""

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


def check_crash():
    global crash
    global imu
    while True:
        try:
            ax = round(imu.accel.x, 2)
            ay = round(imu.accel.y, 2)
            az = round(imu.accel.z, 2)
            if ax >= 2 or ay >= 5 or az >= 5:
                crash = (ax,ay,az)
        except IndexError as e:
            pass

        # Additional sensor data
        # gx = round(imu.gyro.x)
        # gy = round(imu.gyro.y)
        # gz = round(imu.gyro.z)
        # tem = round(imu.temperature, 2)
        # print(f"A:{(ax,ay,az)}, G:{(gx,gy,gz)}, T:{tem}")
_thread.start_new_thread(check_crash, ())

while True:
    try:
        simModule.connect(apn="airtelgprs.net")
        break
    except Exception as e:
        display("Unable to connect to internet, retrying...")
        print(e)

display(f'\nModem IP address: "{simModule.get_ip_addr()}"')

# Blink if modem ready
picoLed.toggle()
utime.sleep(0.3)
picoLed.toggle()

while True:
    if gpsModule.any():
        try:
            if staus := gpsParserObject.update((gpsModule.read(1)).decode("ASCII")):
                if gpsParserObject.lat and gpsParserObject.lng:
                    display(
                        f"\nLat: {gpsParserObject.lat}, Long: {gpsParserObject.lng}, UTC: {gpsParserObject.utc_time}"
                    )
                    try:
                        picoLed.value(1)
                        display("Now making HTTP GET request")
                        t = utime.ticks_ms()
                        response = simModule.http_request(
                            getUrl(
                                gpsParserObject.lat,
                                gpsParserObject.lng,
                                gpsParserObject.utc_time,
                            ),
                            "GET",
                        )

                        display(
                            f"Time taken to make the request: {utime.ticks_diff(utime.ticks_ms(),t)/1000} sec"
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
                        display("Request Failed!")
                        print(error)
                        pass
        except UnicodeError:
            pass
        picoLed.value(0)
    if crash:
        display("Crash Detected!!")
