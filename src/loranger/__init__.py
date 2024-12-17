from .loranger import LoRanger

BASE_ARGS = [
    {
        "flags": ["console"],
        "help": "Serial interface to use",
        "action": "store",
        "default": "/dev/ttyUSB0",
        "nargs": "?",
    },
    {"flags": ["--baud", "-b"], "help": "Baud rate to use", "action": "store", "default": "9600"},
    {"flags": ["--aux-pin", "-a"], "help": "Auxiliary pin to use", "action": "store", "dest": "aux_pin"},
    {"flags": ["--power-pin", "-p"], "help": "Auxiliary pin to use", "action": "store", "dest": "power_pin"},
    {"flags": {"--m0-pin"}, "help": "M0 pin to use", "action": "store", "dest": "m0_pin"},
    {"flags": {"--m1-pin"}, "help": "M1 pin to use", "action": "store", "dest": "m1_pin"},
]


__all__ = ["LoRanger"]
