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
    {"flags": ["--aux-pin", "-p"], "help": "Auxiliary pin to use", "action": "store", "dest": "aux_pin"},
]


__all__ = ["LoRanger"]
