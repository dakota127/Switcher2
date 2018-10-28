#!/usr/bin/python
# coding: utf-8
# ***********************************************************
#   Switcher 2
#   Testscript zum testen der Klasse MQTT_Conn
#   macht:
#           connect to mqtt broker auf local host
#           subscribe to topic 'switcher2'
#           gibt auf Konsole aus, was gekommen ist
#-------------------------------------------------------------

from sub.swmqtt import MQTT_Conn        # Class mQTT
import sys
import argparse, os
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
import threading
from time import sleep

from sub.swwetter import Wetter 

# Define Variables

mqtt_thread = 0
thread = 0
mymqtt_client = 0
debug = 0
my_wetter = 0

DEBUG_LEVEL0=0              # 'Konstanten'
DEBUG_LEVEL1=1             # 'Konstanten'
DEBUG_LEVEL2=2             # 'Konstanten'
DEBUG_LEVEL3=3             # 'Konstanten'

#----------------------------------------------------------
# get and parse commandline args
def argu():
    global thread

    parser = argparse.ArgumentParser()

    parser.add_argument("-p", help="mit thread", action='store_true')
    parser.add_argument("-d", help="kleiner debug", action='store_true')
    parser.add_argument("-D", help="grosser debug", action='store_true')


    args = parser.parse_args()
    if args.d:
        debug=DEBUG_LEVEL1
    if args.D: 
        debug=DEBUG_LEVEL2
        
    if args.p:
        thread = args.p
        
    
    return(args)
    

#----------------------------------------
# Define on_message event Handler
def on_message(mosq, obj, msg):
    msg = msg.payload.decode()
    print (msg)

#-------------------------------------------
def my_callback_msg(mosq, obj, msg):
    print ("my_callback_msg() called, meldung gekommen mit topic: {}".format(msg.topic))
    msg = msg.payload.decode()
    print (msg)

#--------------------------------------------
def mqtt_loop():
    mymqtt_client.mqtt_run_forever()


def callback_fuer_wetter( payload_in):
    print ("callback_fuer_wetter called(), payload ist: {}". format(payload_in))
    
def callback_fuer_pool( payload_in):
    print ("callback_fuer_pool called(), payload ist: {}". format(payload_in))
    

# ---------- Run the stuff ----------------
def runit():
    global debug
    global thread
    global mymqtt_client
    global my_wetter
    
    myprint = MyPrint("testmqtt","../switcher2.log",debug)    # Instanz von MyPrint Class erstellen
   
    path1 = os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script laeuft
    
    mymqtt_client = MQTT_Conn (debug, path1, "testmqtt")    # Instanz der Klasse MQTT_Conn kreieren
 
 
    my_wetter = Wetter (debug, path1, mymqtt_client)           
   
   
 
    mymqtt_client.mqtt_subscribe_topic ("pool" , callback_fuer_pool)                    # subscribe to topic
   
    
    myprint.myprint (DEBUG_LEVEL0, "nach instanz, thread: {}".format(thread))                                               # mqtt loop entweder in thread oder durch normalen start
    if thread == True:                                  # parameter commandlien
        mqtt_thread = threading.Thread(target = mqtt_loop)
        mqtt_thread.setDaemon (True)                       # damit thread beendet wird, wenn main thread endet
        mqtt_thread.start()                             
    else:
        mymqtt_client.mqtt_start()                          # ohne thread
    
#    mymqtt_client.mqtt_subscribe_topic ("switcher2/in/wetter" , callback_fuer_msg)                    # subscribe to topic
    myprint.myprint (DEBUG_LEVEL0, "Nach mqtt_start()")
    
       
    try:                                
        while True:                                         # main loop des programms
            sleep(1)
    except KeyboardInterrupt:
    # aufraeumem
        print ("Keyboard Interrupt")
        retu = my_wetter.get_wetter_data_all()
        print (retu)
        mymqtt_client.mqtt_stop()
        del mymqtt_client
   
        if thread == True:
            mqtt_thread.join()
 
    print ("testmqtt beendet")
 
       
            
# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    options=argu()        
 
    runit()
         
             
