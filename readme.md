# LoRanger

System controller designed to be used with LoRa radios.

Has only been tested with ebyte E220 modules. Should work with any modules that work over UART.

## Server

`loranger_server` runs a server which listens for queries and commands from the client, and sends responses back.

## Client

`loranger_client` can send queries with -q, or run actions with -a followed by the action name and args.

### Query

Currently the following system information can be queried:

- `hostname` - returns the system hostname
- `uptime` - returns the system uptime
- `interfaces` - returns the system interfaces
- `ip4` - returns the system ipv4 address by interface name
- `ip6` - returns the system ipv6 address by interface name
- `macs` - returns the system mac addresses by interface name
- `routes` - returns all system routes


### Actions

- `disable_interface` Disables an interface by name 
- `enable_interface` Enables an interface by name
- `add_address` Adds an address to an interface
- `del_address` Deletes an address from an interface
- `start_service` Starts an OpenRC service
- `stop_service` Stops an OpenRC service
