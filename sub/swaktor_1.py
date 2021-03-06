#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class Akto_1 
#   
#   Diese Class impmentiert das pyhsische Schalten der Dosen 
#
#   diese Class erbt von der MyPrint Class
#   
#   Version mit 4 LED - meist zum Testen verwendet.
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
 
DEBUG_LEVEL0=0                      
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

#----------------------------------------------------
# Class Definition Aktor, erbt vom MyPrint
#----------------------------------------------------
class Aktor_1 (MyPrint):
    ' klasse aktor '
    aktorzahler=0               # Class Variable
    
    def __init__(self, dosennummer,debug_in , config_filename_in):  # Init Funktion
        self.errorcode = 8
        self.nummer = Aktor_1.aktorzahler
        self.debug=debug_in
        self.dosennummer=dosennummer            # arbeite für diese Dose (1 bis n)
        self.Pins2=[]
        self.config_file = config_filename_in          # pfad  main switcher

        GPIO.setmode (GPIO.BCM)
        rev=GPIO.RPI_REVISION
        GPIO.setwarnings(False)             # juni2018 ist neu hier, war in gpio_setup()

        
        self.action_type="4 LED"     # welche art Schalten ist dies hier
        
        self.myprint (DEBUG_LEVEL2, "--> aktor_1 aktor_init called für Dose {}".format (self.dosennummer))
        Aktor_1.aktorzahler +=1            # erhögen aktorzähler

 # nun alle GPIO Pins aus dem Config File holen
 # es müssen 5 Pins definiert werden, da maximal 5 Dosen vorkommen können
        
        config=ConfigRead(self.debug)        # instanz der ConfigRead Class
        
        ret = config.config_read(self.config_file,"aktor_1",cfglist_akt)
##        ret=config.config_read(self.path + "/swconfig.ini","aktor_1",cfglist_akt)
        if ret > 0:
            self.myprint (DEBUG_LEVEL0, "config_read hat retcode: {}".format (ret))
            self.errorcode=99
            return None

        self.myprint (DEBUG_LEVEL3, "--> aktor_1 {} aktor_init : dose {} configfile read {}".format (self.nummer,self.dosennummer, cfglist_akt))

#   GPIO Pin 1 holen
 
        self.Pins2.append (int(cfglist_akt["gpio_1"]))
#   GPIO Pin 2 holen

        self.Pins2.append (int(cfglist_akt["gpio_2"]))
#   GPIO Pin 3 holen
        self.Pins2.append (int(cfglist_akt["gpio_3"]))
#   GPIO Pin 4 holen
        self.Pins2.append (int(cfglist_akt["gpio_4"]))
#   GPIO Pin 5 holen
        self.Pins2.append (int(cfglist_akt["gpio_5"]))

# nun wurde alle 5 Pins geholt, diese Instanz verwendet genau einen der Pins in der Liste Pins2
        self.mypin=self.Pins2[self.nummer]        # hole Pin NUmmer 
        GPIO.setup(self.mypin, GPIO.OUT)
 #       GPIO.output(self.mypin, True)
        self.myprint (DEBUG_LEVEL1, "--> aktor_1 {} aktor_init : dose {}, using GPIO:{}".format (self.nummer,self.dosennummer, self.mypin))
   
        self.errorcode=0    # init aktor ok



#-------------Terminate Action PArt ---------------------------------------
# cleanup GPIO PIns
#------------------------------------------------------------------------
    def __del__(self):
        self.myprint (DEBUG_LEVEL2, "--> aktor del called")
        
        if self.errorcode == 0:
            GPIO.cleanup(self.mypin)  # cleanup GPIO Pins


# ***** Function zum setzen GPIO *********************
    def schalten(self,einaus, debug_level_mod):
        global GPIO
  
        self.myprint (debug_level_mod, "--> aktor.schalten called mit: Gpio: %d ein/aus: %s" % (self.mypin, einaus))
#
        if einaus== 1:
            GPIO.output(self.mypin, True)         # dosen muss minus 1 sein wegen List index Dosen
        else:
            GPIO.output(self.mypin, False)
   
# ************************************************** 		


#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swaktor_1.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
