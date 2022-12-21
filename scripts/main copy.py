import utime
from machine import Pin, UART
# from micropyGPS import MicropyGPS

gsm = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
print(gsm)

while True:
    # Handshake test
    gsm.write(b'AT\r\n')
    print(gsm.read())
    # Signal quality test, 0 - 31, 31 best
    gsm.write(b'AT+CSQ\r\n')
    print(gsm.read())
    # Read SIM info
    gsm.write(b'AT+CCID\r\n')
    # Check whether it has registered in the network
    gsm.write(b'AT+CREG?\r\n')
    utime.sleep(3)
