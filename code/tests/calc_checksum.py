# Test checksum calculation

# Test UBX message:  Disable xxRMC
# b"\xB5\x62\x06\x01\x08\x00\xF0\x04\x00\x00\x00\x00\x00\x01\x04\x40"
from utils import bytes_to_hex_str


def get_checksum(ubx_msg: bytes) -> bytes:
    CK_A = 0x00
    CK_B = 0x00

    for byte in ubx_msg:
        CK_A = CK_A + byte
        CK_A = CK_A & 0xFF
        CK_B = CK_B + CK_A
        CK_B = CK_B & 0xFF

    CK = (CK_A << 8) + CK_B
    return CK.to_bytes(2, "big")


test_ubx_message_bytes = (
    b"\xB5\x62\x06\x01\x08\x00\xF0\x02\x00\x00\x00\x00\x00\x01\x02\x32"
)
# test_ubx_message_bytes = b"\xB5\x62\x06\x01\x08\x00\xF0\x04\x00\x00\x00\x00\x00\x01\x04\x40"
print(f"UBX Message: {bytes_to_hex_str(test_ubx_message_bytes)}")

test_bytes = test_ubx_message_bytes[2:-2]
print(f"Checksum bytes: {bytes_to_hex_str(test_bytes)}")
checksum_bytes = get_checksum(test_bytes)
print(f"Checksum: {bytes_to_hex_str(checksum_bytes)}")
assert checksum_bytes == test_ubx_message_bytes[-2:], "Checksum doesn't match"
