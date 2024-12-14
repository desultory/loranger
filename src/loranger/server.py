#!/usr/bin/python3

from zenlib.util import get_kwargs

from loranger import LoRanger


def main():
    args = [
        {
            "flags": ["console"],
            "help": "Serial interface to use",
            "action": "store",
            "default": "/dev/ttyUSB0",
            "nargs": "?",
        },
        {"flags": ["--baud", "-b"], "help": "Baud rate to use", "action": "store", "default": "9600"},
    ]

    kwargs = get_kwargs(package="loranger", description="loranger", arguments=args)
    console = kwargs.pop("console")
    baud = kwargs.pop("baud")
    logger = kwargs.pop("logger")
    loranger = LoRanger(console=console, baud=baud, logger=logger)

    loranger.runloop()


if __name__ == "__main__":
    main()
