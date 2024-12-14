from zenlib.util import get_kwargs

from loranger import BASE_ARGS, LoRanger


def main():
    args = BASE_ARGS + [
        {"flags": ["-q", "--query"], "help": "Query to perform", "action": "store"},
        {"flags": ["-a", "--action"], "help": "action to perform", "action": "store", "nargs": "*"},
        {"flags": ["-c", "--command"], "help": "command to perform", "action": "store"},
    ]

    kwargs = get_kwargs(package="loranger", description="loranger", arguments=args)
    console = kwargs.pop("console")
    baud = kwargs.pop("baud")
    logger = kwargs.pop("logger")
    query = kwargs.pop("query", None)
    action = kwargs.pop("action", None)
    command = kwargs.pop("command", None)

    client = LoRanger(console=console, baud=baud, logger=logger, read_timeout=10)

    if query:
        logger.info(f"Sending query: {query}")
        logger.info(f"[{query}] Got response: {client.run_query(query)}")

    if action:
        action_name = action[0]
        action_args = action[1:]
        logger.info(f"Sending action: {action_name} with args: {action_args}")
        logger.info(f"[{action_name}] Got response: {client.run_action(action_name, action_args)}")

    if command:
        logger.info(f"Sending command: {command}")
        logger.info(f"[{command}] Got response:\n{client.run_command(command)}")
