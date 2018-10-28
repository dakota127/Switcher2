#!/usr/bin/python
# coding: utf-8
# ***********************************************************
#   Testscript timetest
#
#   probieren der time, differenz und so 
# ***** Imports ******************************
import sys, getopt, os
import time
import argparse
import datetime      
from datetime import date, datetime, timedelta

# ***** Variables *****************************

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

debug=DEBUG_LEVEL0
start_time_str =0
start_time =0
start_day =0
timenow=0
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


#-------------------------------------------------
# funktion testprint zum Testen der debug-print funktion
#------------------------------------------------
def test_time():
    global debug
    time_now=0
    time_now_str=0
    
    for i in range(40):
        time.sleep(10)
        time_now_str = "%s %s"  % (datetime.today().strftime("%A"), datetime.now().strftime("%d.%m.%Y %H.%M"))
        time_now = datetime.now()
        print ("Time now: {}".format(time_now_str))
        print ("diff: {}".format(time_now - start_time))
        today_day = date.today()
        
        lauf_tage = (today_day - start_day).days

        print ("Laufe seit {} Tagen".format (lauf_tage))
 
    print ("\nEnde testtime")
#

# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    options=argu()        
    start_day = date.today()
    
    start_time_str = "%s %s"  % (datetime.today().strftime("%A"), datetime.now().strftime("%d.%m.%Y %H.%M"))
    start_time = datetime.now()

    print ("Start time_test: start um: {}".format(start_time_str))
    print ("Start time_test: start um: {}".format(start_time))       # do the work
    
    test_time()
    
    sys.exit(0)
#**************************************************************
#  That is the end
#***************************************************************
#