#!/usr/bin/env python
# coding: utf-8
#
#   Client-Programm für Switcher-Daemon
#  Basierend auf Lazy Pirate client von Daniel Lundin hhttp://zguide.zeromq.org/py:all
#  Use zmq_poll to do a safe request-reply
#
#   Uses reliable request-reply to send request to server
#
#   if server does logging we use the subscriber model to receive logging messages from the server.
#
#   Author: Peter K. Boxler, August 2014, Revision July 2018
#------------------------------------------------------------

import sys, getopt, os

import zmq
import time
from time import sleep
import json
from sub.swipc import IPC_Client        # class IPC_Client
import sys
import argparse
from sys import version_info
from sub.swcfg_switcher import cfglist_swi
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output

from sub.configread import ConfigRead


SERVER_ENDPOINT = "tcp://localhost:5555"
REQUEST_RETRIES=3
REQUEST_TIMEOUT=3500

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
lastcommand=""
web=0
client=0
poll=0
context=0
debug=0
reboot_verlangt = 0
valid_commands =  [                 # tuple of valid commands
        "stop" ,                  #  terminate switcher
        "sdeb" ,                   # switcher stop debug output
        "mdeb",                    # switcher start debug output
        "stat",                    # switcher gebe status zurück
        "stad" ,                     # kurzen status
        "term",                    # terminate the client (not switcher)
        "spez",
        "dos1",
        "dos2",
        "dos3",
        "dos4",
        "dos5",
        "d1ein",
        "d2ein",
        "d3ein",
        "d4ein",
        "d5ein",
        "d1aus",
        "d2aus",
        "d3aus",
        "d4aus",
        "d5aus",
        "d1nor",
        "d2nor",
        "d3nor",
        "d4nor",
        "d5nor",        
        "aein",
        "aaus",
        "anor",
        "mmit",
        "mnie",
        "wett",
        "rebo",             # sende reboot verlangt an den switcher
        "reboc"             # dieser client mach reboot pi
        
        ]                    # switcher soll antwort verspätet senden

anz_commands=0
#------------------------------    

sequence = 0

i=0
anzerr=0
anztry=3
message=" "
stop=0
slog=0
ret=0
debug=0
ipc=0
#
config=0
mypri=0


#----------------------------------------------------------
# get and parse commandline args
def argu():
    global debug
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", help="kleiner debug", action='store_true')
    parser.add_argument("-D", help="grosser debug", action='store_true')
    parser.add_argument("-A", help="ganz grosser debug", action='store_true')
    parser.add_argument("-s",       help="Nur Statusausgabe", action='store_true')
    parser.add_argument("-dein",    help="Dose manuell ein", default=0, type=int)
    parser.add_argument("-daus",    help="Dose manuell aus", default=0, type=int)
    parser.add_argument("-dnor",    help="Dose normal",default=0, type=int)


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
def setup():
    global anz_commands
    global options
    global config, mypri
  
    options=argu()                          # get commandline args
    pfad=os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft

    mypri=MyPrint("swclient2","../switcher2.log",debug)    # Instanz von MyPrint Class erstellen
                                                        # übergebe appname und logfilename
    config=ConfigRead(debug)        # instanz der ConfigRead Class

    anz_commands=len (valid_commands)
    config=ConfigRead(debug)        # instanz der ConfigRead Class
    ret=config.config_read(pfad + "/swconfig.ini","switcher",cfglist_swi)
    if ret > 0:
        print("config_read hat retcode: {}".format (ret))
        sys.exit(2)
# fertig behandlung confifile

    if ret==9:  sys.exit(2)
# fertig behandlung confifile

    
#----------------------------------------------------------
def printReply(meldung):
    spos=0
    epos=0
    
    if meldung.find("stat") == -1 and meldung.find("stad") == -1 and meldung.find("wett") == -1: 
        print ("Antwort vom Server: %s" % meldung)
        return       #  ss ist nicht stat oder stad oder wett

    # es ist antwort auf statusrequest oder wetter
    meldung = meldung[4:]         # entferne meldungs id 4 char

    try:
        meld=json.loads(meldung)   # JSON Object wird in Python List of List gewandelt
    except:
        print ("Status string nicht gut...")
        return

    # antwort besteht aus einer Liste mit Einträgen
    # index[0] sind die Daten an den Webserver
    # restliche einträge sind die DAten
    
    print ("Info fuer den Webserver: -------- Anz Items: {}".format(len(meld[0])))  
    for i in range(len(meld[0])):
        print ("{:18}:  {:<18}".format (meld[0][i][0]  ,meld[0][i][1]))
    
    meld.pop(0)             # liste mit indo an den webserver wegpoppen
    
    
    print ("Und nun die Daten: -------------- Anz Items: {}".format(len(meld)))     

#  wetterdaten ist liste laenge 2, alle anderen haben mehr items
#  not very well done..... but it works
    if len(meld) == 2 :         # sind wetterdaten
        for item1 in meld :   
  #          print ("len item1: {}".format(len(item1))) 
            for item2 in item1 :
                print ("{:18}:  {:<18}".format (item2[0]  ,item2[1]))
    else:       # andere daten haben liste mit mehr als 2 items
        for item1 in meld :    
            print ("{:18}:  {:<18}".format (item1[0]  ,item1[1]))    

    print ("--------------------------------------")
#----------------------------------------------------------




#-------------Get Command from Keyboard----------------------------------
# falls letzter command stat war, kann dieser mit enter wiederholt werden.
def get_command() :
    while True:
        stop=0
        slog=0
        global lastcommand

        sys.stdout.write("Bitte einen Command eingeben: ")
        if sys.version_info[0] < 3:
            message = raw_input().strip()
        else:
            message = input()
            
        message = message.strip()
       
        if (len(message)==0 and lastcommand=="stat"): return (lastcommand)
        
        lastcommand=message
        return(message)              
#-----------------------------------------------

#----------------------------------
def runit():
    global debug, reboot_verlangt
# Loop until command term is given
    while True:
    # get command from user
        cmd=get_command()       # command in cmd  
        cmd = cmd.strip()
                                # zuerst spezielle commands behandeln
        if cmd.find("term") != -1: break 
        if cmd.find("reboc") != -1: 
            reboot_verlangt = 1
            break 
        if cmd.find("mdeb") != -1: debug=1
        if cmd.find("sdeb") != -1: debug=0

        if cmd.find("spez") != -1: 
        
            if cmd.isalpha(): cmd=cmd+"500"         # falls keine Nummer gegeben wurde nach spez 
            s=int("".join(filter(str.isdigit, cmd)))
            print ("Requesting Serverdelay: %d" % s)
            pass
                                # nun die normalen commands
        elif cmd not in  valid_commands:
            print("wrong command, try again") 
            continue          

#    send to server und wait for reply    
        retcode=ipc.ipc_exchange(cmd)           # try to send request
        if retcode[0] == 9:                        # server antwortet nicht
            break            
        printReply(retcode[1])          #  this the string that came back from server
    
#-----------------------------------
# MAIN, starts here
#------------------------------------
if __name__ == "__main__":

    if version_info[0] < 3:
        print("swclient2.py läuft nur richtig unter Python 3.x, du verwendest Python {}".format(version_info[0]))
        sys.exit(2)

    setup()
    u=cfglist_swi.index("ipc_endpoint_c") + 1           # wo kommt der gelieferte name vor (index)

    ipc=IPC_Client(debug,REQUEST_TIMEOUT, cfglist_swi[u],REQUEST_RETRIES)


    # commandline -s verlangt eine Status-Abfrage, dann exit
    if options.s:
        cmd="stat"
        retcode=swipc1.ipc_exchange(cmd)           # try to send request

        if retcode[0] == 0:
            printReply(retcode[1])
        sys.exit(2)
        
    elif options.dein >0 :        # dose schaltn verlangt
        cmd="d" + str(options.dein) + "ein"
        retcode=ipc.ipc_exchange(cmd)           # try to send request
        del ipc
        sys.exit(2)

    elif options.daus >0 :        # dose schaltn verlangt
        cmd="d" + str(options.daus) + "aus"
        retcode=swipc1.ipc_exchange(cmd)           # try to send request
        del ipc
        sys.exit(2)

    elif options.dnor >0 :        # dose schaltn verlangt
        cmd="d" + str(options.dnor) + "nor"
        retcode=swipc1.ipc_exchange(debug,cmd)           # try to send request
        swipc1.ipc_term(debug)
        sys.exit(2)

#  now run the programm, falls vond er Commandline gestartet        
    runit()                 # get commands from Console and send them....
                            # kommt zurück, wenn term command gegeben oder Verbindung nicht geht.
    del ipc                        
    
    if reboot_verlangt == 1:
        print ("Terminating mit reboot pi")
        sleep(2)
        os.system('sudo shutdown -r now')
    else:
        print ("Client terminating...")
#            
#