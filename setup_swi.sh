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
echo " "
echo "kopiere scripts für switcher"

#
file="/etc/init.d/switcher2.sh"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden."
else
	echo "$file not found, also kopiere"
    cp -n -v shell_scripts/switcher2.sh /etc/init.d
fi

file="/etc/init.d/swserver2.sh"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden."
else
	echo "$file not found, also kopiere"
    cp -n -v shell_scripts/swserver2.sh /etc/init.d
fi

chmod 755 /etc/init.d/switcher2.sh
chmod 755 /etc/init.d/swserver2.sh

update-rc.d switcher2.sh defaults
update-rc.d swserver2.sh defaults

#
echo "Files fuer switcher gemacht"



