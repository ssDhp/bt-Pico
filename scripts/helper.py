pub_key = "pub-c-448b0aed-e6f8-4536-a1e4-f235af33663b"
sub_key = "sub-c-10e0e350-30c8-4f8c-84dc-659f6954424e"
busNo = "H"
channel = "bus_" + busNo
callback = "myCallback"
store = 0
uuid = "pico-test"


def getUrl(lat: float, lng: float, utc: float):
    payload = f"%7B%22lat%22%3A%20{lat}%2C%0A%22lng%22%3A%20{lng}%2C%0A%22utc%22%3A%20{utc}%0A%7D"
    return f"http://ps.pndsn.com/publish/{pub_key}/{sub_key}/0/{channel}/{callback}/{payload}?strore={store},uuid={uuid}"
