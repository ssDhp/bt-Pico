import ujson

# environment variable to python object
class envConfig(object):
    def __init__(self, data=None):
        if data is None:
            with open("config.json") as file:
                data = ujson.load(file)
        else:
            data = dict(data)

        for key, val in data.items():
            setattr(self, key, self.compute_attr_value(val))

    def compute_attr_value(self, value):
        if type(value) is list:
            return [self.compute_attr_value(x) for x in value]
        elif type(value) is dict:
            return envConfig(value)
        else:
            return value


# Environment Vraiables
env = envConfig()
channel = "bus_" + env.id.busNo


def getUrl(lat: float, lng: float, utc: float):
    payload = f"%7B%22lat%22%3A%20{lat}%2C%0A%22lng%22%3A%20{lng}%2C%0A%22utc%22%3A%20{utc}%0A%7D"
    return f"http://ps.pndsn.com/publish/{env.pubnub.pk}/{env.pubnub.sk}/0/{channel}/0/{payload}?uuid={env.id.uuid}"
