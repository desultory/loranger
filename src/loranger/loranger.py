from contextlib import contextmanager
from time import sleep, time

from serial import Serial
from sys_gpio import Pin
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

    def __init__(
        self, console: str, baud: int, read_timeout=5, packet_size=200,
        power_pin=None, aux_pin=None, m0_pin=None, m1_pin=None,
        channel=None,
        *args, **kwargs
    ):
        self.serial = Serial(port=console, baudrate=baud)
        self.read_timeout = read_timeout  # serial read timeout in s
        self.packet_size = packet_size

        if m1_pin and not m0_pin or m0_pin and not m1_pin:
            raise ValueError("Both M0 and M1 pins must be defined")

        self.channel = channel
        self.power_pin = Pin(power_pin, logger=self.logger) if power_pin else None
        self.aux_pin = Pin(aux_pin, logger=self.logger) if aux_pin else None
        self.m0_pin = Pin(m0_pin, logger=self.logger) if m0_pin else None
        self.m1_pin = Pin(m1_pin, logger=self.logger) if m1_pin else None


    def module_init(self):
        """ Sets the module channel """
        if not self.channel:
            return self.logger.debug("No channel defined, skipping channel set")
        if self.channel and (not self.m0_pin or not self.m1_pin):
            raise ValueError("Both M0 and M1 pins must be defined to set the channel")

        self.m0_pin.value, self.m1_pin.value = 0, 0

        with self.aux_ready():
            self.logger.info("Setting channel to: %s", self.channel)
            self.serial.write(f"AT+CHANNEL={self.channel}\r\n".encode())
            ret = self.read_data(break_char=b"x\00")
            if ret != "=OK\x00":
                raise ValueError(f"Failed to set channel: {ret}")

    def module_startup(self):
        """Runs the startup sequence for the module"""

        if self.power_pin:
            self.logger.info("Powering pin: %s", self.power_pin)
            self.power_pin.value = 1

        if self.aux_pin:
            self.logger.info("Initalizing AUX pin: %s", self.aux_pin)
            self.aux_pin.direction = "in"

        self.serial.reset_input_buffer()
        self.module_init()

        if self.m0_pin:
            self.logger.info("Setting M0 and M1 to 1")
            # a value of 1 activates nfets tying the pins to module ground enabling transmission
            self.m0_pin.value, self.m1_pin.value = 1, 1
        self.announce()

    def module_reset(self):
        """Power cycles the module then sets the AUX pin high for 1s"""
        if not self.power_pin and not self.aux_pin:
            return self.logger.error("No power or AUX pin defined, cannot reset module")
        self.logger.info("Resetting module")
        self.power_pin.value = 0
        sleep(0.5)  # Power the module off for half a second
        self.power_pin.value = 1
        self.serial.reset_input_buffer() # Clear any junk data
        self.announce()

    def runloop(self):
        """Main loop, runs read_data forever and calls the appropriate action"""
        self.module_startup()
        self.logger.info("Listening on serial port: %s", self.serial.port)
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

    @contextmanager
    def aux_ready(self, low_time=10):
        """Checks that the AUX pin is low for 10ms before sending data.
        Low time is the time in ms that the AUX pin must be low before sending data"""
        if not self.aux_pin:
            try:
                yield
            finally:
                return

        low_s = low_time / 1000

        self.logger.debug("Checking AUX pin: %s", self.aux_pin)
        while self.aux_pin.value:  # First wait for the AUX pin to go low
            self.logger.debug("AUX pin is high, waiting for it to go low")
            with self.aux_pin.on_fall() as val:
                if val:
                    self.logger.debug("AUX pin went low")
                    break  # The pin is low

        begin_time = time()
        start_time = begin_time
        while start_time + low_s > time():
            with self.aux_pin.on_rise(low_s) as val:
                if val:  # The pin went high, reset the timer
                    self.logger.debug("AUX pin went high after %s", time() - start_time)
                    start_time = time()
        self.logger.debug("AUX pin is low, sending data. Elapsed time: %s", time() - begin_time)
        yield

    def chunk_data(self, data: bytes, chunk_size: int = None):
        """Chunks the data into chunks of chunk_size"""
        packet_size = chunk_size or self.packet_size
        for i in range(0, len(data), packet_size):
            yield data[i : i + packet_size]

    def send_msg(self, response: str):
        """Sends the message to the serial port
        If the aux pin is not defined, there may be data loss.
        """
        if isinstance(response, list) and not isinstance(response, str):
            response = ",".join(response)
        if not response.endswith("\n"):
            response += "\n"
        response = response.encode()
        self.logger.debug("Sending message: %s", response)

        if not self.aux_pin and len(response) > self.packet_size * 2:
            self.logger.warning("Data loss may occur without AUX pin")

        for chunk in self.chunk_data(response):
            with self.aux_ready():
                self.logger.debug("Sending chunk: %s", chunk)
                self.serial.write(chunk)

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
        if self.power_pin and not self.power_pin.value:
            self.logger.warning("Power is off, re-initializing module")
            self.module_startup()

        break_char = break_char.encode() if isinstance(break_char, str) else break_char
        timeout = timeout or self.read_timeout
        current_time = time()
        data = b""
        # Loop while the timeout is not reached, or if data is read
        while time() - current_time < timeout:
            if chunk := self.serial.read_all():
                self.logger.debug("Read chunk: %s", chunk)
                if (
                    chunk in [b"\xff\xbf"] or chunk.startswith(b"\xff") or chunk.startswith(b"\xbf")
                ):  # Got junk, reset AUX
                    self.logger.warning("Got junk data, resetting AUX pin")
                    self.module_reset()
                    data = b""
                    continue
                data += chunk
                current_time = time()
            if break_char and data.endswith(break_char):
                break
            sleep(0.001)
        # Sanitize first
        try:
            data = data.decode().strip()
        except UnicodeDecodeError:
            self.logger.warning("Data could not be decoded: %s", data)
            return self.module_reset()
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
