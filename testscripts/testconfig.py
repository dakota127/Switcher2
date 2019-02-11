#!/usr/bin/python
# coding: utf-8
# ***********************************************************
# 	Programm zum Anzeigen des Inhalts der XML Steuerfiles
# 	Designed and written by Peter K. Boxler, Februar 2015  
# 
#   Hilfsprogramm, welches die Aktionen im Steuer-File detailliert anzeigt
#
#
#	Commandline Parameter
#	-d kleiner Debug, Statusmeldungen werden ausgegeben (stdout)
#	-D grosser Debug, es wird viel ausgegeben (stdout)
#
#   Verbessert/Erweitert im Januar 2015, Peter K. Boxler
#   Verbessert/Erweitert im Juli 2018, Peter K. Boxler

# ***** Imports ******************************
import sys, getopt, os
import time
from time import sleep
import datetime
import argparse
from sub.swcfg_switcher import cfglist_swi
from sub.swcfg_switcher import cfglist_akt       # struktur des Aktors Config im Config File  
from sub.swdose import Dose                   # Class Dose, für das Dosenmanagement
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.configread import ConfigRead


# ***** Variables *****************************
tmp=0				# tmp für ein/aus

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
debug=0
#

# ***** Function Parse commandline arguments ***********************

#----------------------------------------------------------
# get and parse commandline args
def argu():
    global debug

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", help="kleiner debug", action='store_true')
    parser.add_argument("-D", help="grosser debug", action='store_true')
    parser.add_argument("-A", help="ganz grosser debug", action='store_true')


    args = parser.parse_args()
    if args.d:
        debug=DEBUG_LEVEL1
    if args.D: 
        debug=DEBUG_LEVEL2
    if args.A: 
        debug=DEBUG_LEVEL3
                 
    return(args)
    

def fun1():
    mypri.myprint (DEBUG_LEVEL0,  "Function fun1 prints...")	# für log und debug
    
def fun2(callback):
    mypri.myprint (DEBUG_LEVEL0,  "bin in fun2 vor call to callback")	# für log und debug

    callback()
    mypri.myprint (DEBUG_LEVEL0,  "bin in fun2 nach call to callback")	# für log und debug
    


# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    options=argu()                          # get commandline args
    
     #   Etablieren des Pfads 
    pfad=os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft
    logfile = pfad + "/test.log"

    mypri=MyPrint("testconfig","../test.log",debug)    # Instanz von MyPrint Class erstellen
    config=ConfigRead(debug)             # instanz der ConfigRead Class
    



    ret=config.config_read("swconfig.ini","switcher",cfglist_swi)
    mypri.myprint (DEBUG_LEVEL0,  "config_read bringt: {}".format (ret))	# für log und debug
    if ret > 0 :
        sys.exit(2)



# suche selbst nach werten, gibt aber exception, wenn nicht gefunden    
    u=cfglist_swi.index("testmode") + 1           # wo kommt der gelieferte name vor (index)
    mypri.myprint (DEBUG_LEVEL0,  "testmode value: {}".format (cfglist_swi[u]))	# für log und debug
    
# suche werte mit Methode, die sicher not found ab.
    ret=config.get_value(cfglist_swi,"hans")
    mypri.myprint (DEBUG_LEVEL0,  "get_value bringt: {}".format (ret))	# für log und debug
  
   
    mypri.myprint (DEBUG_LEVEL0,  "Nun actor_1 config lesen")	# für log und debug

    ret=config.config_read("swconfig.ini","aktor_1",cfglist_akt)
    mypri.myprint (DEBUG_LEVEL0,  "config_read bringt: {}".format (ret))	# für log und debug
    if ret > 0:
        sys.exit(2)
    
# suche werte mit Methode, die sicher not found ab.
    ret=config.get_value(cfglist_akt,"gpio_1")
    mypri.myprint (DEBUG_LEVEL0,  "get_value bringt: {}".format (ret))	# für log und debug

 # suche werte mit Methode, die sicher not found ab.
    ret=config.get_value(cfglist_akt,"gpio_X")
    mypri.myprint (DEBUG_LEVEL0,  "get_value bringt: {}".format (ret))	# für log und debug


    mypri.myprint (DEBUG_LEVEL0,  "Nun actor_5 config lesen")	# für log und debug  
    ret=config.config_read("swconfig.ini","aktor_5",cfglist_akt)
    mypri.myprint (DEBUG_LEVEL0,  "config_read bringt: {}".format (ret))	# für log und debug
    if ret > 0:
        sys.exit(2)  

# suche werte mit Methode, die sicher not found ab.
    ret=config.get_value(cfglist_akt,"pfad_1")
    mypri.myprint (DEBUG_LEVEL0,  "get_value bringt: {}".format (ret))	# für log und debug

    mypri.myprint (DEBUG_LEVEL0,  "\nnun test mit lesen swdosen.ini file")
    
    anz = config.read_dosenconfig ()
    mypri.myprint (DEBUG_LEVEL0,  "\ngemeldet wird anzahl dosen: {}". format(anz))     
           
    mypri.myprint (DEBUG_LEVEL0,  "\nnun test mit schreiben swdosen.ini file")
    
    config.write_value (int(4))
    
   
# fertig behandlung confifile

# noch test funktionsaufruf mit callback, ich rufe fun2 auf mit Parameter fun1 und fun2 führt dies aus. Genial.
    aa=fun1             # aa points to fun1()
    fun2(aa)            # an fun2 gebe ich fun1() als parameter
    


#  Abschlussvearbeitung
    print ("\nProgram terminated....")
    sys.exit(0)
#**************************************************************
#  That is the end
#***************************************************************
#