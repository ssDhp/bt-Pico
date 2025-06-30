import struct

VALID_CHARS = {
    "b",
    "B",
    "h",
    "H",
    "i",
    "I",
    "l",
    "L",
    "q",
    "Q",
    "e",
    "f",
    "d",
    "s",
    "P",
}

BYTE_ORDER_CHARS = {
    "@",
    "<",
    ">",
    "!",
}


def expand_fmt_str(source_fmt_str: str) -> str:
    """Coverts alpha-numerice format string into expanded format strings

    Ex: expand_fmt_str(">2b10H") -> ">bbHHHHHHHHHH"

    Args:
        source_fmt_str (str): Compressed format string

    Raises:
        ValueError: If last character in the format string is numeric.
        ValueError: If unrecognised/unknown character is found in the format string.

    Returns:
        str: Expanded format string
    """

    if type(source_fmt_str) != str:
        raise ValueError(
            f"Expected object of class 'str', recieved argument of type {type(source_fmt_str)}"
        )

    if source_fmt_str[-1].isdigit():
        raise ValueError(f"Invalid format string!")

    expanded_str = ""
    num_str = ""

    for current_index, current_char in enumerate(source_fmt_str):

        if current_index == 0 and current_char in BYTE_ORDER_CHARS:
            expanded_str += current_char

        elif current_char.isdigit():
            num_str += current_char

        elif current_char in VALID_CHARS:
            str_multiplier = 1 if num_str == "" else int(num_str)
            expanded_str += str_multiplier * current_char
            num_str = ""

        else:
            raise ValueError(
                f"Invalid format string! Invalid/Unkown char at index {current_index}"
            )

    return expanded_str


def bytes_to_hex_str(source_bytes: bytes) -> str:
    """Coverts object of class 'bytes' into a formatted string containing hex representation of source bytes

    Ex: bytes_to_hex_str(b'\\x06\\x23\\x55') -> "0x06 0x23 0x55"

    Args:
        source_bytes (bytes): bytes to be converted
        big_endian (bool): Byte order of output string. Defaults to True

    Returns:
        str: string containing hex representaion of source bytes
    """

    if type(source_bytes) != bytes:
        raise ValueError(
            f"Expected object of class 'bytes', recieved argument of type {type(source_bytes)}"
        )

    if source_bytes == b"":
        return ""
    else:
        hex_str_array = [byte_str for byte_str in source_bytes.hex(" ").split(" ")]
        return "".join([f"0x{hex_str} " for hex_str in hex_str_array]).strip()


def split_bytes_fmt(source_fmt_str: str, source_bytes: bytes) -> tuple[bytes, ...]:
    """Splits a 'bytes' object into multiple 'bytes' according to the format string.

    Any byte order characters("@", "<", ">", "!") in the format string are stripped from the output tuple.

    Ex: split_bytes(">2bh", b"\\x23\\x32\\x55\\xAA") -> (b"\\x23", b"\\x32", b"\\x55\\xAA")

    Args:
        source_fmt_str (str): String which describes how to split 'source_bytes' argument.
        source_bytes (bytes): 'bytes' object to be split as described by argument 'source_fmt_str'

    Raises:
        ValueError: If unrecognised/unknown character is found in the format string.

    Returns:
        tuple[bytes, ...]:
    """

    if type(source_bytes) != bytes:
        raise ValueError(
            f"Expected object of class 'bytes', recieved argument of type {type(source_bytes)}"
        )

    expanded_fmt_str = expand_fmt_str(source_fmt_str)

    bytes_index = 0
    bytes_array = []

    for current_char in expanded_fmt_str:
        if current_char == expanded_fmt_str[0] and current_char in BYTE_ORDER_CHARS:
            continue

        elif current_char in VALID_CHARS:
            bytes_size = struct.calcsize(current_char)
            bytes_array.append(source_bytes[bytes_index : bytes_index + bytes_size])
            bytes_index += bytes_size

        else:
            raise ValueError(
                f"Invalid format string! Invalid/Unkown char at index {bytes_index}"
            )

    return tuple(bytes_array)


def reverse_byte_order(source_bytes: bytes) -> bytes:
    """Reverses the byte order of bytes

    Ex: reverse_byte_order(b"\\x55\\xAA") -> b"\\xAA\\x55"

    Args:
        source_bytes (bytes): Bytes to reversed

    Returns:
        bytes: Reversed bytes
    """
    if type(source_bytes) != bytes:
        raise ValueError(
            f"Expected object of class 'bytes', recieved argument of type {type(source_bytes)}"
        )

    reversed_bytes = b""

    current_index = len(source_bytes)
    while current_index >= 0:
        reversed_bytes += source_bytes[current_index : current_index + 1]
        current_index -= 1

    assert len(source_bytes) == len(reversed_bytes)
    return reversed_bytes


if __name__ == "__main__":
    print("utils.py: Running test...")

    compressed_fmt_str = ">2b10H"
    expanded_fmt_str = expand_fmt_str(compressed_fmt_str)
    print(f"Original format string: {compressed_fmt_str}")
    print(f"Expanded format string: {expanded_fmt_str}")
    assert expanded_fmt_str == ">bbHHHHHHHHHH"

    test_bytes = b"\xB5\x65"
    print(f"Bytes default formatting: {test_bytes}")
    print(f"Bytes hex formatting: {test_bytes.hex(' ')}")
    print(f"Bytes hex_str formatting: {bytes_to_hex_str(test_bytes)}")

    original_bytes = b"\x55\xAA"
    reversed_bytes = reverse_byte_order(original_bytes)
    print(f"Orignial bytes: {bytes_to_hex_str(original_bytes)}")
    print(f"Reversed bytes: {bytes_to_hex_str(reversed_bytes)}")
    assert reversed_bytes == b"\xAA\x55"
