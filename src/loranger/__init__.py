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
]


__all__ = ["LoRanger"]
