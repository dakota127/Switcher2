#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class Aktor_3 
#   
#   Diese Class impmentiert das pyhsische Schalten der Dosen 
#
#   diese Class erbt von der MyPrint Class
#   
#   Version IoT mit Subscribe to MQTT broker.
#
#   folgende public methods stehen zur Verfügung:
#       schalten (ein_aus)     ein_aus ist entweder 0 oder 1
#   
#   Juli 2018
#************************************************
#
import os
import sys
import time
from time import sleep
import RPi.GPIO as GPIO         #  Raspberry GPIO Pins
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.myconfig import ConfigRead
from sub.swcfg_switcher import cfglist_akt       # struktur des Aktors Config im Config File  
import socket
import paho.mqtt.client as mqtt
 
DEBUG_LEVEL0 = 0                      
DEBUG_LEVEL1 = 1
DEBUG_LEVEL2 = 2
DEBUG_LEVEL3 = 3

OFFON = ['OFF','ON']
TOPIC_P = ['','cmnd/dose%/POWER', 'cmnd/sonoff%/POWER','cmnd/future',' ']  # 4 Topics Publish fuer 4 verschiedene WiFi Schalter
                                                        # item 0 not used !!
TOPIC_S = ['','stat/dose%/POWER', 'stat/sonoff%/POWER','stat/future',' ']  # 4 Topics  Subscribe fuer 4 verschiedene WiFi Schalter
                                                        # item 0 not used !!
#----------------------------------------------------
# Class Definition Aktor, erbt vom MyPrint
#----------------------------------------------------
class Aktor_3 (MyPrint):
    ' klasse aktor '
    aktorzahler=0               # Class Variable
    
    def __init__(self, dosennummer,debug_in, meldungs_typ, subscribe, config_filename_in, mqtt_client_in, callback_dosen):  # Init Funktion
        self.errorcode = 8           # init wert beliebig aber not zero
        self.nummer = Aktor_3.aktorzahler
        self.debug = debug_in
        self.mqttc = mqtt_client_in
        self.meldungs_variante = meldungs_typ             # typ der mqtt meldung und topic
        self.subscribe_noetig = subscribe
        self.config_file = config_filename_in          # configfile
        self.dosencallback = callback_dosen
        self.dosennummer = dosennummer            # arbeite für diese Dose (1 bis n)
        self.mqtt_broker_ip = ""
        self.mqtt_port = 0
        self.mqtt_keepalive_intervall = 0
        self.mqtt_topic = ""
        self.mqtt_client_id = ""
        self.action_type = "mqtt"     # welche art Schalten ist dies hier
        self.broker_ok = False
        self.how = ''
        self.myprint (DEBUG_LEVEL1, "--> aktor_3 {} aktor_init called fuer Dose {}, msg_type:{}, subscribe:{}".format (self.nummer,self.dosennummer,self.meldungs_variante, self.subscribe_noetig))
        Aktor_3.aktorzahler += 1            # erhögen aktorzähler

 # nun mqtt Brokder data aus config holen
        
        config = ConfigRead(self.debug)        # instanz der ConfigRead Class
        ret = config.config_read(self.config_file,"aktor_3",cfglist_akt)
        if ret > 0:
            self.myprint (DEBUG_LEVEL0, "config_read hat retcode: {}".format (ret))
            self.errorcode = 99
            return None

        self.myprint (DEBUG_LEVEL2, "--> aktor_3 {} aktor_init : dose {} configfile read {}".format (self.nummer,self.dosennummer, cfglist_akt))

        self.broker_ok = True
  
        if self.subscribe_noetig > 0:       #   config verlangt, dass wir ein subscribe absetzen, damit die statusmeldungen
                                            #   von smart switches (sonoff) empfangen werden können
                                            #   NOTE: die Callback-Funktione liegt in der Dosenklasse, sie meldet uns
                                            #   den pointer zur funktion
            first, second = TOPIC_S[self.meldungs_variante].split('%')
            topic_subscribe = first + str(self.dosennummer) + second
  
            self.mqttc.subscribe_topic (topic_subscribe , self.dosencallback)     # subscribe to topic
            self.myprint (DEBUG_LEVEL0,  "--> aktor3 done mqtt subscription, topic: {} ".format(topic_subscribe))
    
            self.mqttc.subscribe_topic ("switcher2/switch/lw" , self.last_will)              # subscribe to Last Will Topic der Sensoren

        pass

# ************************************************** 		

#-------------Terminate Action PArt ---------------------------------------
# cleanup 
#------------------------------------------------------------------------
    def __del__(self):
        self.myprint (DEBUG_LEVEL2, "--> aktor_3 del called")
    
        pass



# ***** Function zum setzen GPIO *********************
    def schalten(self,einaus, debug_level_mod):
      
        payload = ""
        
        self.myprint (DEBUG_LEVEL0, "--> aktor3.schalten called mit ein/aus: {} ".format(einaus))
        
#
#       WICHTIG:
#       self.meldungs_variante == 1 ist für Testaufbau mit esp8266 
#       self.meldungs_variante == 2 ist für sonof switches , 
#       other smart switches might use other payloads <<<<------------- 
#       subscriber script swmqtt_sub.py zeigt meldung an
#
        self.how = OFFON[einaus]        # 'ON' oder 'OFF' setzen, wird gebraucht für Payload


        if self.meldungs_variante == 2 or self.meldungs_variante == 1:          # mqtt typ 2 für sonof switches    
 #           self.mqtt_topic = TOPIC_P[self.meldungs_variante]
            first, second = TOPIC_P[self.meldungs_variante].split('%')
            self.mqtt_topic = first + str(self.dosennummer) + second
            payload = self.how              # 'ON' oder 'OFF'

        elif self.meldungs_variante == 3:           # mqtt typ 3  (for future use9)      
            self.mqtt_topic = TOPIC_P[self.meldungs_variante]
            payload = str(self.dosennummer) + self.how
                   
               
        
        if self.broker_ok:          # nur senedne, wenn mqtt connection ok
                                    # wir verwenden für loggin den mod debuglevel von der dose
            self.myprint (debug_level_mod, "--> aktor3. publish mqtt Topic: {} , Payload: {}".format(self.mqtt_topic, payload))
 
 
        mqtt_error = self.mqttc.publish_msg (self.mqtt_topic, payload)
#        time.sleep(0.3)
        if mqtt_error > 0:
            myprint.myprint (DEBUG_LEVEL0, progname +  ": publish returns errorcode: {}".format(mqtt_error)) 
  #          return (mqtt_error)       
  #          self.mqttc.mypublish(self.mqtt_topic, payload)


#---- set_sensorstat -----------------
# hier kommt Last Will and Testament des schalters (siehe Arduino Code für ESP8266)
    def last_will(self,payload):
        self.myprint (DEBUG_LEVEL0,"--> aktor3.last_will() called  payload: {}".format( payload))
        pass
        
        # vorläufig empty
 
#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swaktor_3.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
