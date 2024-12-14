from pyroute2 import IPRoute


def get_queries():
    """Gets the names of all actions in this module."""
    return [name for name in dir(Queries) if not name.startswith("__")]


class Queries:
    """Mixins for queries.
    Actions are run in response to q:param.
    """

    def get_queries(self):
        """Gets the names of all actions in this module."""
        return get_queries()

    def query_interfaces(self):
        """Gets all interfaces of the current machine."""
        with IPRoute() as ipr:
            return [link.get_attr("IFLA_IFNAME") for link in ipr.get_links() if link["ifi_type"] != 772]

    def query_hostname(self):
        """Gets the hostname of the current machine."""
        from os import uname

        return uname()[1]

    def query_ip4(self):
        """Gets all IP addresses of the current machine."""
        out_str = ""
        with IPRoute() as ipr:
            for interface in ipr.get_links():
                if interface["ifi_type"] == 772:
                    continue
                out_str += f"{interface.get_attr('IFLA_IFNAME')}["
                out_str += ",".join(
                    f"{addr.get_attr("IFA_ADDRESS")}/{addr["prefixlen"]}"
                    for addr in ipr.get_addr(index=interface["index"])
                    if addr["family"] == 2
                )
                out_str += "]"
        return out_str

    def query_ip6(self):
        """Gets all IPv6 addresses of the current machine."""
        out_str = ""
        with IPRoute() as ipr:
            for interface in ipr.get_links():
                if interface["ifi_type"] == 772:
                    continue
                out_str += f"{interface.get_attr('IFLA_IFNAME')}["
                out_str += ",".join(
                    f"{addr.get_attr("IFA_ADDRESS")}/{addr["prefixlen"]}"
                    for addr in ipr.get_addr(index=interface["index"])
                    if addr["family"] == 10
                )
                out_str += "]"
        return out_str

    def query_routes(self):
        """Gets all routes of the current machine."""
        with IPRoute() as ipr:
            return [
                f"{ipr.get_links(route.get_attr("RTA_OIF"))[0].get_attr('IFLA_IFNAME')}[{route.get_attr("RTA_DST")}/{route["dst_len"]}]"
                for route in ipr.get_routes()
                if route.get_attr("RTA_DST") is not None and route["family"] == 2 and route["type"] == 1
            ]

    def query_macs(self):
        """Gets all MAC addresses of the current machine."""
        out_str = ""
        with IPRoute() as ipr:
            for interface in ipr.get_links():
                if interface["ifi_type"] == 772:
                    continue
                out_str += f"{interface.get_attr('IFLA_IFNAME')}[{interface.get_attr('IFLA_ADDRESS')}]"
        return out_str

    def query_uptime(self):
        """Gets the uptime of the current machine."""
        from pathlib import Path

        return Path("/proc/uptime").read_text().split()[0]
