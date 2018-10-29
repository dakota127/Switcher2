#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class Aktor_5
#   
#   Diese Class impmentiert das pyhsische Schalten der Dosen 
#
#   diese Class erbt von der MyPrint Class
#   
#   Version mit send Module (Habi).
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
from sub.configread import ConfigRead
from sub.swcfg_switcher import cfglist_akt       # struktur des Aktors Config im Config File  
 
DEBUG_LEVEL0=0                      
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

#----------------------------------------------------
# Class Definition Aktor, erbt vom MyPrint
#----------------------------------------------------
class Aktor_5 (MyPrint):
    ' klasse aktor '
    aktorzahler=0               # Class Variable

    def __init__(self, dosennummer,debug_in , path_in):  # Init Funktion
        self.errorcode = 8           # init wert beliebig aber not zero

        self.nummer = Aktor_5.aktorzahler
        self.debug=debug_in
        self.path = path_in          # pfad  main switcher

        self.dosennummer=dosennummer            # arbeite für diese Dose (1 bis n)
        self.code=""
        self.pfad=""
        self.commandline=""
        self.pin=0
        GPIO.setmode (GPIO.BCM)
        rev=GPIO.RPI_REVISION
        GPIO.setwarnings(False)             # juni2018 ist neu hier, war in gpio_setup()

        
        self.action_type="Funk bei Habi"     # welche art Schalten ist dies hier
        
        self.myprint (DEBUG_LEVEL2, "--> aktor_5 {} aktor_init called für Dose {}".format (self.nummer,self.dosennummer))
        Aktor_5.aktorzahler +=1            # erhögen aktorzähler

 # nun alle GPIO Pins aus dem Config File holen
        
        config=ConfigRead(self.debug)        # instanz der ConfigRead Class
        ret=config.config_read(self.path + "/swconfig.ini","aktor_5",cfglist_akt)
        if ret > 0:
            self.myprint (DEBUG_LEVEL1, "config_read hat retcode: {}".format (ret))
            self.errorcode=99
            return None

        self.myprint (DEBUG_LEVEL3, "--> aktor_5 {} aktor_init : dose {} configfile read {}".format (self.nummer,self.dosennummer, cfglist_akt))

#   Hole Parameter aus config
        y=cfglist_akt.index("gpio_send")  + 1    # suche den Wert im Config-file
        self.pin = str(cfglist_akt[y])

        y=cfglist_akt.index("system_code")  + 1    # suche den Wert im Config-file
        self.code = cfglist_akt[y].decode()
        y=cfglist_akt.index("pfad_1")  + 1    # suche den Wert im Config-file
        self.pfad = cfglist_akt[y].decode()
        self.myprint (DEBUG_LEVEL1, "--> aktor_5 {} aktor_init : dose {}, using code {} und pfad: {} und pin:{}".format (self.nummer,self.dosennummer, self.code, self.pfad,self.pin))

        self.commandline = "sudo " + self.pfad + "/send" + " " + str(self.pin)+ " " + self.code + " " + str(self.dosennummer) + " "
        self.myprint (DEBUG_LEVEL1, "--> aktor_5 {} aktor_init : dose {}, using commandline: {}".format (self.nummer,self.dosennummer, self.commandline))
       

# **************************************************  



#-------------Terminate Action PArt ---------------------------------------
# cleanup GPIO PIns
#------------------------------------------------------------------------
    def __del__(self):
        self.myprint (DEBUG_LEVEL2, "--> aktor5 del called")
       
        pass


# ***** Function zum setzen GPIO *********************
    def schalten(self,einaus,debug_level_mod):
  
        self.myprint (debug_level_mod, "--> aktor5.schalten called ein/aus:{}".format(einaus))
#
        
        self.cmd=self.commandline + str(einaus)
        ret=os.system(self.cmd)
        time.sleep(1.2)                     # wenn mehrer setSwitch hintereinander kommen, muss man warten  
   
        if ret >0:
            self.myprint (DEBUG_LEVEL0, "--> aktor_5 dose {}, send module nicht gefunden: {}".format (self.dosennummer, self.cmd))
      
# ************************************************** 		


#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swaktor_5.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
