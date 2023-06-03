# HomeWizard-Wifi-Energy-Socket
A Python plugin for Domoticz that creates several devices for the HomeWizard Wifi Energy Socket.

![HomeWizard Wi-Fi Energy Socket](https://www.homewizard.com/wp-content/uploads/2023/02/homewizard-energy-socket.png)

The [HomeWizard Wi-Fi Energy Socket](https://www.homewizard.com/energy-socket/) can be used to measure the energy that is being used by the devices you plug into it. By default it sends all of its data to the HomeWizard servers but thanks to its local API you can read the device locally too. With this plugin you can use Domoticz to read the socket and store the data without using your internet connection.

###### Installing this plugin

Domoticz uses Python to run plugins. Use the [installation instructions](https://www.domoticz.com/wiki/Using_Python_plugins#Required:_install_Python) on the Domoticz wiki page to install Python. When Python is installed use [these instructions](https://www.domoticz.com/wiki/Using_Python_plugins#Installing_a_plugin) to install this plugin.

###### Enabling the API

To access the data from the Wifi Energy Socket, you have to enable the API. You can do this in the HomeWizard Energy app (version 1.5.0 or higher). Go to Settings > Meters > Your meter, and turn on Local API.

## Devices

The plugin creates several devices depending on the values that are read from your meter. Some may not be usefull for everyone but you can safely ignore those.
 1. An energy meter that shows your current power usage and total power usage
 2. A switch to turn the socket on/off
 3. A Wi-Fi signal strength meter that shows the current signal strength from the Wi-Fi Energy Socket

## Configuration

The configuration is pretty self explaining. You just need the IP address of your Wi-Fi Energy Socket. Make sure the IP address is static DHCP so it won't change over time.

| Configuration | Explanation |
|--|--|
| IP address | The IP address of the Wi-Fi P1 meter |
| Port | The port on which to connect (80 is default) |
| Data interval | The interval for the data devices to be refreshed |
| State interval | The interval to refresh the current status of the switch |
| Debug | Used by the developer to test stuff |
