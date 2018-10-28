#!/usr/bin/python
# coding: utf-8
# ***********************************************************
#   Testscript MyPrint
#
#   es wird in File printest.log  geschrieben
# ***** Imports ******************************
import sys, getopt, os
import time
import argparse

import socket

from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output

# ***** Variables *****************************

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

debug=DEBUG_LEVEL0

#
# ***** Function Parse commandline arguments ***********************
# get and parse commandline args
def argu():
    global li 
    global seas
    global debug

    parser = argparse.ArgumentParser()
                                                          #       kein Parm       will DEBUG_LEVEL0 sehen (sehr wichtig)                   
    parser.add_argument("-d", help="kleiner debug", action='store_true')        # will DEBUG_LEVEL1 sehen
    parser.add_argument("-D", help="grosser debug", action='store_true')        # will DEBUG_LEVEL2 sehen
    parser.add_argument("-A", help="ganz grosser debug", action='store_true')   # will DEBUG_LEVEL3 sehen
                                                              
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
    
	
# ***********************************************


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

#-------------------------------------------------
# funktion testprint zum Testen der debug-print funktion
#------------------------------------------------
def test_print():
    global debug
    
    mypr.myprint(DEBUG_LEVEL0,"---> Debug-Level ist auf {} gesetzt".format( debug))
  
    mypr.myprint(DEBUG_LEVEL0, "Debug-Output Level {} öéü sehr wichtig ".format(DEBUG_LEVEL0))    # unwichtig
    mypr.myprint(DEBUG_LEVEL1, "Debug-Output Level {} wichtig".format(DEBUG_LEVEL1))    # weniger wichtig
    mypr.myprint(DEBUG_LEVEL2, "Debug-Output Level {} weniger wichtig".format(DEBUG_LEVEL2))    # wichtig
    mypr.myprint(DEBUG_LEVEL3, "Debug-Output Level {} unwichtig".format( DEBUG_LEVEL3))    # sehr wichtig


    debug=2
    mypr.set_debug_level (debug)
    mypr.myprint(DEBUG_LEVEL0,"---> Debug-Level ist auf {} gesetzt".format( debug))
  
    mypr.myprint(DEBUG_LEVEL0, "Debug-Output Level {} sehr wichtig ".format(DEBUG_LEVEL0))    # unwichtig
    mypr.myprint(DEBUG_LEVEL1, "Debug-Output Level {} wichtig".format(DEBUG_LEVEL1))    # weniger wichtig
    mypr.myprint(DEBUG_LEVEL2, "Debug-Output Level {} weniger wichtig".format(DEBUG_LEVEL2))    # wichtig
    mypr.myprint(DEBUG_LEVEL3, "Debug-Output Level {} unwichtig".format( DEBUG_LEVEL3))    # sehr wichtig


    print ("\nEnde Debug-Print")
#

# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    options=argu()        

    mypr=MyPrint("printest_1","../switcher2.log",debug)    # Instanz von MyPrint Class erstellen

    mypr.myprint(DEBUG_LEVEL3,"Start printest_1")

    ipadr=get_ip()                # do get ip adr first
    mypr.myprint(DEBUG_LEVEL0,"This Pi's IP-Adress: {}".format(ipadr))

    test_print()        # do the work
    
    sys.exit(0)
#**************************************************************
#  That is the end
#***************************************************************
#