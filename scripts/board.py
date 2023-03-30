import os
import sys
import ujson
from utime import sleep
from machine import Pin


class pico():
    def __init__(self, data: dict = {}) -> None:
        if not data:
            # Check if config file exists in the root dir
            if "config.json" not in os.listdir():
                print("Config file not found!")
                sys.exit()
            with open("config.json") as fileObj:
                fileContent = ujson.load(fileObj)
        else:
            fileContent = data

        # Set attr from config file
        self.json2Attr(fileContent)

        # Location
        self.lat = 0.0
        self.lng = 0.0
        self.utc = 0.0

        # LED Pin
        self.LED = Pin(25,Pin.OUT)
        # print(self.__dict__) # For testing

    def json2Attr(self, file: dict) -> None:
        """
        Sets attributes from a dict/json
        """

        for key, val in file.items():
            if type(val) is dict:
                setattr(self, key, pico(val))
            else:
                setattr(self, key, val)

    def httpGetUrl(self):
        """
        Returns URL to send location data via HTTP Get request
        """
        channel = f"bus_{self.id.busNo}"
        payload = f"%7B%22lat%22%3A{self.lat}%2C%22lng%22%3A{self.lng}%2C%22utc%22%3A{self.utc}%7D"
        return f"http://ps.pndsn.com/publish/{self.pubnub.pk}/{self.pubnub.sk}/0/{channel}/0/{payload}?uuid={self.id.boardId}"

    def crashUrl(self):
        """
        Returns URL to send crash data via HTTP Get request
        """
        payload = f"%7B%22bus%22%3A%22{self.id.busNo}%22%2C%22lat%22%3A{self.lat}%2C%22lng%22%3A{self.lng}%2C%22utc%22%3A{self.utc}%7D"
        return f"http://ps.pndsn.com/publish/{self.pubnub.pk}/{self.pubnub.sk}/0/crash_notification/0/{payload}?uuid={self.id.boardId}"

    def blinkLed(self, delay:float = 0.1 ) -> None:
        self.LED.toggle()
        sleep(delay*2)
        self.LED.toggle()
        sleep(delay)


if __name__ == "__main__":
    pass
