import json
from collections import namedtuple


DeviceModuleUART = namedtuple(
    "DeviceModuleUART",
    ["type", "name", "uart_id", "tx", "rx", "reset_pin", "baudrate"],
)


class DeviceConfig:
    def __init__(self, path_to_config: str = "../config.json") -> None:
        try:
            config_file = open(path_to_config, "r")
        except FileNotFoundError:
            raise FileNotFoundError(f"File '{path_to_config}' was not found!")
        else:
            config_json = json.load(config_file)
            config_file.close()

            self.device_name = config_json["device_name"]
            self.firmware_version = config_json["firmware_version"]
            self.hardware_revision = config_json["hardware_revision"]

            self.GPS_module_config = DeviceModuleUART(**config_json["modules"][0])
            assert (
                self.GPS_module_config.type == "GPS"
            ), "Specify GPS module config at index 0 in the modules array in config.json"

            self.SIM_module_config = DeviceModuleUART(**config_json["modules"][1])
            assert (
                self.SIM_module_config.type == "SIM"
            ), "Specify SIM module config at index 1 in the modules array in config.json"

    def __str__(self) -> str:
        device_config_str = f"""
        Name: {self.device_name}
        Firmware Version: {self.hardware_revision}
        Hardware Revision: {self.hardware_revision}
        [GPS] Module: {self.GPS_module_config.name}, Tx: {self.GPS_module_config.tx}, Rx: {self.GPS_module_config.rx}, Baudrate: {self.GPS_module_config.baudrate}
        [SIM] Module: {self.SIM_module_config.name}, Tx: {self.SIM_module_config.tx}, Rx: {self.SIM_module_config.rx}, Reset: {self.SIM_module_config.reset_pin}, Baudrate: {self.SIM_module_config.baudrate}
        """.strip()

        # Hack to de-indent multiline f-string
        return "\n".join(line.strip() for line in device_config_str.splitlines())


if __name__ == "__main__":
    test_config = DeviceConfig()
    print(test_config)
