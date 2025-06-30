# Test connections to the modules

import machine
import time
from device_config import DeviceConfig

test_config = DeviceConfig()
print(test_config)

gps_uart = machine.UART(
    test_config.GPS_module_config.uart_id,
    9600,
    # test_config.GPS_module_config.baudrate,
    tx=test_config.GPS_module_config.tx,
    rx=test_config.GPS_module_config.rx,
)

sim_uart = machine.UART(
    test_config.SIM_module_config.uart_id,
    115200,
    # test_config.SIM_module_config.baudrate,
    tx=test_config.SIM_module_config.tx,
    rx=test_config.SIM_module_config.rx,
)
sim_reset_pin = machine.Pin(
    test_config.SIM_module_config.reset_pin, machine.Pin.OUT, machine.Pin.PULL_UP
)

print("Resetting SIM Module...", end="")
sim_reset_pin.low()
time.sleep_ms(200)  # Minimum delay 105 ms
sim_reset_pin.high()
time.sleep_ms(3000)  # Minimum delay 2700 ms
print("Done.")

print("Writing to SIM: AT")
sim_uart.write("AT\n")
while True:
    if gps_uart.any(): 
        print(f"[GPS] {gps_uart.read()}")
    if sim_uart.any(): 
        print(f"[SIM] {sim_uart.read()}")
    time.sleep_ms(100)
