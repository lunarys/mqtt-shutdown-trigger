#!/bin/bash
systemctl disable mqtt-shutdown.service
rm -r /run/shutdown-service
rm /usr/local/bin/sss
rm /etc/systemd/system/mqtt-shutdown.service
rm /usr/local/bin/mqtt-shutdown.py
rm /etc/mqtt-integration/mqtt-shutdown.conf
