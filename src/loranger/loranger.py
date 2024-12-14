#!/usr/bin/python3

from time import sleep, time

from serial import Serial
from zenlib.logging import loggify

from .actions import Actions
from .queries import Queries


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
    c:ommand
      c:<command> - Runs the specified command on the device
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
        elif data[0] == "c":
            command = data[1]
            self.logger.debug("Received command: %s", command)
            return self.handle_command(command)
        self.logger.debug("Unknown data: %s", data)

    def send_msg(self, response: str):
        """Sends the message to the serial port

        TODO: modules seem to have a limit of 1224 bytes per burst.
        Handling this may require reading the AUX pin to determine when the module is ready to receive more data
        """
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
            self.logger.info("Running query: %s", parameter)
            return query()
        raise QueryNotFoundError(parameter)

    def handle_action(self, action_name: str, args: list):
        """Runs the specified action with the given arguments
        Raises ActionNotFoundError if the action is not defined"""
        if action := getattr(self, action_name, None):
            self.logger.info("Running action: %s with args: %s", action_name, args)
            return action(*args)
        raise ActionNotFoundError(action_name)

    def handle_command(self, command: str):
        """Runs the specified command on the device"""
        from subprocess import TimeoutExpired, run

        self.logger.info("Running command: %s", command)
        arglist = command.split(" ")
        try:
            ret = run(arglist, capture_output=True, timeout=30)
        except TimeoutExpired as e:
            output = e.stdout.decode()
        except FileNotFoundError:
            output = f"Command not found: {command}"
        else:
            output = ret.stdout.decode()
        output += "\x00\x00"

        return output

    def read_data(self, timeout=None, break_char="\n"):
        """Attempts to read data from the serial port, stops after read_timeout"""
        timeout = timeout or self.read_timeout
        current_time = time()
        data = b""
        # Loop while the timeout is not reached, or if data is read
        while time() - current_time < timeout:
            if chunk := self.serial.read_all():
                self.logger.debug("Read chunk: %s", chunk)
                data += chunk
                current_time = time()
            if break_char and data.endswith(break_char.encode()):
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

    def run_command(self, command: str, timeout=35):
        """Runs a command and returns the result"""
        self.send_msg(f"c:{command}")
        return self.read_data(timeout=timeout, break_char="\x00\x00\n")
