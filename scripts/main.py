import _thread
from machine import Pin, UART
from micropyGPS import MicropyGPS
from board import pico

def networking():
    """
    Network thread which runs on the second core of Pico. \n
    It handles communication with PubNub to update location data.
    """
    from sim800l import Modem

    global bus
    reqNum = 1  # No of successfull requests made

    # Setup SIM module
    simUART = UART(bus.sim.uart,baudrate=9600, rx=Pin(bus.sim.rx), tx=Pin(bus.sim.tx))
    simResetPin = bus.sim.rst
    simModule = Modem(simUART, simResetPin)
    while True:
        try:
            simModule.initialize()
            simModule.connect(apn="airtelgprs.net")  # APN is different for different SIM providers
        except Exception as e:
            print(e)
            if "Timeout" in str(e):
                print("Modem timed out! Retrying ...")
            else:
                print("Unable to connect to internet, retrying ...")
        else:
            print("Modem initialized and connected to internet.")
            print(f"IP Address: {simModule.get_ip_addr()}")
            RSSI, BER = simModule.get_signal_strength()  # 99 is "not know or not detectable"
            print(f"RSSI: {RSSI}%, BER: {BER}")
            battChargeStatus, battLevel, battVoltage = simModule.battery_status()
            print(f"Battery: {battChargeStatus}, Level: {battLevel}, Voltage: {battVoltage}")
            break
    # Send loaction to PubNub
    while True:
        url = bus.httpGetUrl()
        print(f"#{reqNum} GET: {url}")
        # Hold the LED high while making http request
        bus.LED.high()
        response = simModule.http_request(url, "GET")
        bus.LED.low()
        if response.status_code == 200:
            reqNum += 1
            bus.blinkLed()

def main():
    """ 
    Main Thread \n
    It reads the sensors and updates the global object
    """
    global bus
    gpsUART = UART(bus.gps.uart,baudrate=9600 ,rx=Pin(bus.gps.rx), tx=Pin(bus.gps.tx))
    parser = MicropyGPS()
    while True:
        if gpsUART.any():
            try:
                if status := parser.update((gpsUART.read(1)).decode("utf-8")):
                    if parser.lat and parser.lng:
                        bus.lat = parser.lat
                        bus.lng = parser.lng
                        bus.utc = parser.utc_time
                    # print(lat,lng, utc)
            except UnicodeError:
                pass
            except Exception as e:
                print(e)


# Object to store config
bus = pico()

# Second Thread
secondThread = _thread.start_new_thread(networking, ())
# Main Thread
main()
