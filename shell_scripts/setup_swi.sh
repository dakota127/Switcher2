#!/bin/bash

#  setup switcher

echo "kopiere Files für mosquitto"

file="/etc/mosquitto/conf.d/my_mosquitto.conf"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden, remove"
	rm -f $file
fi
echo "$file not found, copy"
cp -n -v mosquitto_stuff/my_mosquitto.conf /etc/mosquitto/conf.d

# Password file 
rm -f my_passw.txt
file="/etc/mosquitto/my_passw.txt"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden, remove"
	rm -f $file
fi

echo "$file not found, also kopiere"
cp -n -v mosquitto_stuff/my_passw.txt /etc/mosquitto

# encrypt the passowrd file
echo "encrypt password file..."
mosquitto_passwd -U /etc/mosquitto/my_passw.txt

echo "mosquitto user config done"
echo " "

echo "mosquitto logfile permissions"
echo " "
sudo chmod 777 /var/log/mosquitto/mosquitto.log

echo " "
echo "copy scripts for switcher2"

#
file="/etc/init.d/switcher2.sh"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden, remove"
	rm -f $file
fi
echo "$file not found, also kopiere"
cp -n -v shell_scripts/switcher2.sh /etc/init.d


file="/etc/init.d/swserver2.sh"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden, remove"
	rm -f $file
fi
	echo "$file not found, also kopiere"
    cp -n -v shell_scripts/swserver2.sh /etc/init.d

chmod 755 /etc/init.d/switcher2.sh
chmod 755 /etc/init.d/swserver2.sh

update-rc.d switcher2.sh defaults
update-rc.d swserver2.sh defaults

echo "entferne .git Ordner"
rm -rf .git

#

echo "Setup for switcher2 done"



