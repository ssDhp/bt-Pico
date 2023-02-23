# Imports
import time
import json


class GenericATError(Exception):
    pass


class Response(object):
    def __init__(self, status_code, content):
        self.status_code = int(status_code)
        self.content = content


class Modem(object):
    def __init__(
        self,
        uart=None,
    ):

        # Uart
        self.uart = uart

        self.initialized = False
        self.modem_info = None

    # ----------------------
    #  Modem initializer
    # ----------------------

    def initialize(self):

        # Test AT commands
        retries = 0
        while True:
            try:
                self.modem_info = self.execute_at_command("modeminfo")
            except:
                retries += 1
                if retries < 3:
                    time.sleep(3)
                else:
                    raise
            else:
                break

        # Set initialized flag and support vars
        self.initialized = True

        # Check if SSL is supported
        self.ssl_available = self.execute_at_command("checkssl") == "+CIPSSL: (0-1)"

    # ----------------------
    # Execute AT commands
    # ----------------------
    def execute_at_command(self, command, data=None, clean_output=True):

        # Commands dictionary. Not the best approach ever, but works nicely.
        commands = {
            "modeminfo": {"string": "ATI", "timeout": 3, "end": "OK"},
            "fwrevision": {"string": "AT+CGMR", "timeout": 3, "end": "OK"},
            "battery": {"string": "AT+CBC", "timeout": 3, "end": "OK"},
            "scan": {"string": "AT+COPS=?", "timeout": 3, "end": "OK"},
            "network": {"string": "AT+COPS?", "timeout": 3, "end": "OK"},
            "signal": {"string": "AT+CSQ", "timeout": 3, "end": "OK"},
            "checkreg": {"string": "AT+CREG?", "timeout": 3, "end": None},
            "setapn": {
                "string": f'AT+SAPBR=3,1,"APN","{data}"',
                "timeout": 3,
                "end": "OK",
            },
            "setuser": {
                "string": f'AT+SAPBR=3,1,"USER","{data}"',
                "timeout": 3,
                "end": "OK",
            },
            "setpwd": {
                "string": f'AT+SAPBR=3,1,"PWD","{data}"',
                "timeout": 3,
                "end": "OK",
            },
            "initgprs": {
                "string": 'AT+SAPBR=3,1,"Contype","GPRS"',
                "timeout": 3,
                "end": "OK",
            },  # Appeared on hologram net here or below
            "opengprs": {"string": "AT+SAPBR=1,1", "timeout": 5, "end": "OK"},
            "getbear": {"string": "AT+SAPBR=2,1", "timeout": 3, "end": "OK"},
            "inithttp": {"string": "AT+HTTPINIT", "timeout": 3, "end": "OK"},
            "sethttp": {"string": 'AT+HTTPPARA="CID",1', "timeout": 3, "end": "OK"},
            "checkssl": {"string": "AT+CIPSSL=?", "timeout": 3, "end": "OK"},
            "enablessl": {"string": "AT+HTTPSSL=1", "timeout": 3, "end": "OK"},
            "disablessl": {"string": "AT+HTTPSSL=0", "timeout": 3, "end": "OK"},
            "initurl": {
                "string": f'AT+HTTPPARA="URL","{data}"',
                "timeout": 3,
                "end": "OK",
            },
            "doget": {"string": "AT+HTTPACTION=0", "timeout": 30, "end": "+HTTPACTION"},
            "setcontent": {
                "string": f'AT+HTTPPARA="CONTENT","{data}"',
                "timeout": 3,
                "end": "OK",
            },
            "setuserdata": {
                "string": f'AT+HTTPPARA="USERDATA","{data}"',
                "timeout": 3,
                "end": "OK",
            },
            "postlen": {
                "string": f"AT+HTTPDATA={data},5000",
                "timeout": 3,
                "end": "DOWNLOAD",
            },  # "data" is data_lenght in this context, while 5000 is the timeout
            "dumpdata": {"string": data, "timeout": 1, "end": "OK"},
            "dopost": {
                "string": "AT+HTTPACTION=1",
                "timeout": 30,
                "end": "+HTTPACTION",
            },
            "getdata": {"string": "AT+HTTPREAD", "timeout": 3, "end": "OK"},
            "closehttp": {"string": "AT+HTTPTERM", "timeout": 3, "end": "OK"},
            "closebear": {"string": "AT+SAPBR=0,1", "timeout": 3, "end": "OK"},
        }

        # Sanity checks
        if command not in commands:
            raise Exception(f'Unknown command "{command}"')

        # Support vars
        command_string = commands[command]["string"]
        excpected_end = commands[command]["end"]
        timeout = commands[command]["timeout"]
        processed_lines = 0

        # Execute the AT command
        command_string_for_at = f"{command_string}\r\n"
        self.uart.write(command_string_for_at)

        # Support vars
        pre_end = True
        output = ""
        empty_reads = 0

        while True:

            line = self.uart.readline()
            if not line:
                time.sleep(1)
                empty_reads += 1
                if empty_reads > timeout:
                    raise Exception(
                        f'Timeout for command "{command}" (timeout={timeout})'
                    )
                    # logger.warning('Timeout for command "{}" (timeout={})'.format(command, timeout))
                    # break
            else:
                try:
                    # Convert line to string
                    line_str = line.decode("utf-8")

                    # Do we have an error?
                    if line_str == "ERROR\r\n":
                        raise GenericATError("Got generic AT error")

                    # If we had a pre-end, do we have the expected end?
                    if line_str == f"{excpected_end}\r\n":
                        break
                    if pre_end and line_str.startswith(f"{excpected_end}"):
                        output += line_str
                        break

                    # Do we have a pre-end?
                    if line_str == "\r\n":
                        pre_end = True
                    else:
                        pre_end = False

                    # Keep track of processed lines and stop if exceeded
                    processed_lines += 1

                    # Save this line unless in particular conditions
                    if command == "getdata" and line_str.startswith("+HTTPREAD:"):
                        pass
                    else:
                        output += line_str
                except:
                    return line

        # Remove the command string from the output
        output = output.replace(command_string + "\r\r\n", "")

        # ..and remove the last \r\n added by the AT protocol
        if output.endswith("\r\n"):
            output = output[:-2]

        # Also, clean output if needed
        if clean_output:
            output = output.replace("\r", "")
            output = output.replace("\n\n", "")
            if output.startswith("\n"):
                output = output[1:]
            if output.endswith("\n"):
                output = output[:-1]

        # Return
        return output

    # ----------------------
    #  Function commands
    # ----------------------

    def get_info(self):
        output = self.execute_at_command("modeminfo")
        return output

    def battery_status(self):
        output = self.execute_at_command("battery")
        return output

    def scan_networks(self):
        networks = []
        output = self.execute_at_command("scan")
        pieces = output.split("(", 1)[1].split(")")
        for piece in pieces:
            piece = piece.replace(",(", "")
            subpieces = piece.split(",")
            if len(subpieces) != 4:
                continue
            networks.append(
                {
                    "name": json.loads(subpieces[1]),
                    "shortname": json.loads(subpieces[2]),
                    "id": json.loads(subpieces[3]),
                }
            )
        return networks

    def get_current_network(self):
        output = self.execute_at_command("network")
        network = output.split(",")[-1]
        if network.startswith('"'):
            network = network[1:]
        if network.endswith('"'):
            network = network[:-1]
        # If after filtering we did not filter anything: there was no network
        if network.startswith("+COPS"):
            return None
        return network

    def get_signal_strength(self):
        # See more at https://m2msupport.net/m2msupport/atcsq-signal-quality/
        output = self.execute_at_command("signal")
        signal = int(output.split(":")[1].split(",")[0])
        signal_ratio = float(signal) / float(
            30
        )  # 30 is the maximum value (2 is the minimum)
        return signal_ratio

    def get_ip_addr(self):
        output = self.execute_at_command("getbear")
        if output.startswith("ERROR"):
            raise Exception("Error")

        output = output.split("+")[
            -1
        ]  # Remove potential leftovers in the buffer before the "+SAPBR:" response
        pieces = output.split(",")
        if len(pieces) != 3:
            raise Exception('Cannot parse "{}" to get an IP address'.format(output))
        ip_addr = pieces[2].replace('"', "")
        if len(ip_addr.split(".")) != 4:
            raise Exception('Cannot parse "{}" to get an IP address'.format(output))
        if ip_addr == "0.0.0.0":
            return None
        return ip_addr

    def connect(self, apn, user="", pwd=""):
        if not self.initialized:
            raise Exception("Modem is not initialized, cannot connect")

        # Are we already connected?
        if self.get_ip_addr():
            return

        # Closing bearer if left opened from a previous connect gone wrong:
        try:
            self.execute_at_command("closebear")
        except GenericATError:
            pass

        # First, init gprs
        self.execute_at_command("initgprs")

        # Second, set the APN
        self.execute_at_command("setapn", apn)
        # self.execute_at_command("setuser", user)
        # self.execute_at_command("setpwd", pwd)

        # Then, open the GPRS connection.
        self.execute_at_command("opengprs")

        # Ok, now wait until we get a valid IP address
        retries = 0
        max_retries = 5
        while True:
            retries += 1
            ip_addr = self.get_ip_addr()
            if not ip_addr:
                retries += 1
                if retries > max_retries:
                    raise Exception(
                        "Cannot connect modem as could not get a valid IP address"
                    )
                time.sleep(1)
            else:
                break

    def disconnect(self):

        # Close bearer
        try:
            self.execute_at_command("closebear")
        except GenericATError:
            pass

        # Check that we are actually disconnected
        ip_addr = self.get_ip_addr()
        if ip_addr:
            raise Exception(
                "Error, we should be disconnected but we still have an IP address ({})".format(
                    ip_addr
                )
            )

    def http_request(self, url, mode="GET", data=None, content_type="application/json"):

        # Protocol check.
        assert url.startswith(
            "http"
        ), 'Unable to handle communication protocol for URL "{}"'.format(url)

        # Are we  connected?
        if not self.get_ip_addr():
            raise Exception("Error, modem is not connected")

        # Close the http context if left open somehow
        try:
            self.execute_at_command("closehttp")
        except GenericATError:
            pass

        # First, init and set http
        self.execute_at_command("inithttp")
        self.execute_at_command("sethttp")

        # Do we have to enable ssl as well?
        if self.ssl_available:
            if url.startswith("https://"):
                self.execute_at_command("enablessl")
            elif url.startswith("http://"):
                self.execute_at_command("disablessl")
        else:
            if url.startswith("https://"):
                raise NotImplementedError(
                    "SSL is only supported by firmware revisions >= R14.00"
                )

        # Second, init and execute the request
        self.execute_at_command("initurl", data=url)

        if mode == "GET":

            output = self.execute_at_command("doget")
            response_status_code = output.split(",")[1]

        elif mode == "POST":

            self.execute_at_command(
                "setuserdata",
                "Authorization:Basic cWNnRW9RLnlLZDBtUTpXcm1Rc2ZJOC1OYVhwTWVCTzVXZTA5NG1fN2paTTN3b1UxWXMtQUVmUDdn",
            )

            self.execute_at_command("setcontent", content_type)

            self.execute_at_command("postlen", len(data))

            self.execute_at_command("dumpdata", data)

            output = self.execute_at_command("dopost")
            response_status_code = output.split(",")[1]

        else:
            raise Exception(f'Unknown mode "{mode}"')

        # Third, get data
        response_content = self.execute_at_command("getdata", clean_output=False)

        # Then, close the http context
        self.execute_at_command("closehttp")

        return Response(status_code=response_status_code, content=response_content)


if __name__ == "__main__":
    pass
