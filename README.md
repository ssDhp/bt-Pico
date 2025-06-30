## bt-Pico - GPS Tracker

### Changelog
1. Updated SIM driver
   - Added support for TCP and UDP connections
2. Updated GPS driver
   - Removed support for NEMA 
   - Added support for UBX protocol

---
![v2 image](/assets/imagev2.jpg)


### Modules used:

- NEO-6M GPS module
- SIM800L GSM/GPRS module
- Raspberry Pi Pico Microcontroller


### Wiring Diagram

![Drawing Diagram](/assets/wiring_diagram.png)


### NOTE

- You need to upload Micropython firmware to Raspberry Pi Pico. Click [here](https://projects.raspberrypi.org/en/projects/getting-started-with-the-pico/3)

### Uploading and Running Code

- Uploading Code 
   1. Connect Raspberry Pi Pico to your computer using a USB cable and Open the project's `code` folder in VS Code
   2. Open command pallete by pressing `Ctrl+Shift+P` and Run `Upload project to Pico` command.

- Running Code
   1. Open command pallete by pressing `Ctrl+Shift+P` and Run `Reset > Soft(Listen)` command.
