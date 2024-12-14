#!/usr/bin/python3

from time import sleep, time

from serial import Serial
from zenlib.logging import loggify

from .queries import Queries
from .actions import Actions


class ActionNotFoundError(Exception):
    def __str__(self):
        return f"Action not found: {self.args[0]}"

class QueryNotFoundError(Exception):
    def __str__(self):
        return f"Query not found: {self.args[0]}"


@loggify
class LoRanger(Queries, Actions):
    """
    h:ello
      h:<hostname> - Announces the hostname of the device
    q:uery
      q:<parameter> - Queries the device for the specified parameter
    a:ction
      a:<action>:<arg1>,<arg2>... - Runs the specified action with the given arguments
    """

    def __init__(self, console: str, baud: int, read_timeout=5, *args, **kwargs):
        self.serial = Serial(port=console, baudrate=baud)
        self.read_timeout = read_timeout  # serial read timeout in s

    def runloop(self):
        """Main loop, runs read_data forever and calls the appropriate action"""
        self.logger.info("Starting main loop")
        self.announce()
        while True:
            if data := self.read_data():
                try:
                    resp = self.handle_data(data)
                    self.logger.info("Prepared response: %s", resp)
                except (ActionNotFoundError, QueryNotFoundError) as e:
                    self.logger.error(e)
                    resp = str(e)
                if resp:
                    self.send_msg(resp)

    def announce(self):
        """Sends an announcement message to the serial port"""
        from os import uname
        self.send_msg(f"h:{uname()[1]}")

    def handle_data(self, data: str):
        """Handles input data, actions will be in the format of "r:action:arg1,arg2..."
        run_action may raise ActionNotFoundError if the action is not defined"""
        self.logger.debug("Handling data: %s", data)
        data = data.split(":")
        if data[0] == "a":
            self.logger.debug("Received action: %s", data)
            action = data[1]
            if args := data[2]:
                arglist = args.split(",")
            else:
                arglist = []
            self.logger.debug("Action: %s, Args: %s", action, arglist)
            return self.handle_action(action, arglist)
        elif data[0] == "q":
            parameter = data[1]
            self.logger.debug("Received query for parameter: %s", parameter)
            return self.handle_query(parameter)
        self.logger.debug("Unknown data: %s", data)

    def send_msg(self, response: str):
        """Sends the message to the serial port"""
        if isinstance(response, list) and not isinstance(response, str):
            response = ",".join(response)
        if not response.endswith("\n"):
            response += "\n"
        response = response.encode()
        self.logger.debug("Sending message: %s", response)
        self.serial.write(response)

    def handle_query(self, parameter: str):
        """Runs the specified query and returns the result"""
        if query := getattr(self, f"query_{parameter}", None):
            self.logger.debug("Running query: %s", parameter)
            return query()
        raise QueryNotFoundError(parameter)

    def handle_action(self, action_name: str, args: list):
        """Runs the specified action with the given arguments
        Raises ActionNotFoundError if the action is not defined"""
        if action := getattr(self, action_name, None):
            self.logger.debug("Running action: %s with args: %s", action_name, args)
            return action(*args)
        raise ActionNotFoundError(action_name)

    def read_data(self):
        """Attempts to read data from the serial port, stops after read_timeout"""
        current_time = time()
        data = b""
        # Loop while the timeout is not reached, or if data is read
        while time() - current_time < self.read_timeout:
            if chunk := self.serial.read_all():
                data += chunk
                current_time = time()
            if data.endswith(b"\n"):
                break
            sleep(0.001)
        # Sanitize first
        data = data.decode().strip()
        if not data:
            return None
        # log and return data if received
        self.logger.debug("Read data: %s", data)
        return data

    def run_query(self, parameter):
        """Runs a query and returns the result"""
        self.send_msg(f"q:{parameter}")
        return self.read_data()

    def run_action(self, action, args):
        """Runs an action with the given arguments"""
        self.send_msg(f"a:{action}:{','.join(args)}")
        return self.read_data()

