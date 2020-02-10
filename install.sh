#!/bin/bash
if ! which python3 &> /dev/null || ! which pip3 &> /dev/null; then
	echo "python3 and pip3 are required for this service"
	exit 1
fi

pip3 install -r ./requirements
cp ./mqtt-shutdown.py /usr/local/bin
cp ./mqtt-shutdown.service /etc/systemd/system
cp ./switch.sh /usr/local/bin/sss
chown root:root /usr/local/bin/mqtt-shutdown.py
chown root:root /etc/systemd/system/mqtt-shutdown.service
chown root:1000 /usr/local/bin/sss
chmod 775 /usr/local/bin/sss
mkdir -p /etc/mqtt-integration
cp ./mqtt-shutdown.conf /etc/mqtt-integration
chown -R root:root /etc/mqtt-integration
chmod 755 /etc/mqtt-integration
chmod 600 /etc/mqtt-integration/mqtt-shutdown.conf

echo "Please configure this service in '/etc/mqtt-integration/mqtt-shutdown.conf'"

mkdir -p /etc/mqtt-integration/shutdown-service
chown root:1000 /etc/mqtt-integration/shutdown-service
chmod 664 /etc/mqtt-integration/shutdown-service

echo "This service can be started using 'systemctl enable mqtt-shutdown.service'"
