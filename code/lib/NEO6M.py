import time
import struct
import machine

import ubx
import utils
import logger
import device_config



class NEO6M:

    ENABLED_NMEA_MSG_CLSID = [
        b"\xF0\x00",  # GGA
        b"\xF0\x01",  # GLL
        b"\xF0\x02",  # GSA
        b"\xF0\x03",  # GSV
        b"\xF0\x04",  # RMC
        b"\xF0\x05",  # VTG
    ]
    """All NMEA messages that are enabled by default and transmitted periodically over I/O interface 'Serial1' by NEO-6M"""

    # Unused
    NMEA_MSG_CLSID = [
        # NMEA Standard Messages
        b"\xF0\x0A",  # DTM
        b"\xF0\x09",  # GBS
        b"\xF0\x00",  # GGA
        b"\xF0\x01",  # GGL
        b"\xF0\x06",  # GRS
        b"\xF0\x02",  # GSA
        b"\xF0\x07",  # GST
        b"\xF0\x03",  # GSV
        b"\xF0\x04",  # RMC
        b"\xF0\x05",  # VTG
        b"\xF0\x08",  # ZDA
        # NMEA Proprietary Messages
        b"\xF1\x00",  # UBX, 00,
        b"\xF1\x03",  # UBX, 03,
        b"\xF1\x04",  # UBX, 04
    ]
    """All NMEA messages that can be transmitted by NEO-6M"""

    # Unused
    UBX_MSG_CLSID = [
        b"\x0b\x30",
        b"\x0b\x32",
        b"\x0b\x33",
        b"\x0b\x31",
        b"\x0b\x01",
        b"\x0b\x00",
        b"\x0a\x05",
        b"\x0a\x09",
        b"\x0a\x0b",
        b"\x0a\x02",
        b"\x0a\x06",
        b"\x0a\x07",
        b"\x0a\x21",
        b"\x0a\x08",
        b"\x01\x60",
        b"\x01\x22",
        b"\x01\x31",
        b"\x01\x04",
        b"\x01\x01",
        b"\x01\x02",
        b"\x01\x32",
        b"\x01\x06",
        b"\x01\x03",
        b"\x01\x30",
        b"\x01\x20",
        b"\x01\x21",
        b"\x01\x11",
        b"\x01\x12",
        b"\x02\x20",
        b"\x0d\x03",
        b"\x0d\x01",
        b"\x0d\x06",
    ]
    """All UBX messages that can be transmitted by NEO-6M"""

    GPS_FIX_TYPES = [
        "No Fix",
        "Dead reckoning only",
        "2D fix",
        "3D fix",
        "GPS + DR",
        "Time only fix",
    ]

    class RESET_TYPES:
        HW_RESET = b"\x00"
        SW_RESET = b"\x01"
        SW_RESET_GPS_ONLY = b"\x02"
        HW_RESET_AFTER_SHUTDOWN = b"\x04"
        GPS_START = b"\x08"
        GPS_STOP = b"\x09"

    class RESTART_TYPES:
        COLD = b"\xFF\xFF"
        WARM = b"\x00\x01"
        HOT = b"\x00\x00"

    def __init__(
        self,
        config: device_config.DeviceModuleUART,
        logger: logger.Logger,
        default_baudrate: int = 9600,
    ) -> None:
        self.module_UART_config = config
        self.logger = logger

        self.uart_id = self.module_UART_config.uart_id
        self.tx_pin = machine.Pin(self.module_UART_config.tx)
        self.rx_pin = machine.Pin(self.module_UART_config.rx)

        # Assume the NEO6M is running the default config i.e 9600
        self.baudrate = default_baudrate
        self.UART = machine.UART(
            self.uart_id, self.baudrate, tx=self.tx_pin, rx=self.rx_pin
        )
        # Configure the module to use the specified baudrate
        try:
            self.configure_uart(self.module_UART_config.baudrate)
        # If the default baudrate fails, try the baudrate specified in the config
        except ubx.UBXErrorTimeout:
            self.baudrate = self.module_UART_config.baudrate
            self.UART = machine.UART(
                self.uart_id, self.baudrate, tx=self.tx_pin, rx=self.rx_pin
            )
            self.configure_uart(self.baudrate)



    def send_UBX_message(
        self,
        ubx_message: ubx.UBXMessage,
        read_timeout_ms: int = 1_000,
    ) -> tuple[bool | None, list[bytes]]:

        # Flush Rx buffer to ignore any unread bytes
        if self.UART.any():
            self.logger.warning(f"Rx buffer was NOT empty. Contents flushed: {self.UART.read()}")

        self.UART.write(ubx_message.message_bytes)
        self.UART.flush()

        # Read and wait for response
        rx_buffer = b""  # Temporary buffer for unparsed messages
        parsed_messages = []  # Array of parsed UBX messages
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < read_timeout_ms:
            # Append any unread bytes to rx_buffer
            if self.UART.any():
                rx_buffer += self.UART.read()

            # If rx_buffer is not empty, parse ubx messages
            if len(rx_buffer) >= 2:

                # Find ubx header bytes (0xB5 0x62)
                header_index = rx_buffer.find(b"\xB5\x62")
                if header_index == -1:
                    continue
                else:
                    if header_index != 0:
                        self.logger.warning(f"Expected header bytes, read unexpected bytes; ignoring them. Bytes ignored: {rx_buffer[:header_index]}")
                        rx_buffer = rx_buffer[header_index:]
                        header_index = 0

                    # Wait and read message class, message id and payload length
                    if len(rx_buffer) < 6:
                        continue
                    else:
                        # Read ubx header(2 bytes), message class + message id(1 + 1 = 2 bytes), payload length (little endian 2 bytes)
                        response_header_bytes = rx_buffer[:2]
                        response_class_id_bytes = rx_buffer[2:4]
                        response_payload_length_bytes = rx_buffer[4:6]
                        (response_payload_length,) = struct.unpack(
                            ubx.UBXDataTypes.PAYLOAD_LENGTH,
                            response_payload_length_bytes,
                        )

                        # Wait and read the remaining message i.e payload and 2 bytes checksum
                        if len(rx_buffer) < (2 + 2 + 2) + response_payload_length + 2:
                            continue
                        else:
                            response_payload_start_index = (
                                len(response_header_bytes)  # 2 bytes
                                + len(response_class_id_bytes)  # 2 bytes
                                + len(response_payload_length_bytes)  # 2 bytes
                            )
                            assert response_payload_start_index == 6

                            response_payload_end_index = (
                                response_payload_start_index + response_payload_length
                            )
                            response_payload_bytes = rx_buffer[
                                response_payload_start_index:response_payload_end_index
                            ]
                            response_checksum_bytes = rx_buffer[
                                response_payload_end_index : response_payload_end_index
                                + 2
                            ]

                            response_bytes = (
                                response_header_bytes
                                + response_class_id_bytes
                                + response_payload_length_bytes
                                + response_payload_bytes
                                + response_checksum_bytes
                            )

                            message_size = len(response_bytes)
                            message_end_index = header_index + message_size
                            parsed_message = rx_buffer[header_index:message_end_index]
                            rx_buffer = rx_buffer[message_end_index:]
                            parsed_messages.append(parsed_message)
                            assert parsed_message == response_bytes

                            response_status = None
                            # If the sent UBX message was of message class CFG(0x06)
                            # then it has to acknowledged with a response message of class ACK(0x05)
                            if ubx_message.message_class_id_bytes.startswith(b"\x06"):
                                if (response_class_id_bytes== ubx.UBXMessageTypes.ACK_ACK):
                                    response_status = True
                                    return (response_status, parsed_messages)

                                elif (response_class_id_bytes== ubx.UBXMessageTypes.ACK_NAK):
                                    response_status = False
                                    return (response_status, parsed_messages)

                                else:
                                    # Current message has to poll response
                                    assert (ubx_message.message_class_id_bytes== response_class_id_bytes)
                                    continue

                            else:
                                return (response_status, parsed_messages)

        raise ubx.UBXErrorTimeout(f"Timeout reached! Recieved Bytes: {utils.bytes_to_hex_str(rx_buffer)}")

    def reset_and_restart(
        self, reset_type: bytes, restart_type: bytes, default_baudrate: int = 9600
    ) -> None:

        reset_fmt_str = ubx.UBXDataTypes.X2 + ubx.UBXDataTypes.U1 + ubx.UBXDataTypes.U1

        nav_bbr_mask = restart_type
        reset_mode = reset_type
        reserved_byte = b"\x00"
        payload = nav_bbr_mask + reset_mode + reserved_byte

        message = ubx.UBXMessage(ubx.UBXMessageTypes.CFG_RST, reset_fmt_str, payload)
        message_status, _ = self.send_UBX_message(message)
        assert message_status == True

        # Current config will be lost, if reset was a hardware reset
        # Revert to the default baudrate
        if (
            reset_type == NEO6M.RESET_TYPES.HW_RESET
            or reset_type == NEO6M.RESET_TYPES.HW_RESET_AFTER_SHUTDOWN
        ):
            self.baudrate = default_baudrate
            self.UART = machine.UART(
                self.uart_id, self.baudrate, tx=self.tx_pin, rx=self.rx_pin
            )

            # Wait for the module to recover from hardware reset
            time.sleep_ms(300)  # Arbitrary sleep delay

        # Restore the baudrate specified in the config file
        self.baudrate = self.module_UART_config.baudrate
        self.configure_uart(self.baudrate)

    def reset_sw_restart_cold(self) -> None:
        """Forces GPS only software reset and cold restart. Current configuration will persists after the restart."""
        self.reset_and_restart(
            NEO6M.RESET_TYPES.SW_RESET_GPS_ONLY, NEO6M.RESTART_TYPES.COLD
        )

    def reset_sw_restart_warm(self) -> None:
        """Forces GPS only software reset and warm restart. Current configuration will persists after the restart."""
        self.reset_and_restart(
            NEO6M.RESET_TYPES.SW_RESET_GPS_ONLY, NEO6M.RESTART_TYPES.WARM
        )

    def reset_sw_restart_hot(self) -> None:
        """Forces GPS only software reset and hot restart. Current configuration will persists after the restart."""
        self.reset_and_restart(
            NEO6M.RESET_TYPES.SW_RESET_GPS_ONLY, NEO6M.RESTART_TYPES.HOT
        )

    def configure_uart(
        self,
        baudrate: int | None = None,
        mode: bytes | None = None,
        in_proto_mask: bytes | None = None,
        out_proto_mask: bytes | None = None,
    ) -> None:
        """_summary_

        See Section 31.16.3 of mannual

        Args:
            baudrate (int): _description_
            mode (bytes, optional): _description_. Defaults to b"\x00\x00\x08\xD0".

        Returns:
            bool: _description_
        """

        payload_fields_fmt_str = (
            ubx.UBXDataTypes.U1
            + ubx.UBXDataTypes.U1
            + ubx.UBXDataTypes.X2
            + ubx.UBXDataTypes.X4
            + ubx.UBXDataTypes.U4
            + 2 * ubx.UBXDataTypes.X2
            + 2 * ubx.UBXDataTypes.U2
        )

        # Poll the current config
        polled_mode, polled_baudrate, polled_in_proto_mask, polled_out_proto_mask = (
            self.poll_config_uart()
        )

        port_id = b"\x01"  # Port id for interface Serial1
        tx_ready = b"\x00\x00"  # Always 0

        # Reuse polled config, none is provided
        new_mode = polled_mode if mode is None else mode
        new_baudrate = polled_baudrate if baudrate is None else baudrate
        new_in_proto_mask = (
            polled_in_proto_mask if in_proto_mask is None else in_proto_mask
        )
        new_out_proto_mask = (
            polled_out_proto_mask if out_proto_mask is None else out_proto_mask
        )

        baudrate_fmt_str = ubx.UBXDataTypes.BIG_ENDIAN + ubx.UBXDataTypes.U4
        new_baudrate_bytes = struct.pack(baudrate_fmt_str, new_baudrate)

        # Padding
        reserved0 = b"\x00"
        reserved4 = b"\x00\x00"
        reserved5 = b"\x00\x00"

        config_message = ubx.UBXMessage(
            ubx.UBXMessageTypes.CFG_PRT,
            payload_fields_fmt_str,
            port_id,
            reserved0,
            tx_ready,
            new_mode,
            new_baudrate_bytes,
            new_in_proto_mask,
            new_out_proto_mask,
            reserved4,
            reserved5,
        )

        # This message will be timed out, because budrate will changed if config message is successful
        # No point in waiting for timeout duration, hence the 0ms timeout duration
        try:
            self.send_UBX_message(config_message, 0)

        # Parse response to cofig message with the new baudrate
        except ubx.UBXErrorTimeout:

            # TODO: Add support for non-default 'mode'
            # Reconfigure UART to use the new baudrate
            self.baudrate = new_baudrate
            self.UART = machine.UART(
                self.uart_id, self.baudrate, tx=self.tx_pin, rx=self.rx_pin
            )

            rx_buffer = b""

            while True:
                if self.UART.any():
                    rx_buffer += self.UART.read()

                if len(rx_buffer) >= 10:
                    header_index = rx_buffer.find(b"\xB5\x62")
                    if header_index == -1:
                        continue

                    else:
                        if header_index != 0:
                            self.logger.warning(f"Expected header bytes, read unexpected bytes; ignoring them. Bytes ignored: {rx_buffer[:header_index]}")
                            rx_buffer = rx_buffer[header_index:]
                            header_index = 0

                        response_start_index = header_index
                        response_end_index = header_index + 10
                        response_bytes = rx_buffer[
                            response_start_index:response_end_index
                        ]  # Response to config message

                        if len(rx_buffer) > 10:
                            self.logger.warning(f"Recieved more than expected bytes; ignoring them. Bytes ignored: {rx_buffer[response_end_index:]}")

                        (
                            _,
                            msg_cls_id_bytes,
                            payload_length_bytes,
                            payload_bytes,
                            _,
                        ) = ubx.UBXMessage.split_message_bytes(response_bytes)

                        assert msg_cls_id_bytes == ubx.UBXMessageTypes.ACK_ACK
                        assert payload_length_bytes == b"\x02\x00"
                        assert payload_bytes == config_message.message_class_id_bytes

                        break

        # Poll the new config
        polled_mode, polled_baudrate, polled_in_proto_mask, polled_out_proto_mask = (
            self.poll_config_uart()
        )

        # Check if new config is as expected
        assert new_mode == polled_mode
        assert new_baudrate == polled_baudrate
        assert new_in_proto_mask == polled_in_proto_mask
        assert new_out_proto_mask == polled_out_proto_mask

    def poll_config_uart(self) -> tuple[bytes, int, bytes, bytes]:
        port_id = b"\x01"
        payload_fields_fmt_str = ubx.UBXDataTypes.U1

        poll_config_msg = ubx.UBXMessage(
            ubx.UBXMessageTypes.CFG_PRT, payload_fields_fmt_str, port_id
        )

        response_status, response_messages = self.send_UBX_message(poll_config_msg)
        poll_response = response_messages[0]

        assert response_status == True

        _, message_cls_id_bytes, payload_length_bytes, payload_bytes, _ = (
            ubx.UBXMessage.split_message_bytes(poll_response)
        )

        response_payload_fields_fmt_str = (
            2 * ubx.UBXDataTypes.U1
            + ubx.UBXDataTypes.X2
            + ubx.UBXDataTypes.X4
            + ubx.UBXDataTypes.U4
            + 2 * ubx.UBXDataTypes.X2
            + 2 * ubx.UBXDataTypes.U2
        )

        (payload_length,) = struct.unpack(
            ubx.UBXDataTypes.PAYLOAD_LENGTH, payload_length_bytes
        )
        calculated_payload_length = struct.calcsize(response_payload_fields_fmt_str)

        assert payload_length == calculated_payload_length
        assert message_cls_id_bytes == ubx.UBXMessageTypes.CFG_PRT

        (
            response_port_id,
            _,
            tx_ready_bytes,
            mode_bytes,
            baudrate_bytes,
            in_proto_mask_bytes,
            out_proto_mask_bytes,
            _,
            _,
        ) = utils.split_bytes_fmt(response_payload_fields_fmt_str, payload_bytes)

        assert port_id == response_port_id
        assert tx_ready_bytes == b"\x00\x00"

        (baudrate,) = struct.unpack(ubx.UBXDataTypes.U4, baudrate_bytes)

        return (
            utils.reverse_byte_order(mode_bytes),
            baudrate,
            utils.reverse_byte_order(in_proto_mask_bytes),
            utils.reverse_byte_order(out_proto_mask_bytes),
        )

    def poll_nav_posllh(self) -> tuple[int, int, int, int, int, int, int]:

        poll_message = ubx.UBXMessage(ubx.UBXMessageTypes.NAV_POSLLH, "")

        response_status, response = self.send_UBX_message(poll_message)

        assert response_status == None
        assert len(response) == 1

        payload_fields_fmt_str = (
            ubx.UBXDataTypes.LITTLE_ENDIAN
            + ubx.UBXDataTypes.U4
            + 4 * ubx.UBXDataTypes.I4
            + 2 * ubx.UBXDataTypes.U4
        )

        response_bytes = response[0]
        (
            _,  # Header bytes
            _,  # Message class and id bytes
            _,  # Payload_length_bytes
            payload_bytes,
            _,  # Checksum bytes
        ) = ubx.UBXMessage.split_message_bytes(response_bytes)

        assert struct.calcsize(payload_fields_fmt_str) == len(payload_bytes)

        return struct.unpack(payload_fields_fmt_str, payload_bytes)

    def poll_nav_status(self) -> tuple[int, int, int, int, int, int, int]:
        poll_message = ubx.UBXMessage(ubx.UBXMessageTypes.NAV_STATUS, "")
        response_status, response = self.send_UBX_message(poll_message)

        assert response_status == None
        assert len(response) == 1

        payload_fields_fmt_str = (
            ubx.UBXDataTypes.U4
            + ubx.UBXDataTypes.U1
            + 3 * ubx.UBXDataTypes.X1
            + 2 * ubx.UBXDataTypes.U4
        )

        response_bytes = response[0]
        (
            _,  # Header bytes
            _,  # Message class and id bytes
            _,  # Payload_length_bytes
            payload_bytes,
            _,  # Checksum bytes
        ) = ubx.UBXMessage.split_message_bytes(response_bytes)

        assert struct.calcsize(payload_fields_fmt_str) == len(payload_bytes)

        return struct.unpack(payload_fields_fmt_str, payload_bytes)

    def poll_nav_timeutc(
        self,
    ) -> tuple[int, int, int, int, int, int, int, int, int, int]:
        poll_message = ubx.UBXMessage(ubx.UBXMessageTypes.NAV_TIMEUTC, "")

        response_status, response = self.send_UBX_message(poll_message)

        assert response_status == None
        assert len(response) == 1

        payload_fields_fmt_str = (
            2 * ubx.UBXDataTypes.U4
            + ubx.UBXDataTypes.I4
            + ubx.UBXDataTypes.U2
            + 5 * ubx.UBXDataTypes.U1
            + ubx.UBXDataTypes.X1
        )

        response_bytes = response[0]
        (
            _,  # Header bytes
            _,  # Message class and id bytes
            _,  # Payload_length_bytes
            payload_bytes,
            _,  # Checksum bytes
        ) = ubx.UBXMessage.split_message_bytes(response_bytes)

        assert struct.calcsize(payload_fields_fmt_str) == len(payload_bytes)

        return struct.unpack(payload_fields_fmt_str, payload_bytes)


if __name__ == "__main__":
    print("NEO6M.py: Runing tests...")

    test_config = device_config.DeviceConfig()
    logger = logger.Logger(logger.Logger.LOG_ALL)
    gps_module = NEO6M(test_config.GPS_module_config, logger)

    print("Initialized GPS Module.")
    print(f"Current Config: {gps_module.module_UART_config}")

    gps_module.reset_and_restart(NEO6M.RESET_TYPES.HW_RESET, NEO6M.RESTART_TYPES.COLD)
    print("Forced hardware reset and cold restart.")

    gps_module.reset_sw_restart_cold()
    print("Forced GPS only software reset and cold restart.")

    gps_module.reset_sw_restart_warm()
    print("Forced GPS only software reset and warm restart.")

    gps_module.reset_sw_restart_hot()
    print("Forced GPS only software reset and hot restart.")

    print("Printing NMEA messages...")
    read_timeout_ms = 3_000
    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < read_timeout_ms:
        if gps_module.UART.any():
            print(gps_module.UART.read())

    print("Disabling all NMEA messages for Serial1: ")
    for msg_type in NEO6M.NMEA_MSG_CLSID:
        msg = ubx.UBXMessage(
            ubx.UBXMessageTypes.CFG_MSG,
            2 * ubx.UBXDataTypes.U1 + 1 * ubx.UBXDataTypes.U1,
            msg_type,
            b"\x00",
        )

        response_status, response_messages = gps_module.send_UBX_message(msg)
        if response_status:
            print(f"ACK: {utils.bytes_to_hex_str(msg_type)}")
            pass
        else:
            print(f"NAK: {utils.bytes_to_hex_str(msg_type)}")
            pass

    print("Printing NMEA messages...")
    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < read_timeout_ms:
        if gps_module.UART.any():
            print(gps_module.UART.read())

    print("Testing timeout... ", end="")
    try:
        invalid_message = ubx.UBXMessage(b"\x00\x00", ubx.UBXDataTypes.U1, b"\x00")
        gps_module.send_UBX_message(invalid_message)
    except ubx.UBXErrorTimeout as error:
        print("Success")
    except Exception as error:
        print("Failure")
        print(error)

    print("Polling Serial1 config...")
    mode, baudrate, in_proto_mask, out_proto_mask = gps_module.poll_config_uart()
    mode_hex_str = utils.bytes_to_hex_str(mode)
    in_proto_mask_hex_str = utils.bytes_to_hex_str(in_proto_mask)
    out_proto_mask_hex_str = utils.bytes_to_hex_str(out_proto_mask)
    print(f"Current Config:")
    print(f"Mode: {mode_hex_str}")
    print(f"Baudrate: {baudrate}")
    print(f"Active Input Protocols: {in_proto_mask_hex_str}")
    print(f"Active Output Protocols: {out_proto_mask_hex_str}")
    # Check if config is as expected
    assert mode_hex_str == "0x00 0x00 0x08 0xc0"
    assert baudrate == 115200
    assert in_proto_mask_hex_str == "0x00 0x07"
    assert out_proto_mask_hex_str == "0x00 0x07"

    print("Changing baudrate...")
    gps_module.configure_uart(115200)

    print("Polling Serial1 config...")
    mode, baudrate, in_proto_mask, out_proto_mask = gps_module.poll_config_uart()
    mode_hex_str = utils.bytes_to_hex_str(mode)
    in_proto_mask_hex_str = utils.bytes_to_hex_str(in_proto_mask)
    out_proto_mask_hex_str = utils.bytes_to_hex_str(out_proto_mask)
    print(f"Current Config:")
    print(f"Mode: {mode_hex_str}")
    print(f"Baudrate: {baudrate}")
    print(f"Active Input Protocols: {in_proto_mask_hex_str}")
    print(f"Active Output Protocols: {out_proto_mask_hex_str}")
    # Check if config is as expected
    assert mode_hex_str == "0x00 0x00 0x08 0xc0"
    assert baudrate == 115200
    assert in_proto_mask_hex_str == "0x00 0x07"
    assert out_proto_mask_hex_str == "0x00 0x07"

    # Example: How to send UBX command and parse received data  
    # See Section 31.17 CFG-RATE for more information about UBX-CFG-RATE command
    # Poll the current navigation/measurement rate
    message_fmt_str = 3 * ubx.UBXDataTypes.U2
    message = ubx.UBXMessage(ubx.UBXMessageTypes.CFG_RATE, "")
    response_status, response = gps_module.send_UBX_message(message)
    assert response_status == True

    response_bytes = response[0]
    payload_bytes = ubx.UBXMessage.split_message_bytes(response_bytes)[-2]
    meas_rate_bytes, nav_rate_bytes, time_ref_bytes = utils.split_bytes_fmt(
        message_fmt_str, payload_bytes
    )
    meas_rate, nav_rate, time_ref = struct.unpack(message_fmt_str, payload_bytes)
    print(f"Current mesurement rate: {meas_rate} ms", nav_rate, time_ref)

    # Set higher measurement rate, otherwise the module doesn't respond to multiple consecutive NAV messages quickly
    # This will increase power consumption
    new_meas_rate_ms = 100
    new_meas_rate_ms_bytes = struct.pack(
        ubx.UBXDataTypes.BIG_ENDIAN + ubx.UBXDataTypes.U2, new_meas_rate_ms
    )
    print(f"Setting mesurement rate to {new_meas_rate_ms} ms...")

    message = ubx.UBXMessage(
        ubx.UBXMessageTypes.CFG_RATE,
        message_fmt_str,
        new_meas_rate_ms_bytes,
        nav_rate_bytes,
        time_ref_bytes,
    )
    response_status, response = gps_module.send_UBX_message(message)
    assert response_status == True

    # Poll the new navigation/measurement rate
    message_fmt_str = 3 * ubx.UBXDataTypes.U2
    message = ubx.UBXMessage(ubx.UBXMessageTypes.CFG_RATE, "")
    response_status, response = gps_module.send_UBX_message(message)
    assert response_status == True

    response_bytes = response[0]
    payload_bytes = ubx.UBXMessage.split_message_bytes(response_bytes)[-2]
    meas_rate_bytes, nav_rate_bytes, time_ref_bytes = utils.split_bytes_fmt(
        message_fmt_str, payload_bytes
    )
    (meas_rate,) = struct.unpack(
        ubx.UBXDataTypes.LITTLE_ENDIAN + ubx.UBXDataTypes.U2, meas_rate_bytes
    )
    print(f"New mesurement rate: {meas_rate} ms")

    # Wait for GPS fix
    print("Waiting for GPS fix....")
    while True:
        _, gps_fix, _, _, _, ttff, msss = gps_module.poll_nav_status()
        print(f"GPS fix type: {NEO6M.GPS_FIX_TYPES[gps_fix]}")
        print(f"Time to first fix: {ttff} ms")
        print(f"Time since startup/reset: {msss} ms")
        if gps_fix == 2 or gps_fix == 3 or gps_fix == 4:
            break
        time.sleep_ms(1000)

    # Example: Sync RTC from GPS time
    _, _, _, year, month, day, hour, min, sec, _ = gps_module.poll_nav_timeutc()
    machine.RTC().datetime((year, month, day, 00, hour, min, sec, 00))
    print(f"UTC time: {time.gmtime()}")

    while True:
        start_time = time.ticks_ms()

        _, lon, lat, height, hMSL, hAcc, vAcc = gps_module.poll_nav_posllh()
        print(f"Latitude, Longitude: {lat*(10**-7)}, {lon*(10**-7)}")
        print(f"Height above Ellipsoid: {height/1000} m")
        print(f"Height above mean sea level: {hMSL/1000} m")
        print(f"Accuracy: {hAcc/1000} m, {vAcc/1000} m")

        print(f"[Loop] Time Taken: {time.ticks_diff(time.ticks_ms(), start_time)} ms")


