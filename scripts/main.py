import utime
from machine import Pin, UART, I2C
from NMEA import NMEAparser
from SIM800L import Modem
from helper import env, httpGetUrl, crashUrl
from imu import MPU6050
from ssd1306 import SSD1306_I2C
import _thread

# function definations


def ledBlink(times: int = 1, delay: int = 1):
    global led_state, picoLed
    if led_state:
        picoLed.value(0)  # turn off led if open
        for _ in range(times * 2 - 1):
            picoLed.toggle()
            utime.sleep(delay)
        picoLed.value(0)  # turn off led if somehow left on


def display(
    text: str, x: int = 0, y: int = 0, color: int = 1, overflow: str = "wrap"
):  # overflow skip character = "eol : chop the line" or "wrap : wrap to next line"
    global last_display, oled_state, oled
    try:
        print(text)
        if oled_state and last_display != text:
            oled.fill(0)  # clear the display
            lines = text.splitlines()
            for index in range(4):
                if index < len(lines):
                    line = lines[index]
                    if len(line) > 16:
                        if overflow == "eol":
                            line = line[:16]
                        else:
                            lines.insert(index + 1, line[16:])
                            line = line[:16]
                    oled.text(line.strip(), x, y, 1)
                    y += 8  # draw some text at x=0, y=0, colour=1
                    oled.show()  # show the new text and image
            last_display = text
    except Exception as e:
        print("Display exception", e)


# LED
try:
    led_state = 1
    picoLed = Pin(env.hardware.led.pin, Pin.OUT)
    print("\nLED: OK")
    ledBlink(2, 0.1)
except Exception as e:
    led_state = 0
    print("\nLED: ERROR")
    print(e)


# OLED Screen
last_display = ""
try:
    oled_state = 1
    oled = SSD1306_I2C(
        width=env.hardware.oled.resolution.width,  # 128
        height=env.hardware.oled.resolution.height,  # 32
        i2c=I2C(
            id=env.hardware.oled.pin.i2c,  # 1
            scl=Pin(env.hardware.oled.pin.scl),  # 15
            sda=Pin(env.hardware.oled.pin.sda),  # 14
            freq=env.hardware.oled.pin.frequency,  # 200000
        ),
    )
    display("\nOLED: OK")
    ledBlink(2, 0.1)
except Exception as e:
    oled_state = 0
    print("\nOLED: ERROR")
    print(e)
    ledBlink(5, 0.1)


# IMU
crash = False
try:
    imu_state = 1
    imu = MPU6050(
        side_str=I2C(
            id=env.hardware.imu.pin.i2c,  # 0
            scl=Pin(env.hardware.imu.pin.scl),  # 17
            sda=Pin(env.hardware.imu.pin.sda),  # 14
            freq=env.hardware.imu.pin.frequency,  # 400000
        ),
    )
    display("\nIMU: OK")
    ledBlink(2, 0.1)
except Exception as e:
    imu_state = 0
    display("\nIMU: ERROR")
    print(e)
    ledBlink(5, 0.1)

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
