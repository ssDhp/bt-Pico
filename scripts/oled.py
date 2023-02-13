import time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C


pix_res_x  = 128 # SSD1306 horizontal resolution
pix_res_y = 32   # SSD1306 vertical resolution

i2c_dev = I2C(1,scl=Pin(15),sda=Pin(14),freq=200000)  # start I2C on I2C1 (GPIO 26/27)


oled = SSD1306_I2C(pix_res_x, pix_res_y, i2c_dev) # oled controller

def display(text: str, x= 0, y= 0, color= 1):
    print(text)
    oled.fill(0) # clear the display
    # 128 Horizontal resolution
    # Each char is 8 X 8
    # So 16 char in one line
    if len(text)> 16:
        text = text[:16]+"\n"+text[16:]
    lines = text.splitlines()
    for line in lines:
        oled.text(line.strip(), x, y, 1)
        y += 8    # draw some text at x=0, y=0, colour=1
        oled.show() # show the new text and image

