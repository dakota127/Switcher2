#!/bin/bash

#  remove switcher

echo "remove services for switcher2"
#
file="/etc/init.d/switcher2.sh"
if [ -f "$file" ]
then
	echo "$file found, remove"
	rm -f $file
fi


file="/etc/init.d/swserver2.sh"
if [ -f "$file" ]
then
	echo "$file found, remove"
	rm -f $file
fi


update-rc.d switcher2.sh remove
update-rc.d swserver2.sh remove



#

echo "services for switcher2 removed"



