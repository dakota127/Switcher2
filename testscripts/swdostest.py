#!/usr/bin/python
# coding: utf-8
# ***********************************************
#   Schalten der Dosen  
#   
#   Testprogramm zum Schalten von 4 Dosen
#  
#   
#   Juli 2018
#************************************************
#
import os
import sys
import time
from time import sleep
import argparse
from sub.swcfg_switcher import cfglist_swi
from sys import version_info

from sub.swdose import Dose                   # Class Dose, für das Dosenmanagement
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.configread import ConfigRead


DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

dosen=[]        # list aller dosen
schalt_art=1
debug=1
counter=5       # loop counter
mypri=0
sleeptime=4

#----------------------------------------------------------
# get and parse commandline args
def argu():
    global schalt_art, counter
    global debug

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", help="kleiner debug", action='store_true')
    parser.add_argument("-D", help="grosser debug", action='store_true')
    parser.add_argument("-A", help="ganz grosser debug", action='store_true')
    parser.add_argument("-s", help="Schalt_Art", default=1, type=int)
    parser.add_argument("-l", help="Durchläufe", default=10, type=int)
    


    args = parser.parse_args()
#    print (args.d, args.s, args.dein, args.daus, args.dnor, args.dexc, args.dinc)          # initial debug
#    if args.s:
#        print ("s war hier")
    if args.d:
        debug=DEBUG_LEVEL1
    if args.D: 
        debug=DEBUG_LEVEL2
    if args.A: 
        debug=DEBUG_LEVEL3
     
    schalt_art=args.s   
    counter=args.l   
    return(args)
 


#-----------------------------------------
def runit():

    global debug, mypri
    
    options=argu()        

    
    mypri=MyPrint("dostest","../test.log",debug)    # Instanz von MyPrint Class erstellen

    config=ConfigRead(debug)        # instanz der ConfigRead Class
    ret=config.config_read("swconfig.ini","switcher",cfglist_swi)
    mypri.myprint (DEBUG_LEVEL1,  "config_read bringt: {}".format (ret))	# für log und debug
    if ret > 0 :
        sys.exit(2)
    path1=os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft

# hole schaltart aus configfile
    y=cfglist_swi.index("schaltart")  + 1           # suche den Wert von schaltart aus Config-file
    schalta=int(cfglist_swi[y])

    mypri.myprint (DEBUG_LEVEL0,  "Schaltart aus Config-File: {}  aus Cmdline Arg: {}".format (schalta,schalt_art))	# für log und debug
    
    try:

        dosen.append(Dose(1,1,debug,path1))           # 4 Dosen instantiieren 
        dosen.append(Dose(2,1,debug,path1))
        dosen.append(Dose(3,1,debug,path1))
        dosen.append(Dose(4,1,debug,path1))
    #    print (dosen)
    
    
        mypri.myprint (DEBUG_LEVEL0,  "dostest: --> Loop, Dosen {} mal ein/ausschalten". format(counter))	# für log und debug
    
        for i in range(counter):
            mypri.myprint (DEBUG_LEVEL0,  "dostest: Schalte Dose 1 ein")	# für log und debug
            dosen[0].set_auto(1)
            sleep(sleeptime)
            mypri.myprint (DEBUG_LEVEL0,  "dostest: Schalte Dose 1 aus")	# für log und debug
            dosen[0].set_auto(0)   
           
            mypri.myprint (DEBUG_LEVEL0,  "dostest: Schalte Dose 2 ein")	# für log und debug
            dosen[1].set_auto(1)
            sleep(sleeptime)
            mypri.myprint (DEBUG_LEVEL0,  "dostest: Schalte Dose 2 aus")	# für log und debug   
            dosen[1].set_auto(0)   
        
        
            mypri.myprint (DEBUG_LEVEL0,  "dostest: Schalte Dose 3 ein")	# für log und debug
            dosen[2].set_auto(1)
            sleep(sleeptime)
            mypri.myprint (DEBUG_LEVEL0,  "dostest: Schalte Dose 3 aus")	# für log und debug   
            dosen[2].set_auto(0)   
        
            mypri.myprint (DEBUG_LEVEL0,  "dostest: Schalte Dose 4 ein")	# für log und debug
            dosen[3].set_auto(1)
            sleep(sleeptime)
            mypri.myprint (DEBUG_LEVEL0,  "dostest: Schalte Dose 4 aus")	# für log und debug   
            dosen[3].set_auto(0)   
    
    
        mypri.myprint (DEBUG_LEVEL0,  "dostest: Loop beendet". format(counter))	# für log und debug
    
        
        mypri.myprint(DEBUG_LEVEL1,"Alle Dosen auf zuhause setzen")
        
        for i in range(len(dosen)):
            dosen[i].set_zuhause()
    
        
        for i in range(len(dosen)):
            dosen[i].display_status()
    
        status=""
        for i in range(len(dosen)):
            status=status + " - " + dosen[i].show_status()
        print (status[3:])
    
        print ("Anzahl Dosen: {}".format(dosen[0].display_anzahl()))
      
        for i in range(len(dosen)):
            dosen[i].set_nichtzuhause()
     
        status=""
        for i in range(len(dosen)):
            status=status + " - " + dosen[i].show_status()
        print (status[3:])
       
  
    except KeyboardInterrupt:
    # aufräumem
        mypri.myprint (DEBUG_LEVEL0,  "Keyboard Interrupt, alle Dosen OFF und clean up pins")
    except Exception:
        #       etwas schlimmes ist passiert, wir loggen dies mit Methode myprint_exc der MyPrint Klasse
        mypri.myprint_exc ("Etwas Schlimmes ist passiert.... !")
    finally:
    # hierher kommen wir immer, ob Keyboard Exception oder andere Exception
        mypri.myprint (DEBUG_LEVEL1, "Main Loop Ende erreicht ohne Probleme (finally reached)")
        print ("Dosen deleten")
        for i in range(len(dosen)):
            del dosen[0]
   
        pass            # letztes Statement im Main Loop    
        

#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
   
    if version_info[0] < 3:
        print ("swdostest.py läuft nur richtig unter Python 3.x, du verwendest Python {}".format(version_info[0]))
        sys.exit(2)
   
    runit()
    
    mypri.myprint(DEBUG_LEVEL1,"Test beendet")

    sys.exit(0)
    
 #------------------------------------------------------------
    
