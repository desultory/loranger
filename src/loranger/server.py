from zenlib.util import get_kwargs

from loranger import BASE_ARGS, LoRanger


def main():
    args = BASE_ARGS
    kwargs = get_kwargs(package="loranger", description="loranger", arguments=args)
    loranger = LoRanger(**kwargs)
    loranger.runloop()
