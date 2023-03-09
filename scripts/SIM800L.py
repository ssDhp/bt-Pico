"""
Modified SIM800L Driver 
Original File: https://github.com/pythings/Drivers/blob/master/SIM800L.py
"""

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

    def __init__(self, uart=None, MODEM_RST_PIN=None):

        # Reset pin
        self.MODEM_RST_PIN = MODEM_RST_PIN

        # Uart
        self.uart = uart

        self.initialized = False
        self.modem_info = None

    # ----------------------
    #  Modem initializer
    # ----------------------

    def initialize(self):

        if not self.uart:
            from machine import Pin

            # Pin initialization
            MODEM_RST_PIN_OBJ = Pin(self.MODEM_RST_PIN, Pin.OUT) if self.MODEM_RST_PIN else None

            # Setup reset pin
            if MODEM_RST_PIN_OBJ:
                print("Set pin high")
                MODEM_RST_PIN_OBJ.high()

        # Test AT commands
        retries = 0
        while True:
            try:
                self.modem_info = self.execute_at_command('modeminfo')
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
        self.ssl_available = self.execute_at_command('checkssl') == '+CIPSSL: (0-1)'

    # ----------------------
    # Execute AT commands
    # ----------------------

    def execute_at_command(self, command, data=None, clean_output=True):

        # Commands dictionary. Not the best approach ever, but works nicely.
        commands = {
            'modeminfo':  {'string': 'ATI', 'timeout': 10, 'end': 'OK'},
            'fwrevision': {'string': 'AT+CGMR', 'timeout': 3, 'end': 'OK'},
            'battery':    {'string': 'AT+CBC', 'timeout': 3, 'end': 'OK'},
            'scan':       {'string': 'AT+COPS=?', 'timeout': 60, 'end': 'OK'},
            'network':    {'string': 'AT+COPS?', 'timeout': 3, 'end': 'OK'},
            'signal':     {'string': 'AT+CSQ', 'timeout': 3, 'end': 'OK'},
            'checkreg':   {'string': 'AT+CREG?', 'timeout': 3, 'end': None},
            'setapn':     {'string': 'AT+SAPBR=3,1,"APN","{}"'.format(data), 'timeout': 3, 'end': 'OK'},
            'setuser':    {'string': 'AT+SAPBR=3,1,"USER","{}"'.format(data), 'timeout': 3, 'end': 'OK'},
            'setpwd':     {'string': 'AT+SAPBR=3,1,"PWD","{}"'.format(data), 'timeout': 3, 'end': 'OK'},
            'initgprs':   {'string': 'AT+SAPBR=3,1,"Contype","GPRS"', 'timeout': 3, 'end': 'OK'},  # Appeared on hologram net here or below
            'opengprs':   {'string': 'AT+SAPBR=1,1', 'timeout': 3, 'end': 'OK'},
            'getbear':    {'string': 'AT+SAPBR=2,1', 'timeout': 30, 'end': 'OK'},
            'inithttp':   {'string': 'AT+HTTPINIT', 'timeout': 3, 'end': 'OK'},
            'sethttp':    {'string': 'AT+HTTPPARA="CID",1', 'timeout': 3, 'end': 'OK'},
            'checkssl':   {'string': 'AT+CIPSSL=?', 'timeout': 3, 'end': 'OK'},
            'enablessl':  {'string': 'AT+HTTPSSL=1', 'timeout': 3, 'end': 'OK'},
            'disablessl': {'string': 'AT+HTTPSSL=0', 'timeout': 3, 'end': 'OK'},
            'initurl':    {'string': 'AT+HTTPPARA="URL","{}"'.format(data), 'timeout': 3, 'end': 'OK'},
            'doget':      {'string': 'AT+HTTPACTION=0', 'timeout': 30, 'end': '+HTTPACTION'},
            'setcontent': {'string': 'AT+HTTPPARA="CONTENT","{}"'.format(data), 'timeout': 3, 'end': 'OK'},
            'postlen':    {'string': 'AT+HTTPDATA={},5000'.format(data), 'timeout': 3, 'end': 'DOWNLOAD'},  # "data" is data_lenght in this context, while 5000 is the timeout
            'dumpdata':   {'string': data, 'timeout': 1, 'end': 'OK'},
            'dopost':     {'string': 'AT+HTTPACTION=1', 'timeout': 3, 'end': '+HTTPACTION'},
            'getdata':    {'string': 'AT+HTTPREAD', 'timeout': 30, 'end': 'OK'},
            'closehttp':  {'string': 'AT+HTTPTERM', 'timeout': 3, 'end': 'OK'},
            'closebear':  {'string': 'AT+SAPBR=0,1', 'timeout': 3, 'end': 'OK'}
        }

        # References:
        # https://github.com/olablt/micropython-sim800/blob/4d181f0c5d678143801d191fdd8a60996211ef03/app_sim.py
        # https://arduino.stackexchange.com/questions/23878/what-is-the-proper-way-to-send-data-through-http-using-sim908
        # https://stackoverflow.com/questions/35781962/post-api-rest-with-at-commands-sim800
        # https://arduino.stackexchange.com/questions/34901/http-post-request-in-json-format-using-sim900-module (full post example)

        # Sanity checks
        if command not in commands:
            raise Exception('Unknown command "{}"'.format(command))

        # Support vars
        command_string = commands[command]['string']
        excpected_end = commands[command]['end']
        timeout = commands[command]['timeout']
        processed_lines = 0

        # Execute the AT command
        command_string_for_at = "{}\r\n".format(command_string)
        self.uart.write(command_string_for_at)

        # Support vars
        pre_end = True
        output = ''
        empty_reads = 0

        while True:

            line = self.uart.readline()
            if not line:
                time.sleep(1)
                empty_reads += 1
                if empty_reads > timeout:
                    raise Exception('Timeout for command "{}" (timeout={})'.format(command, timeout))
            else:

                # Convert line to string
                line_str = line.decode('utf-8')

                # Do we have an error?
                if line_str == 'ERROR\r\n':
                    raise GenericATError('Got generic AT error')

                # If we had a pre-end, do we have the expected end?
                if line_str == '{}\r\n'.format(excpected_end):
                    break
                if pre_end and line_str.startswith('{}'.format(excpected_end)):
                    output += line_str
                    break

                # Do we have a pre-end?
                if line_str == '\r\n':
                    pre_end = True
                else:
                    pre_end = False

                # Keep track of processed lines and stop if exceeded
                processed_lines += 1

                # Save this line unless in particular conditions
                if command == 'getdata' and line_str.startswith('+HTTPREAD:'):
                    pass
                else:
                    output += line_str

        # Remove the command string from the output
        output = output.replace(command_string+'\r\r\n', '')

        # ..and remove the last \r\n added by the AT protocol
        if output.endswith('\r\n'):
            output = output[:-2]

        # Also, clean output if needed
        if clean_output:
            output = output.replace('\r', '')
            output = output.replace('\n\n', '')
            if output.startswith('\n'):
                output = output[1:]
            if output.endswith('\n'):
                output = output[:-1]

        # Return
        return output

    # ----------------------
    #  Function commands
    # ----------------------

    def get_info(self):
        output = self.execute_at_command('modeminfo')
        return output

    def battery_status(self):
        output = self.execute_at_command('battery')
        battChargeStatus, battLevel, battVoltage = output.split(":")[1].split(",")
        # Map values to battery charge state
        if int(battChargeStatus) == 0:
            battChargeStatus = "Not charging"
        elif int(battChargeStatus) == 1:
            battChargeStatus = "Charging"
        elif int(battChargeStatus) == 2:
            battChargeStatus = "Finished charging"
        else:
            battChargeStatus = "Power fault"

        # More conversions
        battLevel = f"{battLevel}%"
        battVoltage = f"{int(battVoltage)/1000}V"
        return battChargeStatus, battLevel, battVoltage

    def scan_networks(self):
        networks = []
        output = self.execute_at_command('scan')
        pieces = output.split('(', 1)[1].split(')')
        for piece in pieces:
            piece = piece.replace(',(', '')
            subpieces = piece.split(',')
            if len(subpieces) != 4:
                continue
            networks.append({'name': json.loads(subpieces[1]), 'shortname': json.loads(subpieces[2]), 'id': json.loads(subpieces[3])})
        return networks

    def get_current_network(self):
        output = self.execute_at_command('network')
        network = output.split(',')[-1]
        if network.startswith('"'):
            network = network[1:]
        if network.endswith('"'):
            network = network[:-1]
        # If after filtering we did not filter anything: there was no network
        if network.startswith('+COPS'):
            return None
        return network

    def get_signal_strength(self):
        # See more at https://m2msupport.net/m2msupport/atcsq-signal-quality/
        output = self.execute_at_command('signal')
        signal = int(output.split(':')[1].split(',')[0])
        signal_ratio = float(signal)*100/float(30) if signal != 99 else 99  # 30 is the maximum value (2 is the minimum)
        rxQual = int(output.split(':')[1].split(',')[1])  # Channel bit error rate
        # RxQual to BER conversion
        if rxQual == 0:
            ber = "BER < 0.2%"
        elif rxQual == 1:
            ber = "0.2% < BER < 0.4%"
        elif rxQual == 2:
            ber = "0.4% < BER < 0.8%"
        elif rxQual == 3:
            ber = "0.8% < BER < 1.6%"
        elif rxQual == 4:
            ber = "1.6% < BER < 3.2%"
        elif rxQual == 5:
            ber = "3.2% < BER < 6.4%"
        elif rxQual == 6:
            ber = "6.4% < BER < 12.8%"
        elif rxQual == 7:
            ber = "12.8% < BER"
        else:
            ber = f"99"
        return signal_ratio, ber

    def get_ip_addr(self):
        output = self.execute_at_command('getbear')
        output = output.split('+')[-1]  # Remove potential leftovers in the buffer before the "+SAPBR:" response
        pieces = output.split(',')
        if len(pieces) != 3:
            raise Exception('Cannot parse "{}" to get an IP address'.format(output))
        ip_addr = pieces[2].replace('"', '')
        if len(ip_addr.split('.')) != 4:
            raise Exception('Cannot parse "{}" to get an IP address'.format(output))
        if ip_addr == '0.0.0.0':
            return None
        return ip_addr

    def connect(self, apn, user='', pwd=''):
        if not self.initialized:
            raise Exception('Modem is not initialized, cannot connect')

        # Are we already connected?
        if self.get_ip_addr():
            return

        # Closing bearer if left opened from a previous connect gone wrong:
        try:
            self.execute_at_command('closebear')
        except GenericATError:
            pass

        # First, init gprs
        self.execute_at_command('initgprs')

        # Second, set the APN
        self.execute_at_command('setapn', apn)
        self.execute_at_command('setuser', user)
        self.execute_at_command('setpwd', pwd)

        # Then, open the GPRS connection.
        self.execute_at_command('opengprs')

        # Ok, now wait until we get a valid IP address
        retries = 0
        max_retries = 5
        while True:
            retries += 1
            ip_addr = self.get_ip_addr()
            if not ip_addr:
                retries += 1
                if retries > max_retries:
                    raise Exception('Cannot connect modem as could not get a valid IP address')
                time.sleep(1)
            else:
                break

    def disconnect(self):

        # Close bearer
        try:
            self.execute_at_command('closebear')
        except GenericATError:
            pass

        # Check that we are actually disconnected
        ip_addr = self.get_ip_addr()
        if ip_addr:
            raise Exception('Error, we should be disconnected but we still have an IP address ({})'.format(ip_addr))

    def http_request(self, url, mode='GET', data=None, content_type='application/json'):

        # Protocol check.
        assert url.startswith('http'), 'Unable to handle communication protocol for URL "{}"'.format(url)

        # Are we  connected?
        if not self.get_ip_addr():
            raise Exception('Error, modem is not connected')

        # Close the http context if left open somehow
        try:
            self.execute_at_command('closehttp')
        except GenericATError:
            pass

        # First, init and set http
        self.execute_at_command('inithttp')
        self.execute_at_command('sethttp')

        # Do we have to enable ssl as well?
        if self.ssl_available:
            if url.startswith('https://'):
                self.execute_at_command('enablessl')
            elif url.startswith('http://'):
                self.execute_at_command('disablessl')
        else:
            if url.startswith('https://'):
                raise NotImplementedError("SSL is only supported by firmware revisions >= R14.00")

        # Second, init and execute the request
        self.execute_at_command('initurl', data=url)

        if mode == 'GET':

            output = self.execute_at_command('doget')
            response_status_code = output.split(',')[1]

        elif mode == 'POST':

            self.execute_at_command('setcontent', content_type)

            self.execute_at_command('postlen', len(data))

            self.execute_at_command('dumpdata', data)

            output = self.execute_at_command('dopost')
            response_status_code = output.split(',')[1]

        else:
            raise Exception('Unknown mode "{}'.format(mode))

        # Third, get data
        response_content = self.execute_at_command('getdata', clean_output=False)

        # Then, close the http context
        self.execute_at_command('closehttp')

        return Response(status_code=response_status_code, content=response_content)
