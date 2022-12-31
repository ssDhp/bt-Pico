## [WIP] bt-Pico - GPS Tracker

![v2 image](/schematic/v2image.jpg)
GPS Tracker updates its location on the website.

Components used:

-   Raspberry Pi Pico (Microcontroller): Controls other two modules
-   NEO-6M (GPS module): Gets current location
-   SIM800L (GSM/GPRS module): Sends location to the website

![Drawing Diagram](/schematic/Bt-Pico.png)

### Working

![Working Diagram](/schematic/working.png)

### How to setup this project?

1. Install this [extension](https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go).
2. Open the project's scripts folder in VS Code
3. Open command pallete by pressing `Ctrl+Shift+P`
4. Run this command. `Pico-W-Go > Configure Project`
5. Done.

### Hardware Checks

Check LEDs on modules to see if modules are working correctly

1. NEO-6M
    - No blinking - Searching for satellites
    - Blink every 1 second - Position fix found (Module can "see" enough satelittes)
2. SIM800L
    - Blink every 1s - Module is seaching for a network
    - Blink every 2s - Data connection is active
    - Blink every 3s - Module is connected to a network and can receive/send

## NEMA Sentences

Format for a NEMA Sentence

`$Talker ID + Sentence ID + Data`

-   Every NMEA sentence begins with a '$' sign.

### Talker ID

-   Talker ID is used to identify from which satellite system data is comming from
-   It is two characters long. Examples below:
-   GP - GPS (USA)
-   GL - GLONASS (Russia)
-   GI - NavIC/IRNSS (India)
-   GN - GNSS  
    **NOTE**: GN is used when cobination of multiple satelitte system is used.

### Sentence ID

-   Sentence ID is define what type of sentence it is and what data it contains.
-   It is three characters long. Examples beow:
-   GGA - Time, position and fix type data
-   GLL - Latitude, longitude, UTC time of position fix and status
-   GSA - GPS receiver operating mode, satellites used in the position solution, and DOP values

-   GSV - Number of GPS satellites in view satellite ID numbers, elevation, azimuth, & SNR values
-   RMC - Time, date, position, course and speed data
