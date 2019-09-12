# ISY-Net

### The ISY-Net nodeserver is designed to mirror the z-wave devices from one ISY to a master.
 - user = Username of the admin user for the remote ISY
 - password = Password of the admin user for the remote ISY
 - address = the IP address of the remote ISY to mirror devices from
 - port = Port number for http connections.  Default it 80

### Currently Support Devices
 - Basic Switch including power plugs
 - Power plug with energy meter capabilities
 - Thermostat (StelPro STZW402+ has been tested)

### Limitations
 - Currently only Imperial UOM is supported (Fahrenheit) for temperatures
 - Mirror nodes may show more options than parent as they are based on the full capabilities
 defined by the ISY node definitions.
 - Sensors are not yet added

### Installation

Install from the Polyglot Store
