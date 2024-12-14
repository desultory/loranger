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
    client = LoRanger(console=console, baud=baud, logger=logger, read_timeout=1)

    while True:
        try:
            if data := client.read_data():
                data = data.split(":")
                if data[0] == "h":
                    hostname = data[1]
                    print(f"Received hello from: {hostname}")
        except KeyboardInterrupt:
            break
