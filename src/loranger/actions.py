from subprocess import run

from pyroute2 import IPRoute
from pyroute2.netlink.exceptions import NetlinkError


def get_actions():
    """Gets the names of all actions in this module."""
    return [name for name in dir(Actions) if not name.startswith("__")]


class Actions:
    """Mixins for actions.
    Actions are run in response to r:cmd:arg1,arg2 calls.
    """

    def get_actions(self, *args, **kwargs):
        """Gets the names of all actions in this module."""
        return get_actions()

    def disable_interface(self, interface_name, *args):
        try:
            with IPRoute() as ipr:
                idx = ipr.link_lookup(ifname=interface_name)[0]
                ipr.link("set", index=idx, state="down")
                return "Disabled inferface: %s" % interface_name
        except IndexError:
            return "Interface not found: %s" % interface_name
        except NetlinkError as e:
            return "Error dissabling interface: %s" % e

    def enable_interface(self, interface_name, *args):
        try:
            with IPRoute() as ipr:
                idx = ipr.link_lookup(ifname=interface_name)[0]
                ipr.link("set", index=idx, state="up")
                return "Enabled inferface: %s" % interface_name
        except IndexError:
            return "Interface not found: %s" % interface_name
        except NetlinkError as e:
            return "Error enabling interface: %s" % e

    def add_address(self, interface_name, address, *args):
        addr, prefixlen = address.split("/")
        try:
            prefixlen = int(prefixlen)
        except ValueError:
            return "Invalid prefix length: %s" % prefixlen
        try:
            with IPRoute() as ipr:
                idx = ipr.link_lookup(ifname=interface_name)[0]
                self.logger.debug(f"ipr.addr('add', index={idx}, address={addr}, mask={prefixlen})")
                ipr.addr("add", index=idx, address=addr, mask=prefixlen)
                return "[%s] Added address: %s" % (interface_name, address)
        except IndexError:
            return "Interface not found: %s" % interface_name
        except NetlinkError as e:
            return "Error adding address: %s" % e

    def del_address(self, interface_name, address, *args):
        try:
            with IPRoute() as ipr:
                idx = ipr.link_lookup(ifname=interface_name)[0]
                ipr.addr("delete", index=idx, address=address)
                return "[%s] Deleted address: %s" % (interface_name, address)
        except IndexError:
            return "Interface not found: %s" % interface_name
        except NetlinkError as e:
            return "Error removing address: %s" % e

    def start_service(self, service_name, *args):
        ret = run(["rc-service", service_name, "start"], capture_output=True)
        if ret.returncode == 0:
            return "Started service: %s" % service_name

        return ret.stderr.decode()

    def stop_service(self, service_name, *args):
        ret = run(["rc-service", service_name, "stop"], capture_output=True)
        if ret.returncode == 0:
            return "Stopped service: %s" % service_name

        return ret.stderr.decode()
