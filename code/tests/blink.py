from machine import Pin
from utime import sleep

pin = Pin("LED", Pin.OUT)

while True:
    try:
        print("Blink")
        pin.toggle()
        sleep(0.5)
    except KeyboardInterrupt:
        break
pin.off()
