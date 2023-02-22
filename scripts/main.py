import utime
from machine import Pin, UART, I2C
from NMEA import NMEAparser
from SIM800L import Modem
from helper import env, httpGetUrl, crashUrl
from imu import MPU6050
from ssd1306 import SSD1306_I2C
import _thread


crash = False
oled_state = 1
pix_res_x = 128  # SSD1306 horizontal resolution
pix_res_y = 32  # SSD1306 vertical resolution

i2c_dev = I2C(
    1, scl=Pin(15), sda=Pin(14), freq=200000
)  # start I2C on I2C1 (GPIO 26/27)
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
            text = text[:16] + "\n" + text[16:]
        lines = text.splitlines()
        for line in lines:
            oled.text(line.strip(), x, y, 1)
            y += 8  # draw some text at x=0, y=0, colour=1
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

# SIM reset pulled high
simModuleRST = Pin(env.hardware.sim.pin.rst, Pin.OUT)
simModuleRST.high()

# SIM Module
try:
    simModule = Modem(
        uart=UART(
            env.hardware.sim.pin.uart,
            baudrate=9600,
            tx=Pin(env.hardware.sim.pin.tx),
            rx=Pin(env.hardware.sim.pin.rx),
        )
    )
    simModule.initialize()
    display("\nSIM: OK")
    ledBlink(2, 0.1)
except Exception as e:
    display("\nSIM: ERROR")
    print(e)
    ledBlink(5, 0.1)

# GPS Module
try:
    gpsModule = UART(
        env.hardware.gps.pin.uart,
        baudrate=9600,
        tx=Pin(env.hardware.gps.pin.tx),
        rx=Pin(env.hardware.gps.pin.rx),
    )
    gpsParserObject = NMEAparser()
    display("\nGPS: OK")
    ledBlink(2, 0.1)
except Exception as e:
    display("\nGPS: ERROR")
    print(e)
    ledBlink(5, 0.1)


def check_crash():
    global crash, imu
    while True:
        try:
            ax = round(imu.accel.x, 2)
            ay = round(imu.accel.y, 2)
            az = round(imu.accel.z, 2)
            if ax >= 2 or ay >= 5 or az >= 5:
                crash = (ax, ay, az)
                break
        except Exception as e:
            print("IMU Error:", e)
            pass

        # Additional sensor data
        # gx = round(imu.gyro.x)
        # gy = round(imu.gyro.y)
        # gz = round(imu.gyro.z)
        # tem = round(imu.temperature, 2)
        # print(f"A:{(ax,ay,az)}, G:{(gx,gy,gz)}, T:{tem}")


_thread.start_new_thread(check_crash, ())


def check_crash():
    global crash
    global imu
    while True:
        try:
            ax = round(imu.accel.x, 2)
            ay = round(imu.accel.y, 2)
            az = round(imu.accel.z, 2)
            if ax >= 2 or ay >= 5 or az >= 5:
                crash = (ax, ay, az)
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
        display("\nUnable to connect to internet, retrying...")
        print(e)


display(f"\nIP address: \n\n{simModule.get_ip_addr()}")
ledBlink(3, 0.3)

lat = 0
lng = 0
utc = 0

while True:
    if gpsModule.any():
        try:
            if staus := gpsParserObject.update((gpsModule.read(1)).decode("ASCII")):
                if gpsParserObject.lat and gpsParserObject.lng:
                    lat = gpsParserObject.lat
                    lng = gpsParserObject.lng
                    utc = gpsParserObject.utc_time

                    try:
                        display(
                            text=f"HTTP GET\nLat: {lat}\nLng: {lng}\nUTC: {utc}",
                            overflow="eol",
                        )
                        picoLed.value(1)
                        t = utime.ticks_ms()
                        response = simModule.http_request(
                            httpGetUrl(
                                lat,
                                lng,
                                utc,
                            ),
                            "GET",
                        )

                        display(
                            f"Status Code: {response.status_code}\n\nTime Delta:\n{utime.ticks_diff(utime.ticks_ms(),t)/1000} s"
                            f"Status Code: {response.status_code}\nTime Delta: {utime.ticks_diff(utime.ticks_ms(),t)/1000} s"
                        )
                        print("Response:", response.content)
                        # Blink if request was sucessfull
                        if response.status_code == 200:
                            utime.sleep(0.3)
                            picoLed.toggle()
                            utime.sleep(0.3)
                            picoLed.toggle()

                    except Exception as e:
                        display("\nRequest Failed!")
                        print(e)
                        pass
                else:
                    display("\nNo GPS signal")
        except UnicodeError:
            pass
        except Exception as e:
            print(e)
        finally:
            picoLed.value(0)
    if crash:
        try:
            display("Crash Detected!!")
            picoLed.value(1)
            t = utime.ticks_ms()
            print("Trying to upload crash data...")
            response = simModule.http_request(
                crashUrl(
                    lat,
                    lng,
                    utc,
                ),
                "GET",
            )
            display(
                f"Status Code: {response.status_code}\n\nTime Delta:\n{utime.ticks_diff(utime.ticks_ms(),t)/1000} s"
            )
            print("Response:", response.content)
            picoLed.value(0)
            break
        except Exception as e:
            print(e)
            break
