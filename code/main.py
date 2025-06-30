import logger
import device_config

import ubx
import utils
import NEO6M

import at
import SIM800L

import os
import sys
import json
import time
import machine

def setup_gps_module(gps_module: NEO6M.NEO6M, logger: logger.Logger):
    logger.info("Disabling all NMEA messages for Serial1...", end="")
    for msg_type in NEO6M.NEO6M.NMEA_MSG_CLSID:
        msg = ubx.UBXMessage(
            ubx.UBXMessageTypes.CFG_MSG,
            2 * ubx.UBXDataTypes.U1 + 1 * ubx.UBXDataTypes.U1,
            msg_type,
            b"\x00",
        )

        response_status, _ = gps_module.send_UBX_message(msg)
        if not response_status:
            logger.warning(f"[WARNING] Unable to disable NEMA '{msg_type}' message")
    logger.info("Done.")


def setup_sim_module(sim_module: SIM800L.SIM800L, logger: logger.Logger):

    logger.info("Resetting SIM Module...", end="")
    sim_module.reset_module ()
    logger.info("Done.")
    logger.info("Initializing SIM Module...", end="")
    sim_module.init_module()
    logger.info("Done.")

    # Check if SIM is inserted in the module
    if not sim_module.get_sim_status():
        raise SIM800L.SIM800LError("SIM NOT detected! Insert a SIM card in the module.")
    pass


if __name__ == "__main__":
    try:
        # If last reset was caused by a crash, enable logging to file
        if machine.reset_cause() != machine.PWRON_RESET and 'CRASH.txt' in os.listdir():    
            logger = logger.Logger(logger.Logger.LOG_ALL, "./LOG.txt")
        else:
            logger = logger.Logger(logger.Logger.LOG_ALL)

        config =  device_config.DeviceConfig("./config.json")
        gps_module = NEO6M.NEO6M(config.GPS_module_config, logger)
        logger.info(f"GPS Module Config: {gps_module.module_UART_config}")
        sim_module = SIM800L.SIM800L(config.SIM_module_config, logger)
        logger.info(f"SIM Module Config: {sim_module.module_UART_config}")

        # Setup module according to the config
        setup_gps_module(gps_module, logger)
        setup_sim_module(sim_module, logger)

        logger.info("Waiting for SIM800L to register...", end="")
        while not sim_module.is_registered():
            time.sleep_ms(100)
        logger.info("Done.")

        logger.info("Opening GPRS context...", end="")
        sim_module.GPRS_context_open()
        logger.info("Done.")
        logger.info(f"SIM INFO: {sim_module.get_module_info()}")
        logger.info(f"SIM Operator: {sim_module.get_sim_operator()}")
        logger.info(f"RSSI, BER: {sim_module.get_signal_quality()}")

        logger.info("Waiting for GPS fix....", end="")
        while True:
            _, gps_fix, _, _, _, ttff, msss = gps_module.poll_nav_status()
            if gps_fix == 2 or gps_fix == 3 or gps_fix == 4:
                logger.info(f"GPS fix type: {NEO6M.NEO6M.GPS_FIX_TYPES[gps_fix]}")
                logger.info(f"Time to first fix: {ttff} ms")
                logger.info(f"Time since startup/reset: {msss} ms")
                break
            time.sleep_ms(100)
        logger.info("Done.")
        
        logger.info("Opening HTTP session...", end="")
        sim_module.HTTP_session_open(enable_redirects=False)
        logger.info("Done.")

        # Main Loop
        
        # Example: HTTP POST request json data example
        # See ./lib/SIM800L.py for HTTP GET, HTTP POST, TCP and UDP examples 
        NPOST = 0
        TEST_URL_POST = "https://httpbin.org/post"
        POST_total_time_taken_ms = 0
        try:
            while True:
                # Poll GPS module
                _, long, lat, height, hMSL, hAcc, vAcc = gps_module.poll_nav_posllh()
                lat = lat*(10**-7)
                long = long*(10**-7)
                height = height/1000
                hMSL = hMSL/1000
                hAcc = hAcc/1000
                vAcc = vAcc/1000
                
                logger.info(f"Latitude, Longitude: {lat}, {long}")
                print(f"Height above Ellipsoid: {height} m")
                print(f"Height above mean sea level: {hMSL} m")
                print(f"Accuracy: {hAcc} m, {vAcc} m")

                POST_DATA = {"lat": lat, "long": long, "height": height, "hMSL": hMSL, "hAcc": hAcc, "vAcc": vAcc}
                POST_CONTENT_TYPE = "application/json"
                POST_JSON = json.dumps(POST_DATA)
                
                start_time = time.ticks_ms()
                logger.info(f"[POST] {TEST_URL_POST} ", end="")
                response_code, response = sim_module.HTTP_POST(TEST_URL_POST, POST_JSON, header_content_type=POST_CONTENT_TYPE)
                time_taken_ms = time.ticks_diff(time.ticks_ms(), start_time)
                POST_total_time_taken_ms += time_taken_ms
                logger.info(f"|{response_code}, {at.HTTP_CODES.get(response_code, '')}, {time_taken_ms} ms")
                print(f"Response: \n{response}")
                NPOST += 1
                pass

        except KeyboardInterrupt:
            print(f"Average time taken to make {NPOST} HTTP POST requests: {POST_total_time_taken_ms/NPOST} ms")
            print()
            print("Closing HTTP session...", end="")
            sim_module.HTTP_session_close()
            print("Done.")
            pass

    except Exception as error:
        sys.print_exception(error)
        time.sleep(3)
        with open("./CRASH.txt", "w") as f:
            f.write(f"[CRASH] {error}")
            f.flush()
        machine.reset()
