#!/usr/bin/python3
# coding: utf-8
#
# http://www.steves-internet-guide.com/client-connections-python-mqtt/
# Test für mqtt connection, guter code...
#
import paho.mqtt.client as mqtt  #import the client1
import time, sys

def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.connected_flag=True  #set flag
        print("connected OK")
    else:
        print("Bad connection Returned code=",rc)

mqtt.Client.connected_flag =False       #create flag in class
broker="192.168.1.145"
client = mqtt.Client("python1")             #create new instance 
client.on_connect = on_connect            #bind call back function
client.loop_start()
print("Connecting to broker ",broker)
client.username_pw_set(username = "switchere" , password="itscool")

client.connect(broker)      #connect to broker

for z in range (10):
    if client.connected_flag:
        break        #wait in loop
    else:
        print("In wait loop")
        time.sleep(1)
 
if not client.connected_flag:
    print ("keine verbindung..., abbruch")
    sys.exit(2)
print   ("connected, now in Main Loop")
client.loop_stop()    #Stop loop 
client.disconnect() # disconnect