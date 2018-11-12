#!/bin/bash

#  setup switcher

echo "kopiere Files für mosquitto"

file="/etc/mosquitto/conf.d/my_mosquitto.conf"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden."
else
	echo "$file not found, also kopiere"
	cp -n -v mosquitto_stuff/my_mosquitto.conf /etc/mosquitto/conf.d
fi

file="/etc/mosquitto/passw.txt"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden."
else
	echo "$file not found, also kopiere"
	cp -n -v mosquitto_stuff/passw.txt /etc/mosquitto
fi

echo "Files fuer mosquitto gemacht"

#
cp -n -v shell_scripts/switcher2.sh /etc/init.d
cp -n -v shell_scripts/swserver2.sh /etc/init.d
update-rc.d switcher2.sh defaults
update-rc.d swserver2.sh defaults
chmod 755 /etc/init.d/switcher2.sh
chmod 755 /etc/init.d/swserver2.sh
#


