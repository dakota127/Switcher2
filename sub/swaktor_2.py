#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class Aktor_2 
#   
#   Diese Class impmentiert das pyhsische Schalten der Dosen 
#
#   diese Class erbt von der MyPrint Class
#   
#   Version für Funksteckdosen mit einem 433 MHz Sender an einem GPIO Pin.
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
# import RPi.GPIO as GPIO         #  Raspberry GPIO Pins
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.configread import ConfigRead
from sub.swcfg_switcher import cfglist_akt       # struktur des Aktors Config im Config File  
from sub.rpi_rf import RFDevice

                 
DEBUG_LEVEL0 = 0
DEBUG_LEVEL1 = 1
DEBUG_LEVEL2 = 2
DEBUG_LEVEL3 = 3

#----------------------------------------------------
# Class Definition Aktor_3, erbt vom MyPrint
#----------------------------------------------------
class Aktor_2 (MyPrint):
    ' klasse aktor '
    aktorzahler = 0               # Class Variable
    
    def __init__(self, dosennummer,debug_in, path_in):  # Init Funktion
        self.errorcode = 8
        self.nummer = Aktor_2.aktorzahler
        self.debug = debug_in
        self.dosennummer = dosennummer            # arbeite für diese Dose (1 bis n)
        self.path = path_in          # pfad  main switcher

        self.action_type = "Funk2"     # welche art Schalten ist dies hier
        
        self.myprint (DEBUG_LEVEL1, "--> aktor {} aktor_init called fuer Dose {}".format (self.nummer,self.dosennummer))
        Aktor_2.aktorzahler += 1            # erhögen aktorzähler
        
 # nun alle notwendigen Parameter aus dem Config File holen
        
        config = ConfigRead(self.debug)        # instanz der ConfigRead Class
        ret = config.config_read(self.path + "/swconfig.ini","aktor_2",cfglist_akt)
        if ret > 0:
            self.myprint (DEBUG_LEVEL0, "config_read hat retcode: {}".format (ret))
            self.errorcode=99
            return None

        self.myprint (DEBUG_LEVEL3, "--> aktor_2 {} aktor_init : dose {} configfile read {}".format (self.nummer,self.dosennummer, cfglist_akt))

#   zuerst den GPIO Pin für den 433 MHz Sender
        y = cfglist_akt.index("gpio_1")  + 1    # suche den Wert im Config-file
        self.mypin = int(cfglist_akt[y])

#   repeat für den 433 MHz Sender
        y = cfglist_akt.index("repeat")  + 1    # suche den Wert im Config-file
        self.repeat = int(cfglist_akt[y])

#   codelengt für den 433 MHz Sender
        y = cfglist_akt.index("codelength")  + 1    # suche den Wert im Config-file
        self.codel = int(cfglist_akt[y])


        self.myprint (DEBUG_LEVEL1, "--> aktor_2 init: Dose: {}, repeat: {} , codel:{}".format(self.dosennummer, self.repeat,self.codel))

#   nun die Switch Codes und die Pulse Lenghts
#   zuerst die Parameter für das Einschalten
        such_base = "send_dat_" + str(self.dosennummer)
        such_ein = such_base+ "_ein"
        y = cfglist_akt.index(such_ein)  + 1    # suche den Wert im Config-file
        self.data = cfglist_akt[y]
        self.data = self.data.decode()
        self.data = str(self.data)

        self.swcode_ein,self.pulselength_ein,self.protocoll_ein = self.data.split(",")
        
        self.myprint (DEBUG_LEVEL1, "--> aktor_2 init: Dose: {}, code: {} , length: {} , protocoll:{}".format(self.dosennummer, self.swcode_ein,self.pulselength_ein,self.protocoll_ein))
 
 #      For Testing       
 #       print (type(self.swcode_ein), self.swcode_ein)
 #       self.swcode_ein=self.swcode_ein.decode()
 #       print (type(self.swcode_ein), self.swcode_ein)
         
        self.swcode_ein = int(self.swcode_ein)
        self.pulselength_ein = int(self.pulselength_ein)
        self.protocoll_ein = int(self.protocoll_ein)
#   dann die Parameter für das Ausschalten
        such_aus = such_base+ "_aus"
        y=cfglist_akt.index(such_aus)  + 1    # suche den Wert im Config-file
        self.data = cfglist_akt[y]
        
        self.data= self.data.decode()
        self.data= str(self.data)
        
         
        self.swcode_aus,self.pulselength_aus,self.protocoll_aus=self.data.split(",")
        self.myprint (DEBUG_LEVEL1, "--> aktor_2 init: Dose: {}, code: {} , length: {} , protocoll:{}".format(self.dosennummer, self.swcode_aus,self.pulselength_aus,self.protocoll_aus))
        self.swcode_aus = int(self.swcode_aus)
        self.pulselength_aus = int(self.pulselength_aus)
        self.protocoll_aus = int(self.protocoll_aus)

  
  # verwende rfdevice  von hier  https://github.com/milaq/rpi-rf
        self.rfdevice = RFDevice(self.mypin,self.myprint)
        self.rfdevice.enable_tx()
        self.rfdevice.tx_repeat = self.repeat
 
        self.errorcode = 0          # aktor init ok

#       For Testing               
#        print (type(self.swcode_ein),type(self.pulselength_ein),type(self.protocoll_ein))
#        print (type(self.swcode_aus),type(self.pulselength_aus),type(self.protocoll_aus))
#        print (type(self.codel), type(self.repeat))
#-------------Terminate Action PArt ---------------------------------------
# delete instance
#------------------------------------------------------------------------
    def __del__(self):
        self.myprint (DEBUG_LEVEL2, "--> aktor2 del called")
    
        pass

# ***** Function zum setzen GPIO *********************
    def schalten(self,einaus, debug_level_mod):
        global GPIO
  
        self.myprint (debug_level_mod, "--> aktor.schalten called mit: Gpio: %d ein/aus: %s" % (self.mypin, einaus))
#
        if einaus == 1:
            self.rfdevice.tx_code(self.swcode_ein, self.protocoll_ein, self.pulselength_ein, self.codel)
 #           self.rfdevice.cleanup()
        else:
            self.rfdevice.tx_code(self.swcode_aus, self.protocoll_aus, self.pulselength_aus, self.codel)
 #           self.rfdevice.cleanup()
          
   
# ************************************************** 		


#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swaktor_2.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
