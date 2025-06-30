import struct
import utils


class UBXMessageTypes:
    """
    UBX message type constants,  Message Class + Message Id
    """

    ACK_ACK = b"\x05\x01"
    ACK_NAK = b"\x05\x01"

    AID_ALM = b"\x0B\x30"
    AID_ALPSRV = b"\x0B\x32"
    AID_ALP = b"\x0B\x50"
    AID_AOP = b"\x0B\x33"
    AID_DATA = b"\x0B\x10"
    AID_EPH = b"\x0B\x31"
    AID_HUI = b"\x0B\x02"
    AID_INI = b"\x0B\x01"
    AID_REQ = b"\x0B\x00"

    CFG_ANT = b"\x06\x13"
    CFG_CFG = b"\x06\x09"
    CFG_DAT = b"\x06\x06"
    CFG_EKF = b"\x06\x12"
    CFG_ESFGWT = b"\x06\x29"
    CFG_FXN = b"\x06\x0E"
    CFG_INF = b"\x06\x02"
    CFG_ITFM = b"\x06\x39"
    CFG_MSG = b"\x06\x01"
    CFG_NAV5 = b"\x06\x24"
    CFG_NAVX5 = b"\x06\x23"
    CFG_NMEA = b"\x06\x17"
    CFG_NVS = b"\x06\x22"
    CFG_PM2 = b"\x06\x3B"
    CFG_PM = b"\x06\x32"
    CFG_PRT = b"\x06\x00"
    CFG_RATE = b"\x06\x08"
    CFG_RINV = b"\x06\x34"
    CFG_RST = b"\x06\x04"
    CFG_RXM = b"\x06\x11"
    CFG_SBAS = b"\x06\x16"
    CFG_TMODE2 = b"\x06\x3D"
    CFG_TMODE = b"\x06\x1D"
    CFG_TP5 = b"\x06\x31"
    CFG_TP = b"\x06\x07"
    CFG_USB = b"\x06\x1B"

    ESF_MEAS = b"\x10\x02"
    ESF_STATUS = b"\x10\x10"

    INF_DEBUG = b"\x04\x04"
    INF_ERROR = b"\x04\x00"
    INF_NOTICE = b"\x04\x02"
    INF_TEST = b"\x04\x03"
    INF_WARNING = b"\x04\x01"

    MON_HW2 = b"\x0A\x0B"
    MON_HW = b"\x0A\x09"
    MON_IO = b"\x0A\x02"
    MON_MSGPP = b"\x0A\x06"
    MON_RXBUFF = b"\x0A\x07"
    MON_RXR = b"\x0A\x21"
    MON_TXBUFF = b"\x0A\x08"
    MON_VER = b"\x0A\x04"

    NAV_AOPSTATUS = b"\x01\x60"
    NAV_CLOCK = b"\x01\x22"
    NAV_DGPS = b"\x01\x31"
    NAV_DOP = b"\x01\x04"
    NAV_EKFSTATUS = b"\x01\x40"
    NAV_POSECEF = b"\x01\x01"
    NAV_POSLLH = b"\x01\x02"
    NAV_SBAS = b"\x01\x32"
    NAV_SOL = b"\x01\x06"
    NAV_STATUS = b"\x01\x03"
    NAV_SVINFO = b"\x01\x30"
    NAV_TIMEGPS = b"\x01\x20"
    NAV_TIMEUTC = b"\x01\x21"
    NAV_VELECEF = b"\x01\x11"
    NAV_VELNED = b"\x01\x12"

    RXM_ALM = b"\x02\x30"
    RXM_EPH = b"\x02\x31"
    RXM_PMREQ = b"\x02\x41"
    RXM_RAW = b"\x02\x10"
    RXM_SFRB = b"\x02\x11"
    RXM_SVSI = b"\x02\x20"

    TIM_SVIN = b"\x0D\x04"
    TIM_TM2 = b"\x0D\x03"
    TIM_TP = b"\x0D\x01"
    TIM_VRFY = b"\x0D\x06"


class UBXDataTypes:
    """
    Source: Section 25.3

    UBX type to Python type conversion table

    U1: 1 Byte, Unsinged Char       -> B
    I1: 1 Byte, Signed Char         -> b
    X1: 1 Byte, Bitfield/Bitmask    -> B, Exact Python datatype doesn't exists

    U2: 2 Bytes Unsinged Short      -> H
    I2: 2 Bytes Signed Short        -> h
    X2: 2 Bytes Bitfield/Bitmask    -> H, Exact Python datatype doesn't exists

    U4: 4 Bytes, Unsinged Long      -> L
    I4: 4 Bytes, Signed Long        -> l
    X4: 4 Bytes, Bitfield/Bitmask   -> L, Exact Python datatype doesn't exists

    R4: 4 bytes, Float              -> f
    R8: 8 bytes, Double             -> d
    CH: 1 byte, ISO 8859.1 Char     -> s, Exact Python datatype doesn't exists
    """

    U1 = "B"
    "1 Byte, Unsigned Char"
    I1 = "b"
    "1 Byte, Signed Char"
    X1 = "B"
    "1 Byte, Bitfield/Bitmask"

    U2 = "H"
    "2 Bytes, Unsigned Short"
    I2 = "h"
    "2 Bytes, Signed Short"
    X2 = "H"
    "2 Bytes, Bitfield/Bitmask"

    U4 = "L"
    "4 Bytes, Unsigned Long"
    I4 = "l"
    "4 Bytes, Signed Long"
    X4 = "L"
    "4 Bytes, Bitfield/Bitmask"

    R8 = "f"
    " 4 bytes, Float"
    R8 = "d"
    "8 bytes, Double"
    CH = "s"
    "1 byte, ISO 8859.1/Latin 1 encoded Char"

    LITTLE_ENDIAN = "<"
    BIG_ENDIAN = ">"

    PAYLOAD_LENGTH = LITTLE_ENDIAN + U2
    "Alias for little endian 2-byte int"


class UBXError(Exception):
    """
    Custom Error Class
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class UBXErrorTimeout(Exception):
    """
    Custom Error Class
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class UBXMessage:
    """
    Structure of of ubx protocol message:
    1. 2-bytes, 0xB5 0x62 Header bytes, All UBX protocol messages start with these 2 bytes
    2. 2-bytes, Message Class and Message ID
    3. 2-bytes, Length of payload field in Litte Endian
    4. n-bytes, Variable length payload field
    5. 2-bytes, Checksum
    """

    _header_bytes = b"\xB5\x62"
    _header_fmt_str = 2 * UBXDataTypes.CH
    _message_class_id_fmt_str = 2 * UBXDataTypes.U1
    _payload_length_fmt_str = UBXDataTypes.LITTLE_ENDIAN + 1 * UBXDataTypes.U2
    _checksum_fmt_str = 2 * UBXDataTypes.U1

    def __init__(
        self,
        ubx_message_type: bytes,
        payload_fields_format_string: str,
        *payload_fields: bytes,
    ) -> None:
        if len(ubx_message_type) != 2:
            raise ValueError(
                "Number of bytes in argument 'ubx_message_type' has to be 2."
            )
        self.message_class_id_bytes = ubx_message_type

        self.payload_fmt_str = UBXDataTypes.LITTLE_ENDIAN + payload_fields_format_string
        self.payload_length = struct.calcsize(self.payload_fmt_str)
        self.payload_length_bytes = struct.pack(
            UBXMessage._payload_length_fmt_str, self.payload_length
        )

        concated_payload_fields = b"".join(payload_fields)
        if self.payload_length != len(concated_payload_fields):
            raise ValueError(
                f"Number of bytes in argument 'payload_fields'({len(concated_payload_fields)}) doesn't match size of argument 'payload_fmt_str'({self.payload_length})"
            )

        payload_expanded_fmt_str = utils.expand_fmt_str(self.payload_fmt_str)
        assert self.payload_length == struct.calcsize(payload_expanded_fmt_str)

        # Array to hold ints which represent payload fields
        payload_fields_array = []
        BYTE_ORDER_CHARS = {"@", "<", ">", "!"}

        # Ignore byte order char if any
        start_index = 1 if payload_expanded_fmt_str[0] in BYTE_ORDER_CHARS else 0
        # Index into concated_payload_field array
        fields_index = 0
        for current_char in payload_expanded_fmt_str[start_index:]:
            # Extract each payload field
            payload_field_size = struct.calcsize(current_char)
            payload_field_bytes = concated_payload_fields[
                fields_index : fields_index + payload_field_size
            ]
            fields_index += payload_field_size

            (payload_field,) = struct.unpack(
                UBXDataTypes.BIG_ENDIAN + current_char, payload_field_bytes
            )
            payload_fields_array.append(payload_field)

        assert fields_index == self.payload_length

        self.payload_bytes = struct.pack(
            self.payload_fmt_str,
            *payload_fields_array,
        )

        # Bytes over which checksum is calculated
        checksum_range = (
            self.message_class_id_bytes + self.payload_length_bytes + self.payload_bytes
        )

        self.checksum_bytes = struct.pack(
            UBXMessage._checksum_fmt_str,
            *list(UBXMessage.calc_checksum(checksum_range)),
        )

        self.message_bytes = (
            UBXMessage._header_bytes
            + self.message_class_id_bytes
            + self.payload_length_bytes
            + self.payload_bytes
            + self.checksum_bytes
        )

    @staticmethod
    def calc_checksum(source_bytes: bytes) -> bytes:
        CK_A = 0x00
        CK_B = 0x00

        # Bytes over which checksum is calculated
        checksum_range = source_bytes

        for message_byte in checksum_range:
            CK_A = CK_A + message_byte
            CK_A = CK_A & 0xFF
            CK_B = CK_B + CK_A
            CK_B = CK_B & 0xFF

        CK = (CK_A << 8) + CK_B
        return CK.to_bytes(2, "big")

    @staticmethod
    def split_message_bytes(
        ubx_message_bytes: bytes,
    ) -> tuple[bytes, bytes, bytes, bytes, bytes]:
        header_bytes = ubx_message_bytes[:2]
        if header_bytes != UBXMessage._header_bytes:
            raise ValueError(
                f"Malformed UBX message. First two bytes of argument 'ubx_message_bytes' have to be 0xB5 0x62. Recieved header bytes: {utils.bytes_to_hex_str(header_bytes)}"
            )

        message_class_id_bytes = ubx_message_bytes[2:4]
        payload_length_bytes = ubx_message_bytes[4:6]
        (payload_length,) = struct.unpack(
            UBXDataTypes.PAYLOAD_LENGTH, payload_length_bytes
        )
        payload_bytes = ubx_message_bytes[6:-2]
        calculated_payload_length = len(payload_bytes)
        if calculated_payload_length != payload_length:
            raise ValueError(
                f"Malformed UBX message. Value in 'length' field({payload_length}) doesn't match calculated size of payload({calculated_payload_length})."
            )

        checksum_bytes = ubx_message_bytes[-2:]
        calculated_checksum_bytes = UBXMessage.calc_checksum(
            message_class_id_bytes + payload_length_bytes + payload_bytes
        )
        if calculated_checksum_bytes != checksum_bytes:
            raise ValueError(
                f"Malformed UBX message. Value of checksum({utils.bytes_to_hex_str(checksum_bytes)}) doesn't match calculated checksum({utils.bytes_to_hex_str(calculated_checksum_bytes)})."
            )

        return (
            header_bytes,
            message_class_id_bytes,
            payload_length_bytes,
            payload_bytes,
            checksum_bytes,
        )


if __name__ == "__main__":
    print("ubx.py: Running tests...")
    test_message = UBXMessage(
        UBXMessageTypes.CFG_MSG,
        2 * UBXDataTypes.U1 + 1 * UBXDataTypes.U1,
        b"\xF0\x0A",
        b"\x00",
    )
    output_str = utils.bytes_to_hex_str(test_message.message_bytes)
    print(f"Message Bytes: {output_str}")
    assert output_str == "0xb5 0x62 0x06 0x01 0x03 0x00 0xf0 0x0a 0x00 0x04 0x23"

    test_message = UBXMessage(
        UBXMessageTypes.CFG_RST,
        1 * UBXDataTypes.X2 + 1 * UBXDataTypes.U1 + 1 * UBXDataTypes.U1,
        b"\x00\x01",
        b"\x02",
        b"\x00",
    )
    output_str = utils.bytes_to_hex_str(test_message.message_bytes)
    print(f"Message Bytes: {output_str}")
    assert output_str == "0xb5 0x62 0x06 0x04 0x04 0x00 0x01 0x00 0x02 0x00 0x11 0x6c"
