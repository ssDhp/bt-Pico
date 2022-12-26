## NEMA Sentences

---

Format for a NEMA Sentence

`$Talker ID + Sentence ID + Data`

- Every NMEA sentence begins with a '$' sign.

### Talker ID

- Talker ID is used to identify from which satellite system data is comming from
- It is two characters long. Examples below:
- GP - GPS (USA)
- GL - GLONASS (Russia)
- GI - NavIC/IRNSS (India)
- GN - GNSS  
  **NOTE**: GN is used when cobination of multiple satelitte system is used.

### Sentence ID

- Sentence ID is define what type of sentence it is and what data it contains.
- It is three characters long. Examples beow:
- GGA - Time, position and fix type data
- GLL - Latitude, longitude, UTC time of position fix and status
- GSA - GPS receiver operating mode, satellites used in the position solution, and DOP values

- GSV - Number of GPS satellites in view satellite ID numbers, elevation, azimuth, & SNR values
- RMC - Time, date, position, course and speed data
