#!/usr/bin/python
# coding: utf-8
# ***********************************************************
#   Testscript MyPrint
#
#   es wird in File printest.log  geschrieben
# ***** Imports ******************************
import os, sys
import argparse

from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output


#
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
    global li 
    global seas
    global debug

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", help="kleiner debug", action='store_true')
    parser.add_argument("-D", help="grosser debug", action='store_true')
    parser.add_argument("-A", help="ganz grosser debug", action='store_true')


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
       
       
    return(args)
    
#----------------------------------------------


# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    nummer=[2,3]                # zum testen
    options=argu()              # get commandline args 
    
    mypri=MyPrint("printest_1","../switcher2.log",debug)    # Instanz von MyPrint Class erstellen
    mypri.myprint(DEBUG_LEVEL0, "Start printest_2")


    try:                                                       # übergebe appname und logfilename
        mypri.myprint (DEBUG_LEVEL1, "working")
        mypri.myprint (DEBUG_LEVEL2, "hard working")
        mypri.myprint (DEBUG_LEVEL3, "terribly hard working")
        pass
 #       qw=zuu
        nummer[4]=23            # sollte Fehler geben exception (hier umlauf für Test éàü)
    except Exception:
        print ("exception !!!")
        mypri.myprint_exc ("Etwas Schlimmes ist passiert.... !")
    finally:
        mypri.myprint (DEBUG_LEVEL1, "finally reached")
        
# fertig behandlung confifile
# Einlesen und Parsen der Steuer-Files für alle Seasons             alles neu juni2018

#  Abschlussvearbeitung
    print ("\nProgram terminated....")
    
    sys.exit(0)
#**************************************************************
#  That is the end
#***************************************************************
#