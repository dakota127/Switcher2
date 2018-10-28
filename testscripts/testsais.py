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
import os, sys
from xml.dom import minidom

from sub.swparse2 import ActionParser
import argparse
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.configread import ConfigRead
from sub.swcfg_switcher import cfglist_swi

forep=1
# aWeekdays
Weekdays={0: "Sonntag", 1:"Montag", 2: "Dienstag",3:"Mittwoch",4:"Donnerstag",5:"Freitag", 6:"Samstag"}
onoff={1:'ON', 0:'OFF'}
li=9                    # default gibt Liste der Aktionen aus, kann per cmdline verhindert werden
seas=0
#
list_tage= [ [] for z in range (3)] 
#   list_dose:  List für alle Seasons/Dosen/Tage/Aktionen
#   WICHTIG:    diese Liste wird nur aufgebaut, damit swlist_action eine Liste über alle Dosen erstellen kann.<<-----------------
#               switcher2.py brucht diese Liste nicht.
list_dose= [ [] for z in range (3)]                                    

list_zimmer =[]

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
debug=0
#
saison_simulate=[0,0]   # für Simulation der Seasons:   
                        # erstes Element: 0=keine Simulation/1=Siumlation
#                       #zweites Element: welche Season simuliert werden soll

actionpars=0
# ***** Function Parse commandline arguments ***********************

#----------------------------------------------------------
# get and parse commandline args
def argu():
    global li 
    global seas
    global debug

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", help="kleiner debug", action='store_true')
    parser.add_argument("-D", help="grosser debug", action='store_true')
    parser.add_argument("-A", help="ganz grosser debug", action='store_true')
    parser.add_argument("-s", help="Aktionsliste Sommer", action='store_true')
    parser.add_argument("-w", help="Aktionsliste Winter", action='store_true')
    parser.add_argument("-z", help="Aktionsliste Zwischen", action='store_true')
    parser.add_argument("-g",  help="Liste der Saisons", action='store_true')


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
    if args.s: 
       li=0             # nur sommer liste
    if args.w: 
       li=1             # nur winter liste
    if args.z: 
       li=2             # nur zwischen liste
    if args.g: 
       seas=1            # Saison Liste
         

    return(args)
    


#-------------------------------------
def setup():
    global actionpars

    config=ConfigRead(debug)        # instanz der ConfigRead Class

    actionpars=ActionParser(debug,pfad)      # Instanz der ActionParser Class
    configfile=pfad + "/swconfig.ini"
    ret=config.config_read(configfile,"switcher",cfglist_swi)
    if ret > 0:
        print("config_read hat retcode: {}".format (ret))
        sys.exit(2)
# fertig behandlung confifile
# Einlesen und Parsen der Steuer-Files für alle Seasons             alles neu juni2018
    ret=actionpars.get_files(list_tage,list_dose, list_zimmer,cfglist_swi)
#
#   nun sind alle Aktionen aus den XML-Files eingelesen und versorgt in den Listen list_tage, list_dosen und zimmer
#

    if ret > 0:
        print ("Methode get_files bringt errorcode: {}, kann nicht weiterfahren".format(ret))
    else:
    
# Anzahl Dosen feststellen: loop über alle Saisons, alle Tage und schauen, wo maximum ist
        anz_dosen=0
        for y in range (len(list_dose)):
            for i in range (len(list_dose[0])):
                anz= (len(list_dose[0][i]))
                if anz >  anz_dosen: anz_dosen=anz
        anz_dosen -= 1      # liste hat 5 elemente , es gibt aber -1 dosen
        print ("swlist: es wurden maximal {} Dosen gefunden".format( anz_dosen))
#        
            


# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    options=argu()        
 #   Etablieren des Pfads 
    pfad=os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft
    logfile = pfad + "/switcher2.log"
    mypri=MyPrint("swlist","../switcher2.log",debug)    # Instanz von MyPrint Class erstellen
    
    setup()                                                 # übergebe appname und logfilename

    actionpars.list_saison()
    ret=actionpars.check_saison_init()         # zuerst init der Seasonermittlung
    if ret > 0:
        print ("Switcher2 beendet wegen Fehler")	# wir starten       juni2018
        sys.exit(2)

    saison_simulate[0]=1
    saison_simulate[1]=1

    season_ret=actionpars.check_saison(saison_simulate)
    print (season_ret)



#  Abschlussvearbeitung
    print ("\nProgram terminated....")
    sys.exit(0)
#**************************************************************
#  That is the end
#***************************************************************
#