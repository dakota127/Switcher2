#!/usr/bin/python
# coding: utf-8
# ***********************************************
# ***********************************************************
# 	MQTT Klasse

#   
#   enkapsulieren die Behandlung vom MQTT
#   
#   Oktober 2018 PBX
#************************************************
#
import os
import sys
import time
from time import sleep
import paho.mqtt.client as mqtt
import socket
from datetime import date
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.configread import ConfigRead

from sub.swcfg_switcher import cfglist_swi


DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3


#-------------------------------------------------
# Class MQTT_Conn erbt vom Class MyPrint
#   diese Class erbt von der MyPrint Class
#   
#
#--------------------------------------------------
class MQTT_Conn(MyPrint):
    ' klasse MQTTConn '

#    Definition der Class Variables
    instzahler=0           # Class variable Anzahl  instanzen


#-------Constructor der Klasse ------------------------------------------
# init Interprocess Comm, Sockets und so, mittels Module zeroMQ
# siehe hier  http://zeromq.org
#
    def __init__ (self , debug_in, path_in, client_id_in):
        self.debug = debug_in
        
        self.myprint (DEBUG_LEVEL1,   "--> MQTTConn_init_ called")    
        self.path = path_in          # pfad  main switcher
        self.topic_sub = ""
        self.mqtt_client_id = client_id_in 
        self.mqtt_broker_ip = ""
        self.mqtt_port = 0
        self.mqtt_keepalive_intervall = 0
        self.mqtt_topic = ""
        self.mqttc = 0              # Instance of mqtt
        self.broker_ok = False
        self.s = 0
        self.connected = False
        self.errorcode = 8
        self.topic_list = []
        self.callback_list = []
        
 # nun mqtt Brokder data aus config holen
        
        config = ConfigRead(self.debug)        # instanz der ConfigRead Class
        ret = config.config_read(self.path + "/swconfig.ini","switcher",cfglist_swi)
        if ret > 0:
            self.myprint (DEBUG_LEVEL0, "MQTT_Conn: config_read hat retcode: {}".format (ret))
            self.errorcode = 99
            return None

        self.myprint (DEBUG_LEVEL1, "--> MQTT_Conn: mqtt_conn_init_ called, client_id:{}".format(self.mqtt_client_id) )

#   IP-ADr Broker holen
        y = cfglist_swi.index("mqtt_ipadr")  + 1    # suche den Wert im Config-file
        self.mqtt_broker_ip = cfglist_swi[y]
#   Port Broker holen
        y = cfglist_swi.index("mqtt_port")  + 1    # suche den Wert im Config-file
        self.mqtt_port = (int(cfglist_swi[y]))
#   Intervall holen
        y = cfglist_swi.index("mqtt_keepalive_intervall")  + 1    # suche den Wert im Config-file
        self.mqtt_keepalive_intervall = (int(cfglist_swi[y]))

#  mqtt subscribe topic  holen
        y = cfglist_swi.index("mqtt_sub_topic")  + 1    # suche den Wert im Config-file
        self.topic_sub  = cfglist_swi[y].decode()

        def my_connect (mqttc, userdata, flags, rc):
            self.myprint (DEBUG_LEVEL1, "MQTT Connect OK, flags: {}, resultcode: {} ".format(str(flags),str(rc)))
            self.connected = True
            return
    
        
        if len(self.mqtt_broker_ip) == 0:
        
# eigene IP-ADr ermitteln
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # doesn't even have to be reachable
                self.s.connect(('10.255.255.255', 1))
                self.IP = self.s.getsockname()[0]
            except:
                self.IP = '127.0.0.1'
            finally:
                self.s.close()
               
        self.mqtt_broker_ip = self.IP       # dies ist unsere IP-ADR
        
        self.myprint (DEBUG_LEVEL1, "MQTT_Conn:: IP-Adr. des MQTT Brokers: {}".format(self.mqtt_broker_ip))

        self.mqttc = mqtt.Client(self.mqtt_client_id)   # Initiate MQTT Client
        self.mqttc.on_connect = my_connect
        # Connect with MQTT Broker
        try:
            self.mqttc.connect(self.mqtt_broker_ip, self.mqtt_port, self.mqtt_keepalive_intervall) 
            self.broker_ok = True
#            self.myprint (DEBUG_LEVEL0, "mqtt_conn: MQTT Connect hat geklappt")
            
        except:
            self.myprint (DEBUG_LEVEL0, "mqtt_conn: MQTT Connect failed, is mosquitto broker running?")
            self.myprint (DEBUG_LEVEL0, "mqtt_conn: start mosquitto mit 'sudo service mosquitto restart'")
    
    
  #      self.mqttc.subscribe(self.topic_sub, 0)
  #      self.myprint (DEBUG_LEVEL0, "Using Topic: {}".format(self.topic_sub))

    # Register Event Handlers
        self.mqttc.on_message = self.my_callback_msg

        self.errorcode = 0           # Aktor init ok

  #      self.mqttc.loop_start()     # starte mqtt loop


        
# --- Publish -------------------------------------
    def mypublish (self,topic, payload):
        self.myprint (DEBUG_LEVEL1,   "--> MQTT_Conn: mqtt_conn publish() called, topic: {}, payload: {}".format(topic,payload))
        pass
        self.mqttc.publish (topic,payload)

        pass

# --- Suscribe -------------------------------------
    def mysubscribe (self,topic_in):
        self.myprint (DEBUG_LEVEL1,   "--> MQTT_Conn: mqtt_conn subscribe() called, topic: {}".format(topic_in))
        pass
        self.mqttc.subscribe (topic_in)

        pass


#---------------------------------------------------
    def mqtt_run_forever(self):
        self.myprint (DEBUG_LEVEL1, "--> MQTT_Conn: mqtt_run_forever() called")
        self.mqttc.loop_forever()
        print ("loop_forever() beendet")
        return

    def mqtt_stop(self):
        self.myprint (DEBUG_LEVEL1, "--> MQTT_Conn: mqtt_stop() called")
        self.mqttc.loop_stop()
        return

#---------------------------------------------------
    def mqtt_start(self):
        self.myprint (DEBUG_LEVEL1, "--> MQTT_Conn: mqtt_start() called")
        self.mqttc.loop_start()
        self.myprint (DEBUG_LEVEL2, "loop_start() ausgefuehrt")
        return

#------------------------------------------------


#--- Method mqtt_set_topic ----------------------
    def mqtt_subscribe_topic (self, topic_in, callback_dazu):
        self.myprint (DEBUG_LEVEL1, "--> MQTT_Conn: mqtt_subscribe_topic() called, topic: {}, callback: {}".format(topic_in ,callback_dazu ))
    
        self.topic_list.append (topic_in)
        self.callback_list.append(callback_dazu)
        self.mqttc.subscribe ("switcher2/in/" + topic_in)
        
        self.myprint (DEBUG_LEVEL1, "--> MQTT_Conn: mqtt_subscribe_topic topic-liste ist nun:{}".format(self.topic_list))
        

        pass
        
        
#----Function Callback (msg gekommen )--------------------------------
    def my_callback_msg(self, mosq, obj, msg):
        global busy, my_wetter, debug
        
        self.myprint (DEBUG_LEVEL1,"--> MQTT_Conn: my_callback_msg() called, meldung gekommen: topic: {},  payload: {}".format( msg.topic,msg.payload.decode()))
    
    
        if  msg.topic.find("switcher2") ==  -1:         # nicht für uns
            self.myprint (DEBUG_LEVEL0, "MQTT_Conn: topic enthält nicht switcher2")
            return
              
    #    print (msg.topic)
    # wir sind an topic3 interessiert
        try:
            topic1, topic2, topic3 =  msg.topic.split("/")
        except:
            self.myprint (DEBUG_LEVEL0, "MQTT_Conn: topic-split falsch")
            return
        
        found = False
        for topic , callba in zip(self.topic_list , self.callback_list):
            if topic == topic3 :
                found = True
                try:
                    callba ( msg.payload.decode() )
                except:
                      

                    self.myprint (DEBUG_LEVEL0, "MQTTT_Conn: callback aufruf fehlerhaft fuer topic: {}".format (topic))
                    self.myprint_exc ("Fehlerhafter Callback .... !")

                    return
                
        if found == False:
            self.myprint (DEBUG_LEVEL0, "MQTT_Conn: my_callback_msg topic3 nicht in topic_list. topic3: {}, topic-list: {} ".format (topic3, self.topic_list))
                 
    #    
        return
    


#-------------Lösche Instanz ------------------------2-----------------
# close sockets und so
    def __del__(self):

        
        if  self.errorcode == 0:   
# Disconnect from MQTT_Broker
    
 #           self.mqttc.loop_stop()
        # Disconnect from MQTT_Broker
            self.mqttc.disconnect()



#--------------------------------------------------------------





#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swmqtt.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
