from zenlib.util import get_kwargs

from loranger import BASE_ARGS, LoRanger


def main():
    args = BASE_ARGS

    kwargs = get_kwargs(package="loranger", description="loranger", arguments=args)
    console = kwargs.pop("console")
    baud = kwargs.pop("baud")
    logger = kwargs.pop("logger")
    loranger = LoRanger(console=console, baud=baud, logger=logger)

    loranger.runloop()
