# MQTT shutdown trigger

## What does this do?
This is basically a service listening on a specified MQTT topic, to shut down the device when `OFF` is received.
This also includes means of setting the remote shutdown on hold or disabling it from the local machine if required.

## Installing
The install script will place the python script, the systemd service file and configuration templates in the default locations.
The OpenRC is included for legacy reasons, as I tried using that for a while, so it may not work in its current state.

Warning: The install script includes some hardcoded UID that should be changed. I did not come around to doing that.
