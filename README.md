## bt-Pico - GPS Tracker

![v2 image](/img/imagev2.jpg)
GPS Tracker updates its location on the website [here](https://bt-p1c0.github.io/BT-Website/).


### Modules used:

- NEO-6M (GPS module): Uses GPS to get module's current location
- SIM800L (GSM/GPRS module): Publishes location data using PubNub API
- Raspberry Pi Pico (Microcontroller): Controls other two modules


### Wiring Diagram

![Drawing Diagram](/img/wiring_diagram.png)


### Working

![Working Diagram](/img/working.png)


### NOTE

- You need to upload Micropython firmware to Raspberry Pi Pico. Click [here](https://projects.raspberrypi.org/en/projects/getting-started-with-the-pico/3)


### How to setup this project?

1. Install this [extension](https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go).
2. Open the project's `scripts` folder in VS Code
3. Open command pallete by pressing `Ctrl+Shift+P`
4. Type and run this command. `Configure Project`
5. Update keys in Pubnub publish and subscribe keys in `scripts\config.json`


### Uploading and Running Code

- Uploading Code 
   1. Connect Raspberry Pi Pico to your computer using a USB cable
   2. Open command pallete by pressing `Ctrl+Shift+P` and Run `Upload project to Pico` command.

- Running Code
   1. Open command pallete by pressing `Ctrl+Shift+P` and Run `Reset > Soft(Listen)` command.


### Files Used

1. [micropyGPS](https://github.com/inmcm/micropyGPS/blob/master/micropyGPS.py)
2. [SIM800l Driver](https://github.com/pythings/Drivers/blob/master/SIM800L.py)
