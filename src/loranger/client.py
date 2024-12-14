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
        {"flags": ["-q", "--query"], "help": "Query to perform", "action": "store"},
        {"flags": ["-a", "--action"], "help": "action to perform", "action": "store", "nargs": "*"},
    ]

    kwargs = get_kwargs(package="loranger", description="loranger", arguments=args)
    console = kwargs.pop("console")
    baud = kwargs.pop("baud")
    logger = kwargs.pop("logger")
    query = kwargs.pop("query", None)
    action = kwargs.pop("action", None)

    client = LoRanger(console=console, baud=baud, logger=logger, read_timeout=10)

    if query:
        logger.info(f"Sending query: {query}")
        logger.info(f"[{query}] Got response: {client.run_query(query)}")

    if action:
        action_name = action[0]
        action_args = action[1:]
        logger.info(f"Sending action: {action_name} with args: {action_args}")
        logger.info(f"[{action_name}] Got response: {client.run_action(action_name, action_args)}")


if __name__ == "__main__":
    main()
