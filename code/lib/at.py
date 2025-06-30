class ATCommandSyntax:
    """ """

    # Basic syntax
    AT = "AT{cmd}{args}"
    "AT\\<Command\\>\\<Arguments\\>"
    ATAND = "AT&{cmd}{args}"
    "AT&\\<Command\\>\\<Arguments\\>"

    # S Parameter syntax
    ATS = "ATS{register_index}={value}"
    "ATS\\<Index of S register\\>=[Optional value to assign]"

    # Extended syntax
    ATPLUS_TEST = "AT+{cmd}=?"
    "AT+\\<Command\\>=?"
    ATPLUS_READ = "AT+{cmd}?"
    "AT+\\<Command\\>?"
    ATPLUS_WRITE = "AT+{cmd}={args}"
    "AT+\\<Command\\>=\\<Arguments\\>"
    ATPLUS_EXECUTE = "AT+{cmd}"
    "AT+\\<Command\\>"

    # Custom syntax
    NO_SYNTAX = "{cmd}"
    "\\<Command\\>"


class ATCommandError(Exception):
    """
    Custom Error Class
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ATCommandErrorTimeout(ATCommandError):
    """
    Custom Error Class
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ATCommand:
    def __init__(
        self,
        at_command_str: str,
        *args: object,
        at_command_syntax: str = ATCommandSyntax.NO_SYNTAX,
        expected_end_str: str = "OK",
    ) -> None:

        self.at_command_syntax = at_command_syntax
        self.at_command_str = at_command_str
        self.expected_end_str = expected_end_str
        self.args = args
        self.concatenated_args = ""

        if (
            self.at_command_syntax == ATCommandSyntax.ATPLUS_TEST
            or self.at_command_syntax == ATCommandSyntax.ATPLUS_READ
            or self.at_command_syntax == ATCommandSyntax.ATPLUS_EXECUTE
            or self.at_command_syntax == ATCommandSyntax.NO_SYNTAX
        ):
            assert len(self.args) == 0
            self.formatted_command_str = self.at_command_syntax.format(
                cmd=self.at_command_str
            )

        else:
            assert len(self.args) != 0

            for arg in self.args:
                self.concatenated_args += f"{arg},"

            self.concatenated_args = self.concatenated_args.rstrip(",")

            if self.at_command_syntax == ATCommandSyntax.ATS:
                assert len(self.args) == 1
                self.formatted_command_str = self.at_command_syntax.format(
                    register_index=self.at_command_str, value=self.concatenated_args
                )
            else:
                self.formatted_command_str = self.at_command_syntax.format(
                    cmd=self.at_command_str, args=self.concatenated_args
                )

    def __repr__(self) -> str:
        return f"ATCommand({repr(self.at_command_syntax)}, {repr(self.at_command_str)}, {repr(self.expected_end_str)}, {repr(self.args)})"

    def __str__(self) -> str:
        return self.formatted_command_str


HTTP_CODES = {
    "100": "Continue",
    "101": "Switching Protocols",
    "200": "OK",
    "201": "Created",
    "202": "Accepted",
    "203": "Non-Authoritative Information",
    "204": "No Content",
    "205": "Reset Content",
    "206": "Partial Content",
    "300": "Multiple Choices",
    "301": "Moved Permanently",
    "302": "Found",
    "303": "See Other",
    "304": "Not Modified",
    "305": "Use Proxy",
    "307": "Temporary Redirect",
    "400": "Bad Request",
    "401": "Unauthorized",
    "402": "Payment Required",
    "403": "Forbidden",
    "404": "Not Found",
    "405": "Method Not Allowed",
    "406": "Not Acceptable",
    "407": "Proxy Authentication Required",
    "408": "Request Time-out",
    "409": "Conflict",
    "410": "Gone",
    "411": "Length Required",
    "412": "Precondition Failed",
    "413": "Request Entity Too Large",
    "414": "Request-URI Too Large",
    "415": "Unsupported Media Type",
    "416": "Requested range not satisfiable",
    "417": "Expectation Failed",
    "500": "Internal Server Error",
    "501": "Not Implemented",
    "502": "Bad Gateway",
    "503": "Service Unavailable",
    "504": "Gateway Time-out",
    "505": "HTTP Version not supported",
    "600": "Not HTTP PDU",
    "601": "Network Error",
    "602": "No memory",
    "603": "DNS Error",
    "604": "Stack Busy",
}


class HTTPError(Exception):
    """
    Error class to handle errors caused by bad HTTP requests.
    """

    def __init__(self, response_code: str, description: str = "") -> None:
        super().__init__()
        self.response_code = response_code
        self.description = description

    def __repr__(self) -> str:
        return f"HTTP Error! Response Code: {self.response_code}, {HTTP_CODES.get(self.response_code, self.description)}\n{self.description}"

    def __str__(self) -> str:
        return f"HTTP Error! Response Code: {self.response_code}"


class TCPError(Exception):
    """
    Custom Error Class
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class TCPErrorTimeout(TCPError):
    """
    Custom Error Class
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class UDPError(Exception):
    """
    Custom Error Class
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class UDPErrorTimeout(UDPError):
    """
    Custom Error Class
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


if __name__ == "__main__":
    print("at.py: Running tests...")

    ########

    print("Basic Syntax: ")
    test_cmd11 = ATCommand(ATCommandSyntax.AT, "D", "+911234567890")
    out_str = str(test_cmd11)
    print(f"Test Command: {out_str}")
    assert out_str == "ATD+911234567890"
    out_str = repr(test_cmd11)
    print(f"Repr: {out_str}")
    assert out_str == "ATCommand('AT{cmd}{args}', 'D', 'OK', ('+911234567890',))"

    test_cmd12 = ATCommand(ATCommandSyntax.ATAND, "F", 0)
    out_str = str(test_cmd12)
    print(f"Read Command: {out_str}")
    assert out_str == "AT&F0"
    out_str = repr(test_cmd12)
    print(f"Repr: {out_str}")
    assert out_str == "ATCommand('AT&{cmd}{args}', 'F', 'OK', (0,))"

    print()

    ########

    print("S Parameter syntax: ")
    test_cmd11 = ATCommand(ATCommandSyntax.ATS, "0", "0")
    out_str = str(test_cmd11)
    print(f"Test Command: {out_str}")
    assert out_str == "ATS0=0"
    out_str = repr(test_cmd11)
    print(f"Repr: {out_str}")
    assert out_str == "ATCommand('ATS{register_index}={value}', '0', 'OK', ('0',))"
    print()

    ########

    print("Extended Syntax: ")

    test_cmd31 = ATCommand(ATCommandSyntax.ATPLUS_TEST, "CIPSEND")
    out_str = str(test_cmd31)
    print(f"Test Command: {out_str}")
    assert out_str == "AT+CIPSEND=?"
    out_str = repr(test_cmd31)
    print(f"Repr: {out_str}")
    assert out_str == "ATCommand('AT+{cmd}=?', 'CIPSEND', 'OK', ())"

    test_cmd32 = ATCommand(ATCommandSyntax.ATPLUS_READ, "CIPSEND")
    out_str = str(test_cmd32)
    print(f"Read Command: {out_str}")
    assert out_str == "AT+CIPSEND?"
    out_str = repr(test_cmd32)
    print(f"Repr: {out_str}")
    assert out_str == "ATCommand('AT+{cmd}?', 'CIPSEND', 'OK', ())"

    test_cmd33 = ATCommand(ATCommandSyntax.ATPLUS_WRITE, "CIPSEND", 16)
    out_str = str(test_cmd33)
    print(f"Write Command: {out_str}")
    assert out_str == "AT+CIPSEND=16"
    out_str = repr(test_cmd33)
    print(f"Repr: {out_str}")
    assert out_str == "ATCommand('AT+{cmd}={args}', 'CIPSEND', 'OK', (16,))"

    test_cmd34 = ATCommand(ATCommandSyntax.ATPLUS_EXECUTE, "CIPSEND")
    out_str = str(test_cmd34)
    print(f"Write Command: {out_str}")
    assert out_str == "AT+CIPSEND"
    out_str = repr(test_cmd34)
    print(f"Repr: {out_str}")
    assert out_str == "ATCommand('AT+{cmd}', 'CIPSEND', 'OK', ())"
    print()

    ########

    print("Custom syntax: ")

    test_cmd11 = ATCommand(ATCommandSyntax.NO_SYNTAX, "A/")
    out_str = str(test_cmd11)
    print(f"Test Command: {out_str}")
    assert out_str == "A/"
    out_str = repr(test_cmd11)
    print(f"Repr: {out_str}")
    assert out_str == "ATCommand('{cmd}', 'A/', 'OK', ())"
    print()
