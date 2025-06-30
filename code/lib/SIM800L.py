import time
import json
import machine

import at
import logger
import device_config


class SIM800LError(Exception):
    """
    Custom Error Class
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class SIM800L:
    SUPPORTED_BAUDRATE = {
        0,  # Auto-bauding
        1200,
        2400,
        4800,
        9600,
        19200,
        38400,
        57600,
        115200,
        230400,
        460800,
    }

    def __init__(
        self, 
        config: device_config.DeviceModuleUART,
        logger: logger.Logger,
    ) -> None:

        self.module_UART_config = config
        self.logger = logger

        self.uart_id = self.module_UART_config.uart_id
        self.TX_PIN = machine.Pin(self.module_UART_config.tx)
        self.RX_PIN = machine.Pin(self.module_UART_config.rx)
        self.RST_PIN = machine.Pin(self.module_UART_config.reset_pin, machine.Pin.OUT, machine.Pin.PULL_UP)

        if self.module_UART_config.baudrate in SIM800L.SUPPORTED_BAUDRATE:
            self.baudrate = self.module_UART_config.baudrate
        else:
            raise SIM800LError(f"Unsupported Baudrate: SIM800L doesn't support {self.module_UART_config.baudrate} baudrate! Supported baudrates: {SIM800L.SUPPORTED_BAUDRATE}")

        self.UART = machine.UART(self.uart_id, self.baudrate, tx=self.TX_PIN, rx=self.RX_PIN)

        self._echo_mode = True
        self._line_delimiter_bytes = b"\r\n"
        self._rx_buffer = b""

        self._GPRS_context_status: None | int = None
        self._HTTP_session_status: None | bool = None
        self._TCP_connection_status: None | bool = None
        self._UDP_connection_status: None | bool = None

    def reset_module(self) -> None:
        self.RST_PIN.low()
        time.sleep_ms(200)  # Minimum delay 105 ms
        self.RST_PIN.high()
        time.sleep_ms(3000)  # Minimum delay 2700 ms

    def send_AT_command(
        self,
        at_command: at.ATCommand,
        read_timeout_ms: int = 1_000,
        supress_warning: bool = False,
    ) -> list[str]:

        self.UART.write(f"{at_command.formatted_command_str}\n")
        self.UART.flush()

        rx_buffer = self._rx_buffer
        unexpected_bytes = b""
        start_bytes = self._line_delimiter_bytes
        if self._echo_mode:
            start_bytes = (
                at_command.formatted_command_str.encode("ascii")
                + self._line_delimiter_bytes
            )
        end_bytes = at_command.expected_end_str.encode("ascii")

        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < read_timeout_ms:
            if self.UART.any():
                rx_buffer += self.UART.read()

            if len(rx_buffer) >= len(start_bytes + end_bytes):
                start_bytes_index = rx_buffer.find(start_bytes)

                # If expected start bytes are found
                if start_bytes_index != -1:
                    # Ignore any bytes before expected start bytes
                    if start_bytes_index != 0:
                        ignored_bytes = rx_buffer[:start_bytes_index]
                        unexpected_bytes += ignored_bytes
                        if not supress_warning:
                            self.logger.warning(f"Expected start bytes({start_bytes}), read unexpected bytes; ignoring them. Bytes ignored: {ignored_bytes}")
                        rx_buffer = rx_buffer[start_bytes_index:]
                        start_bytes_index = 0

                    # Module's reponse should be between start_bytes and end_bytes
                    end_bytes_index = rx_buffer.find(end_bytes)
                    if end_bytes_index != -1:
                        # Find the index of delimiter which immediately follows end bytes
                        end_dilimiter_index = rx_buffer.find(self._line_delimiter_bytes, end_bytes_index)
                        response_end_index = end_dilimiter_index + len(self._line_delimiter_bytes)
                        response_bytes = rx_buffer[start_bytes_index:response_end_index]

                        # Remove parsed bytes from the buffer
                        rx_buffer = rx_buffer[response_end_index:]

                        if len(rx_buffer) != 0:
                            unexpected_bytes += rx_buffer
                            self._rx_buffer = unexpected_bytes
                            if not supress_warning:
                                self.logger.warning(f"Incomplete parse: {self._rx_buffer}")
                        else:
                            self._rx_buffer = b""

                        output_lines = []
                        for line_bytes in response_bytes.split(self._line_delimiter_bytes):
                            if line_bytes != b"":
                                output_lines.append(line_bytes.decode())

                        return output_lines
        raise at.ATCommandErrorTimeout(f"Timeout reached! Expected end string({at_command.expected_end_str}) not recieved. Recieved Bytes: {rx_buffer}")

    def init_module(self, echo_mode: bool = False) -> None:
        """
        This method resets the module, makes sures that microcontroller \n
        can interface with the module and returns when the module is \n
        registered to a network. This usually takes 10 seconds but \n
        can take longer.\n
        """

        # Send 'AT' for autobauding to kick in
        response = self.send_AT_command(at.ATCommand("AT"))
        assert response == ["AT", "OK"]

        # URCs(Unsolicited Result Code) are messages sent by the sim module to inform
        # the user of some asynchronous event, such as when the module recieves a phone call
        # See Section 18.3 Summary of Unsolicited Result Codes for the full list of URCs

        # Handling URCs generated at startup/reset
        # Expected URCs(in order): RDY, +CFUN: 1, +CPIN: READY, Call Ready, SMS Ready
        EXPECTED_URCs = ("RDY", "+CFUN: 1", "+CPIN: READY", "Call Ready", "SMS Ready")
        try:
            for urc in EXPECTED_URCs:
                at_command = at.ATCommand("", expected_end_str=urc)
                # supress_warning=True is a hack
                self.send_AT_command(
                    at_command, read_timeout_ms=3_000, supress_warning=True
                )
        except at.ATCommandErrorTimeout as error:
            raise SIM800LError(f"SIM module initialization failed! {error}")

        # Echo mode is enabled by default
        if echo_mode == False:
            self.send_AT_command(at.ATCommand("ATE0"))
            self._echo_mode = False

        # Enable Mobile Equipment(ME) verbose error reporting
        self.send_AT_command(at.ATCommand("AT+CMEE=2"))

    def get_sim_status(self) -> bool:
        """
        Returns True if SIM card is inserted otherwise False
        """
        response = self.send_AT_command(at.ATCommand("AT+CSMINS?"))
        return bool(response[0].split(",")[1])

    def get_registration_code(self) -> int:
        """
        Returns registration code\n
        Registration Codes:\n
        0 - Not registered, Not Searching for new operator\n
        1 - Registered, Home network\n
        2 - Not Registered, Searching for new opertor\n
        3 - Registeration Denied\n
        4 - Unknown\n
        5 - Registered, Roaming\n
        See: https://m2msupport.net/m2msupport/atcreg-network-registration/
        """

        response = self.send_AT_command(at.ATCommand("AT+CREG?"), read_timeout_ms=5_000)
        return int(response[0].split(",")[1])

    def is_registered(self) -> bool:
        registration_code = self.get_registration_code()
        if registration_code == 1 or registration_code == 5:
            return True
        else:
            return False

    def get_module_info(self) -> str:
        """
        Return module's hardware information.\n
        """
        response = self.send_AT_command(at.ATCommand("ATI"))
        return response[0].split(" ")[1]

    def get_sim_operator(self) -> str:
        """
        Returns SIM operator's name
        """
        response = self.send_AT_command(at.ATCommand("AT+COPS?"))
        return response[0].split(",")[2].strip()

    def get_signal_quality(self) -> tuple[str, str]:
        """
        Returns RSSI and BER
        RSSI: 0 - 30 (Higher is better)
        BER: 0 -7 (Lower is better), 99: Not known
        """

        response = self.send_AT_command(at.ATCommand("AT+CSQ"))
        RSSI, BER = response[0].strip().split(":")[1].split(",")
        return RSSI, BER

    def GPRS_context_open(
        self, apn: str = "", user_name: str = "", password: str = ""
    ) -> None:
        """
        Configure bearer settings for bearer profile 1 and opens GPRS context\n
        GPRS is required to access Internet.
        """

        if self._GPRS_context_status is None or self._GPRS_context_status == 0:

            # Set connection type to GPRS
            self.send_AT_command(at.ATCommand('"AT+SAPBR=3,1,"Contype","GPRS"'))

            # Set APN, username and password
            self.send_AT_command(at.ATCommand(f'AT+SAPBR=3,1,"APN", "{apn}"'))
            if user_name != "":
                self.send_AT_command(at.ATCommand(f"AT+SAPBR=3,1,USER,{user_name}"))
            if password != "":
                self.send_AT_command(at.ATCommand(f"AT+SAPBR=3,1,PWD, {password}"))

            # Open GPRS context
            # This sometimes takes longer than usual and cause timeout exception to be raised.
            self.send_AT_command(at.ATCommand("AT+SAPBR=1,1"), read_timeout_ms=30_000)

            # Wait untill module gets assigned a local IP address
            while True:
                response = self.send_AT_command(at.ATCommand("AT+SAPBR=2,1"))
                ip_address = response[0].split(",")[2].strip()
                if ip_address != '"0.0.0.0"':
                    break
            self._GPRS_context_status = 1
        else:
            self.logger.warning("GPRS context is already open.")

    def GPRS_context_close(self) -> None:
        """
        Closes GPRS context for bearer profile 1
        """

        if self._GPRS_context_status == 1:
            self.send_AT_command(at.ATCommand("AT+SAPBR=0,1"))
            self._GPRS_context_status = 0
        else:
            self.logger.warning("GPRS context is already closed.")

    def HTTP_session_open(
        self,
        enable_redirects: bool = True,
        enable_ssl: bool = True,
        request_timeout_sec: int = 30,
    ) -> None:
        """
        Opens HTTP session and configures session settings for bearer pofile 1\n
        """

        if self._HTTP_session_status is None or self._GPRS_context_status == 0:

            # Init HTTP session
            self.send_AT_command(at.ATCommand("AT+HTTPINIT"))

            # Set parameters for HTTP session
            self.send_AT_command(at.ATCommand('AT+HTTPPARA="CID",1'))

            # Enable auto following of redirect request
            if enable_redirects == True:
                self.send_AT_command(at.ATCommand('AT+HTTPPARA="REDIR",1'))

            # Enable SSL
            if enable_ssl == True:
                self.send_AT_command(at.ATCommand("AT+HTTPSSL=1"))

            # Set timeout
            self.send_AT_command(
                at.ATCommand(f'AT+HTTPPARA="TIMEOUT",{request_timeout_sec}')
            )

            self._HTTP_session_status = True
        else:
            self.logger.warning("HTTP session is already open.")

    def HTTP_session_close(self) -> None:
        """
        Closes HTTP session for bearer profile 1
        """
        if self._HTTP_session_status:
            self.send_AT_command(at.ATCommand("AT+HTTPTERM"))
            self._HTTP_session_status = False
        else:
            self.logger.warning("HTTP session is already closed.")

    def HTTP_GET(
        self,
        url: str,
    ) -> tuple[str, str]:
        """
        Make a GET request to a given URL and return response code, response\n
        """

        if not self._HTTP_session_status:
            raise SIM800LError("HTTP session is NOT open. Open HTTP session with '.HTTP_session_open' method before calling this method.")

        # Set URL
        self.send_AT_command(at.ATCommand(f'AT+HTTPPARA="URL","{url}"'))

        # Make GET request
        module_response = self.send_AT_command(
            at.ATCommand("AT+HTTPACTION=0", expected_end_str="+HTTPACTION"),
            read_timeout_ms=30_000,
        )
        _, http_response_code, http_response_length = (
            module_response[-1].split(":")[-1].split(",")
        )

        # Check response code
        if http_response_code.startswith("4") or http_response_code.startswith("5"):
            raise at.HTTPError(http_response_code)

        if http_response_code.startswith("6"):
            raise at.HTTPError(
                http_response_code,
                "6XX netowork errors usually means SIM has a expired data plan",
            )

        # Read response
        module_response = self.send_AT_command(at.ATCommand("AT+HTTPREAD"))
        _, http_response, _ = module_response

        return http_response_code, http_response

    def HTTP_POST(
        self, url: str, data: str, header_content_type="text/plain"
    ) -> tuple[str, str]:
        """
        Make a GET request to a given URL and return response code, response\n
        """

        self.send_AT_command(at.ATCommand(f'AT+HTTPPARA="URL","{url}"'))

        self.send_AT_command(at.ATCommand(f'AT+HTTPPARA="CONTENT","{header_content_type}"'))

        # Set size of data(in bytes) to be send
        # and set maximum timeout(in milliseconds) to send the data to 1_000ms
        self.send_AT_command(at.ATCommand(f"AT+HTTPDATA={len(data)}, 1000", expected_end_str="DOWNLOAD"))

        # Send the data packet
        self.send_AT_command(at.ATCommand(data))

        # Make POST request
        module_response = self.send_AT_command(
            at.ATCommand("AT+HTTPACTION=1", expected_end_str="+HTTPACTION"),
            read_timeout_ms=30_000,
        )

        _, http_response_code, http_response_length = (
            module_response[-1].split(":")[-1].split(",")
        )

        # Check response code
        if http_response_code.startswith("4") or http_response_code.startswith("5"):
            raise at.HTTPError(http_response_code)

        if http_response_code.startswith("6"):
            raise at.HTTPError(
                http_response_code,
                "6XX netowork errors usually means SIM has a expired data plan",
            )

        # Read response
        module_response = self.send_AT_command(at.ATCommand("AT+HTTPREAD"))
        _, http_response, _ = module_response

        return http_response_code, http_response

    def GPRS_get_status(self) -> bool:
        response = self.send_AT_command(at.ATCommand("AT+CGATT?"))
        status = response[0].split(":")[1].strip()
        if status == "1":
            return True
        elif status == "0":
            return False
        else:
            raise SIM800LError(f"Unexpected response! Response: {response}")

    def TCP_connect(self, remote_address: str, remote_port: int) -> None:
        if not self.GPRS_get_status():
            raise SIM800LError("GPRS not attached! Use '.GPRS_context_open' method before calling this method.")

        # Set module to store response from TCP server for mannual retrieval
        self.send_AT_command(at.ATCommand(f"AT+CIPRXGET=1"))

        self.send_AT_command(
            at.ATCommand(
                f'AT+CIPSTART="TCP",{remote_address},{remote_port}',
                expected_end_str="CONNECT OK",
            ),
            read_timeout_ms=3_000,
        )
        self._TCP_connection_status = True

    def TCP_status(self) -> str:
        return self.send_AT_command(
            at.ATCommand("AT+CIPSTATUS", expected_end_str="STATE:")
        )[1]

    def TCP_is_connection_active(self) -> bool:
        if self.TCP_status() == "STATE: CONNECT OK":
            self._TCP_connection_status = True
            return True
        self._TCP_connection_status = False
        return False

    def TCP_send(self, data: str) -> None:
        """
        Sends the string 'data' to the TCP server.\n
        TCP connection remains open after the transmission.\n
        Connection can be automatically closed by the sever after some time or\n
        mannually by calling .TCP_close() method.\n
        """
        if not self.TCP_is_connection_active:
            raise SIM800LError("Connection not active!")

        # This command doesn't end with a normal line delimiter('\r\n') string
        self.send_AT_command(at.ATCommand("AT+CIPSEND", expected_end_str=""), supress_warning=True)
        # This hack clears the rx buffer and prevent any parse errors that may occurs
        assert self._rx_buffer == b"> "
        self._rx_buffer = b""

        # Append CTRL + Z(0x1a) to terminate data and send it
        self.send_AT_command(
            at.ATCommand(data + b"\x1a".decode("ascii"), expected_end_str="SEND OK"),
            read_timeout_ms=3_000,
        )

    def TCP_recieve(
        self,
        timeout_ms: int = 3_000,
    ) -> str:
        rx_buffer = self._rx_buffer

        end_bytes = self._line_delimiter_bytes

        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            if self.UART.any():
                rx_buffer += self.UART.read()

            if len(rx_buffer) > 0:
                lines_bytes = rx_buffer.split(end_bytes)
                for line_bytes in lines_bytes:
                    if line_bytes != b"":
                        if line_bytes.startswith(b"+CIPRXGET: 1"):
                            response = self.send_AT_command(at.ATCommand("AT+CIPRXGET=2,1460")) # Limited to 1460 bytes at a time
                            if len(response) == 3:
                                return response[1]
                            return ""

                        if line_bytes.startswith(b"CLOSED"):
                            self._TCP_connection_status = False
                            raise at.TCPError("TCP connection was closed!")

        raise at.TCPErrorTimeout(f"Timeout reached! Received bytes: {rx_buffer}")

    def TCP_close(self) -> None:
        # Close the TCP connection
        (r1,) = self.send_AT_command(at.ATCommand("AT+CIPCLOSE", expected_end_str="CLOSE OK"))

        # Close GPRS PDP context, because we only support single connection mode
        (r2,) = self.send_AT_command(at.ATCommand("AT+CIPSHUT"))
        if r1 == "CLOSE OK" and r2 == "SHUT OK":
            self._TCP_connection_status = False
        else:
            raise SIM800LError("Error occured when trying to close TCP connection.")

    def UDP_connect(self, remote_address: str, remote_port: int) -> None:
        if not self.GPRS_get_status():
            raise SIM800LError("GPRS not attached! Use '.GPRS_context_open' method before calling this method.")

        # Set module to store response from UDP server for mannual retrieval
        self.send_AT_command(at.ATCommand(f"AT+CIPRXGET=1"))

        self.send_AT_command(
            at.ATCommand(
                f'AT+CIPSTART="UDP",{remote_address},{remote_port}',
                expected_end_str="CONNECT OK",
            ),
            read_timeout_ms=3_000,
        )
        self._UDP_connection_status = True

    def UDP_status(self) -> str:
        return self.send_AT_command(at.ATCommand("AT+CIPSTATUS", expected_end_str="STATE:"))[1]

    def UDP_is_connection_active(self) -> bool:
        if self.UDP_status() == "STATE: CONNECT OK":
            self._UDP_connection_status = True
            return True
        self._UDP_connection_status = False
        return False

    def UDP_send(self, data: str) -> None:
        """
        Sends the string 'data' to the UDP server.\n
        UDP connection remains open after the transmission.\n
        Connection can be automatically closed by the sever after some time or\n
        mannually by calling .UDP_close() method.\n
        """
        if not self.UDP_is_connection_active:
            raise SIM800LError("Connection not active!")

        # This command doesn't end with a normal line delimiter('\r\n') string
        self.send_AT_command(at.ATCommand("AT+CIPSEND", expected_end_str=""), supress_warning=True)
        # This hack clears the rx buffer and prevent any parse errors that may occurs
        assert self._rx_buffer == b"> "
        self._rx_buffer = b""

        # Append CTRL + Z(0x1a) to terminate data and send it
        self.send_AT_command(
            at.ATCommand(data + b"\x1a".decode("ascii"), expected_end_str="SEND OK"),
            read_timeout_ms=3_000,
        )

    def UDP_recieve(
        self,
        timeout_ms: int = 3_000,
    ) -> str:
        rx_buffer = self._rx_buffer

        end_bytes = self._line_delimiter_bytes

        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            if self.UART.any():
                rx_buffer += self.UART.read()

            if len(rx_buffer) > 0:
                lines_bytes = rx_buffer.split(end_bytes)
                for line_bytes in lines_bytes:
                    if line_bytes != b"":
                        if line_bytes.startswith(b"+CIPRXGET: 1"):
                            response = self.send_AT_command(at.ATCommand("AT+CIPRXGET=2,1460")) # Limited to 1460 bytes at a time
                            if len(response) == 3:
                                return response[1]
                            return ""

                        if line_bytes.startswith(b"CLOSED"):
                            self._UDP_connection_status = False
                            raise at.UDPError("UDP connection was closed!")

        raise at.UDPErrorTimeout(f"Timeout reached! Received bytes: {rx_buffer}")

    def UDP_close(self) -> None:
        # Close the UDP connection
        (r1,) = self.send_AT_command(at.ATCommand("AT+CIPCLOSE", expected_end_str="CLOSE OK"))

        # Close GPRS PDP context, because we only support single connection mode
        (r2,) = self.send_AT_command(at.ATCommand("AT+CIPSHUT"))
        if r1 == "CLOSE OK" and r2 == "SHUT OK":
            self._UDP_connection_status = False
        else:
            raise SIM800LError("Error occured when trying to close UDP connection.")


if __name__ == "__main__":
    print("SIM800L: Running tests...")

    test_config = device_config.DeviceConfig()
    logger = logger.Logger(logger.Logger.LOG_ALL)
    sim_module = SIM800L(test_config.SIM_module_config, logger)
    
    print("Resetting SIM Module...", end="")
    sim_module.reset_module()
    print("Done.")
    print("Initializing SIM Module...", end="")
    sim_module.init_module()
    print("Done.")

    # Check if SIM is inserted in the module
    if not sim_module.get_sim_status():
        raise SIM800LError("SIM NOT detected! Insert a SIM card in the module.")

    # Wait for module to register to a network
    print("Waiting for SIM800L to register...", end="")
    while not sim_module.is_registered():
        time.sleep_ms(100)
    print("Done.")

    print("Opening GPRS context...", end="")
    sim_module.GPRS_context_open()
    print("Done.")

    # At this point sim module is ready to send and receive data
    print(f"SIM INFO: {sim_module.get_module_info()}")
    print(f"SIM Operator: {sim_module.get_sim_operator()}")
    print(f"RSSI, BER: {sim_module.get_signal_quality()}")

    # HTTP Examples
    print("Opening HTTP session...", end="")
    # This module supports automatically following redirect requests but it has a bug
    # If the redirect url contains HTML reserved characters they are not translated to correct html entities
    sim_module.HTTP_session_open(enable_redirects=False) 
    print("Done.")

    # Example: HTTP GET request example
    NGET = 3
    TEST_URL_GET = "https://httpbin.org/get"
    GET_total_time_taken_ms = 0
    for _ in range(NGET):
        start_time = time.ticks_ms()
        print(f"[GET] {TEST_URL_GET} ", end="")
        response_code, response = sim_module.HTTP_GET(TEST_URL_GET)
        time_taken_ms = time.ticks_diff(time.ticks_ms(), start_time)
        GET_total_time_taken_ms += time_taken_ms
        print(
            f"|{response_code}, {at.HTTP_CODES.get(response_code, '')}, {time_taken_ms} ms"
        )
        print(f"Response: \n{response}")
    print(f"Average time taken to make {NGET} HTTP GET requests: {GET_total_time_taken_ms/NGET} ms")
    print()

    # Example: HTTP POST request text data example
    NPOST = 3
    TEST_URL_POST = "https://httpbin.org/post"
    POST_total_time_taken_ms = 0

    POST_DATA = "Hello world!"
    for _ in range(NPOST):
        start_time = time.ticks_ms()
        print(f"[POST] {TEST_URL_POST} ", end="")
        response_code, response = sim_module.HTTP_POST(TEST_URL_POST, POST_DATA)
        time_taken_ms = time.ticks_diff(time.ticks_ms(), start_time)
        POST_total_time_taken_ms += time_taken_ms
        print(
            f"|{response_code}, {at.HTTP_CODES.get(response_code, '')}, {time_taken_ms} ms"
        )
        print(f"Response: \n{response}")
    print(f"Average time taken to make {NPOST} HTTP POST requests: {POST_total_time_taken_ms/NPOST} ms")
    print()

    # Example: HTTP POST request json data example
    NPOST = 3
    TEST_URL_POST = "https://httpbin.org/post"
    POST_total_time_taken_ms = 0

    POST_DATA = {"test_data1": "test_value1"}
    POST_CONTENT_TYPE = "application/json"
    import json

    POST_JSON = json.dumps(POST_DATA)

    for _ in range(NPOST):
        start_time = time.ticks_ms()
        print(f"[POST] {TEST_URL_POST} ", end="")
        response_code, response = sim_module.HTTP_POST(
            TEST_URL_POST, POST_JSON, header_content_type=POST_CONTENT_TYPE
        )
        time_taken_ms = time.ticks_diff(time.ticks_ms(), start_time)
        POST_total_time_taken_ms += time_taken_ms
        print(
            f"|{response_code}, {at.HTTP_CODES.get(response_code, '')}, {time_taken_ms} ms"
        )
        print(f"Response: \n{response}")
    print(f"Average time taken to make {NPOST} HTTP POST requests: {POST_total_time_taken_ms/NPOST} ms")
    print()

    print("Closing HTTP session...", end="")
    sim_module.HTTP_session_close()
    print("Done.")

    # TCP example
    NTCP = 3
    TCP_SERVER = "tcp.example.com"  # Domain or IP address
    # TCP_SERVER = "45.79.112.203"
    TCP_SERVER_PORT = 1234
    TCP_DATA = "Hello world!" * 85  # ~ 1kB
    TCP_total_time_taken_ms = 0

    print(f"Opening TCP connection to '{TCP_SERVER}:{TCP_SERVER_PORT}'...", end="")
    sim_module.TCP_connect(TCP_SERVER, TCP_SERVER_PORT)
    print("Done.")
    for _ in range(NTCP):
        start_time = time.ticks_ms()
        print(f"[TCP] SEND {TCP_DATA} ")
        # Server might close the connection for any reason
        # Don't forget to add try/except block
        try:
            sim_module.TCP_send(TCP_DATA)
            # To recieve data from server, then use .TCP_recieve() method
            print(f"[TCP] RECV {sim_module.TCP_recieve()}")
            time_taken_ms = time.ticks_diff(time.ticks_ms(), start_time)
            TCP_total_time_taken_ms += time_taken_ms
        except at.TCPError as error:
            print(error)
            break
    print(f"Average time taken to send {NTCP} TCP packets of size {len(TCP_DATA)} bytes: {TCP_total_time_taken_ms/NTCP} ms")
    print(f"Closing TCP connection...", end="")
    sim_module.TCP_close()
    print("Done.")
    print()

    # UDP example
    NUDP = 3
    UDP_SERVER = "udp.example.com"  # Domain or IP address
    # UDP_SERVER = "45.79.112.203"
    UDP_SERVER_PORT = 1234
    UDP_DATA = "Hello world!" * 85  # ~ 1kB
    UDP_total_time_taken_ms = 0

    print(f"Opening UDP connection to '{UDP_SERVER}:{UDP_SERVER_PORT}'...", end="")
    sim_module.UDP_connect(UDP_SERVER, UDP_SERVER_PORT)
    print("Done.")
    for _ in range(NUDP):
        start_time = time.ticks_ms()
        print(f"[UDP] SEND {UDP_DATA} ")
        # UDP is unreliable which might cause timeouts
        # Don't forget to add try/except block
        try:
            sim_module.UDP_send(UDP_DATA)
            # To recieve data from server, then use .UDP_recieve() method
            print(f"[UDP] RECV {sim_module.UDP_recieve()}")
            time_taken_ms = time.ticks_diff(time.ticks_ms(), start_time)
            UDP_total_time_taken_ms += time_taken_ms
        except at.UDPError as error:
            print(error)
            break
    print(f"Average time taken to send {NUDP} UDP packets of size {len(UDP_DATA)} bytes: {UDP_total_time_taken_ms/NUDP} ms")
    print(f"Closing UDP connection...", end="")
    sim_module.UDP_close()
    print("Done.")
    print()

    print("Closing GPRS context...", end="")
    sim_module.GPRS_context_close()
    print("Done.")
