from unittest import TestCase, main

from loranger import LoRanger

class TestUptimePing(TestCase):
    def test_uptime_ping(self):
        """ Runs the uptime query continuously """
        loranger = LoRanger("/dev/ttyUSB0", 9600)
        last_uptime = 0
        while True:
            if uptime := loranger.run_query("uptime"):
                uptime = float(uptime)
                print(f"Uptime: {uptime}")
            else:
                uptime = last_uptime

            if uptime <= last_uptime:
                self.fail("Uptime is not increasing")
            last_uptime = uptime


if __name__ == "__main__":
    main()
