# Run this file to check hardware connections
# Run this only after all the hardware checks are passed.


# Testing Pico
from machine import Pin,UART
from time import sleep
from helper import env
from sys import exit

# This delay is not necessary.
delay = 3 

# On board LED is connected to pin 25
LED = Pin(25, Pin.OUT)
LED.toggle()
print("Hello world")

print(f"Waiting {delay} seconds")
sleep(delay)

# Testing NEO-6M
print("Connecting to GPS module...")
try: 
    gpsModule = UART(env.pico.gps.uart, baudrate=9600, tx=Pin(env.pico.gps.tx), rx=Pin(env.pico.gps.rx))
except Exception as error:
    print("Could not connect to GPS module!! \n", error)
    exit()

print(f"Waiting {delay} seconds")
sleep(delay)

# Testing SIM800L
print("Connecting to SIM module...")
try: 
    simModule = UART(env.pico.sim.uart,baudrate=9600,tx=Pin(env.pico.sim.tx),rx=Pin(env.pico.sim.rx))
except Exception as error:
    print("Could not connect to SIM module!! \n", error)
    exit()

print(f"Waiting {delay} seconds")
sleep(delay)

# Testing OLED screen
print("Connecting to OLED screen...")
import sys
from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C

# ! TO DO: Update this
try: 
    pix_res_x  = 128 # SSD1306 horizontal resolution
    pix_res_y = 32   # SSD1306 vertical resolution

    i2c_dev = I2C(1,scl=Pin(15),sda=Pin(14),freq=200000)  # start I2C on I2C1 (GPIO 26/27)
    i2c_addr = [hex(ii) for ii in i2c_dev.scan()] # get I2C address in hex format
    if i2c_addr==[]:
        print('No I2C Display Found') 
        sys.exit() # exit routine if no dev found
    else:
        print("I2C Address      : {}".format(i2c_addr[0])) # I2C device address
        print("I2C Configuration: {}".format(i2c_dev)) # print I2C params


    oled = SSD1306_I2C(pix_res_x, pix_res_y, i2c_dev) # oled controller

    oled.write_cmd(0xc0) # flip display to place 0,0 at lower-left corner
    adc_2 = ADC(2) # ADC channel 2 for input
    while True:
        oled.fill(0) # clear the display
        for jj in range(pix_res_x): # loop through horizontal display resolution
            adc_pt = adc_2.read_u16() # read adc and get 16-bit data point
            plot_pt = (adc_pt/((2**16)-1))*(pix_res_y-1) # convert to OLED pixels
            oled.text('.',jj,int(plot_pt)) # update x=jj with data point
        oled.show() # show the new text and image
except Exception as error:
    print("Could not connect to OLED screen!! \n", error)

exit()

