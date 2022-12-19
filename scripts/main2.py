from NMEA import NMEAparser

with open("test.bin", "rb") as myfile:
    while newline := myfile.readline():
        my_gps = NMEAparser()
        for x in newline.decode("ASCII"):
            if status := my_gps.update(x):
                print(
                    status,  # type
                    "lat",  # latitude (ddf)
                    my_gps.lat,
                    "lng",  # longitude (ddf)
                    my_gps.lng,
                    "utc time",  # gps packet time
                    my_gps.utc_time,
                    "fix time",  # system time
                    my_gps.fix_time,
                )
