#!/usr/bin/python3
# coding: utf-8
# ***********************************************************
# 	Programm zum Schalten von Funksteckdosen - VESRION 2
# 	Designed and written by Peter K. Boxler, August 2014  / August 2018
# 
#   Der Switcher wurde entwickelt, um eine Anzahl von Steckdosen ein- oder auszuschalten, 
#   gemaess einer in Steuerfiles definierten Abfolge von Schaltaktionen. 
#   Ausserdem koennen einzelne Steckdosen durch den Benutzer direkt ein- oder ausgeschaltet werden.
#
#	Die Aktionen (Einschalten/Ausschalten) pro Tag und Dose sind in 3 externen externen 
#   XML-Steuerfile codiert. Es gibt einen File fuer Sommersausin, Winter- und Zwischensaison.
#	Es koennen beliebig viele Ein/Aus Schaltungen pro Wochentag (0 bis 6, also So bis Sa) und Dose definiert werden
#	Die gesamte Wochensequenz wird endlos wiederholt - Abbruch durch ctrl-c.
#   
#	Zum Testen kann mit Commandline Parameter -s eine Simulation gestartet werden: eine Woche wird 
#	dadurch in wenigen Minuten durchlaufen. 
#
#	Commandline Parameter: mache switcher2.py -h
#    
#
#
#   Erweiterungen
#
#   Junli 2018
#   alle Ationen und dazugehoerige Variablem im Zusammenhang mit der bisherigen Implementation mit Funksteckdosen
#   wurde ausgelagert in zwei Klassen Dose und Aktor.
#   Der Code in switcher2.py weiss nichts mehr von der Art und Weise, wie die Dosen
#   angesteuert werden. Dies ist voll in der Klasse Dose (in swdose.py) implementiert.
#   Zudem Einiges bereinigt im Switcher, auch IPC module swipc2.py und dessen Aufrufe verbessert.
#   Alle betroffenen Zeilen gekennzeichnet mit juni2018
#
#
#
# ***** Imports ******************************
import sys, getopt, os
import time
from time import sleep
import signal
import datetime         
import argparse
import threading
from datetime import date, datetime, timedelta
import RPi.GPIO as GPIO         #  Raspberry GPIO Pins

from sub.swparse2 import ActionParser    # Class ActionParser, parsed XML Files
from sub.swdose import Dose                   # Class Dose, fuer das Dosenmanagement
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.configread import ConfigRead
from sub.swipc import IPC_Server    # Class IPC Server 
from sub.swcfg_switcher import cfglist_swi
from sub.swdefstatus import status_klein
from sub.swdefstatus import status_gross

from sub.swmqtt import MQTT_Conn        # Class mQTT
from sub.swwetter import Wetter 
from sub.sizeof import get_size

import json
from sys import version_info
import socket

# 'Konstanten' *******************************
JANEIN=["Nein","Ja"]
ONOFF={1:'ON', 0:'OFF'}     
wochentage=["Sonntag","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag"]
reset_man=["Nie","Mitternacht"]
SLEEPTIME=1			            # default sleeptime normaler Lauf
SLEEPTIME_DONE = 2              # sleeptime vor Mitternacht (alle Aktionen gemacht)
DEBUG_LEVEL0=0                  # 'Konstanten'
DEBUG_LEVEL1=1                  # 'Konstanten'
DEBUG_LEVEL2=2                  # 'Konstanten'
DEBUG_LEVEL3=3                  # 'Konstanten'
ALIVE_INTERVALL_1 = 2400     # in Sekunden, also: 2400 /60  gleich 40 min 
ALIVE_INTERVALL_2 = 86400     # in Sekunden, also: 86400 /60  gleich 1440 min gleich 24 Std        
__VERSION__ = '2.1'             # Switcher version

# ***** Variables *****************************
# Globals for this module


tmp=0				            # tmp fuer ein/aus
actions_only=0		            # switch fuer commandline arg a
ret_ipc=0                       # returncode ipc  juni2018
ret_dose=0                      # return von ipc, dosennunmer
#
hhmm_tag = [0,0]                # liste {'HH.MM', 'Wochentag'}
python_version=0
zuhause=False                   # jemand zuhause status - switch is checked once in main loop
                                # 0 = niemand da switch normally
                                # 1 = jemand zuhause, do not switch light
zuhause_old=False               # to check for change

        
gpio_blink=10                   # GPIO fuer blinkende LED auf gruenem Board 
gpio_home_switch=13             # I am Home Switch (hoch=not home/tief=home)
gpio_home_button=15             # I am Home PushButton 
gpio_home_led=0                 # Led um Home anzuzeigen, 0 falls nicht vorhanden

total_aktionen_protag=0
debug=0                         # debug flag, von commandline parm


# variablen, die für die Status Abfrage geführt/verwendet werden
status_anzactions=0             # fuer Statusanzeige Anzahl Actions durchgefuehrt seit Start
status_nextaction=[99,""]       # fuer Statusanzeige was wird als naechstes  geschaltet, dosennummer und string
#                               # 99 ist init
status_lastaction=[99,"none"]   # fuer Statusanzeige was wurde zuletzt geschaltet, dosennummer und string
#                               # 99 ist init
status_waitfor=""               # fuer Statusanzeige Zeit der noechsten, in der Zukunft liegenden Aktion
status_currtime=""              # fuer Statusanzeige
status_laueft_seit = 0          # Anzahl Tage die der Switchr gelaufen ist seit letztem Start


start_switcher =0               # datum/zeit Start Switcher
switcher_version=0              # fuer Statusanzeige
hostname = ""
simulation=0                    # no longer used
anz_dosen=0
aktive_saison=0
saison_ist_simuliert=0
saison_simulate=[0,0]           # fuer Simulation der Seasons:   erstes Element: 0=keine Simulation/1=Siumlation
#                                                       zweites Element: welche Season simuliert werden soll
#                               dies wird von Client verlangt und von swipc2.py gesetzt, switcher fragt dies ab.

#

startart=0                  # not used, war daemon stuff
term_verlangt=0             # generelle term Variable, 1 heisst fuer alle Loops: beenden
forground=0                 # wird gesetzt aber nicht verwendet
manuell_reset=0             # aus Configfile: fuer manuell geschaltete Dosen, was tun at midnight
oled_vorhanden=0            # aus Config File not used
testmode=False              # aus Config File: Testmode Ja/Nein

info_fuer_webserver = [0 for z in range(10)]        # Info, die an den Webserver gesandt wird
#
#Nun die wichtigsten Lists of Lists deer ganzen Sauce... hier sind alle Schaltaktionen versorgt
#   List os List of List .... hier werden alle Schaltaktionen versorgt in swparse2.py
#   list_tage: List fuer alle Seasons/Tage/Dosen/Aktionen
#   WICHTIG: NUR diese Liste wird im switcher2 verwendet    <<-----------------
#
#   list_dose:  List fuer alle Seasons/Dosen/Tage/Aktionen
#   WICHTIG:    diese Liste wird nur aufgebaut, damit swlist_action eine Liste ueber alle Dosen erstellen kann.<<-----------------
#               switcher2.py braucht diese Liste nicht.  
liste_aller_tage = []           # Liste aller Tage einer bestimmten Saison
list_aktionen_past =[]          # Liste aller vergangenen Aktionen eines tages
list_aktionen_zukunft =[]       # Liste aller noch zu machenden Aktionen eines Tages
list_tage= [ [] for z in range (3)]     # BIG Lister mit allem drin, Ueber alle Tage und Aktionen
list_dose= [ [] for z in range (3)]     # BIG Liste ueber alle Dosen und alle Tage                                  
list_zimmer=[]                  # liste der gefundenen Zimemr

# Class Instances
mypri=0                         # zeigt auf Instanz der myPrint Class
my_wetter = 0                   # Instanz der Wetter Klasse
mymqtt_client = 0               # instanz der MQTT Klasse
actionpars=0                    # instanz des ActionParsers
ipc_instance=0                  # Instanz der IPC_Server Klasse
dosen=[]                        # list von Doseninstanzen
#                               # note: instanz der ConfigRead Klasse ist nur in initswitcher() verwendet

# Sonstiges
blink_thread=0                  # thread handle
button_thread=0                 # thread handle
wetter_behandeln = False

info_fuer_server = [0 for z in range(12)]     
                                # liste von 10 ints wird als string zum webserver gesandt beim Status request
                                # index 0 : anzahl Dosen 
                                # index 1 : switcher mit wettermessung
                                # index 2-9: for future use


mqtt_ok = 0                     # init lief ok
mqtt_setup = 0                  # MQTT gebrucht in Switcher 2
#
#
# ***** Function Parse commandline arguments ***********************
#----------------------------------------------------------
# get and parse commandline args
def argu():
    global actions_only
    global simday
    global debug
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", help="kleiner debug", action='store_true')
    parser.add_argument("-D", help="grosser debug", action='store_true')
    parser.add_argument("-A", help="ganz grosser debug", action='store_true')
    parser.add_argument("-a", help="Nur Aktionsliste ausgeben", action='store_true')
    parser.add_argument("-p", help="Simulate Saison", default=0, type=int)
   
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

    if args.a: actions_only=1     # nur liste ausgeben

    if args.p >0 :
        saison_simulate[0]=1
        saison_simulate[1]=args.p
 
  # check zusaetzlich args Plausi
    if  saison_simulate[0] > 0 and saison_simulate[1] > 2:   
        print ("Commandline arg -p ist falsche Saison")
        sys.exit(2)
 
    return(args)
    	
# ***********************************************

#-- Function to handle kill Signal (SIGTERM)---------------------
def sigterm_handler(_signo, _stack_frame):
    global term_verlangt
    # Raises SystemExit(0):
    mypri.myprint (DEBUG_LEVEL0,  "SIGTERM/SIGHUP Signal received in switcher2")   # fuer Tests
    term_verlangt=1
    terminate(9)                    #      alles gracefully beenden, dann fertig
    raise SystemExit(2)

#---- Callback, wird aufgerufen, wenn Zuhause Pushbutton gedrueckt wird
# -- jedes druecken des Buttons wechselt den Status
def my_callback_zuhause(channel):
    
    sleep(0.05)                                 # simple debounce
    if GPIO.input(channel) == 0:
        mypri.myprint (DEBUG_LEVEL1,  "--> callback zuhause called, aktiver Zustand: {}".format(zuhause))   # fuer Tests
        do_zuhause()

    return()
    
    

#------ Funktion do_stuff_regular -------------
# was im loop immer gemacht werden muss
def do_stuff_regular():
    global  ret_ipc, ret_dose, term_verlangt, status_laueft_seit
    global time_old,debug
#       dies wird in jedem Lop gemacht    

    if gpio_home_switch >  0:           # kein Kippschalter definiert, also nichts tun
        check_home_kippschalter()           # fuer Switcher mit Kippschalter (kommt bald weg)
    
    ret_ipc, ret_dose, term_verlangt, ret_debug = ipc_instance.ipc_check(build_stat)		# check if request from client came in - and answer it. juni201
#    debug = ret_debug               # uebernehme debug
#    mypri.set_debug_level(debug)   # ausgebaut okt. 2018
    
    mypri.myprint (DEBUG_LEVEL3,  "ipc_check returns: ret_ipc:{}  ret_dose:{}  ret_debug:{}".format(ret_ipc, ret_dose, ret_debug ))

    handle_ipc(ret_ipc,ret_dose)    # behandlung der Antwort
         
    status_laueft_seit = ( date.today() - start_switcher).days     # ermitteln, wieviele Tage der Switcher laeuft

#   check if alive meldung noetig
    time_new =  datetime.now() 
    delta = time_new - time_old
    delta = int(delta.days * 24 * 3600 + delta.seconds)     # delta in sekunden
    mypri.myprint (DEBUG_LEVEL3,  "Check ob alive meldung noetig: delta: {}, laeuft seit Tagen: {}".format(delta,status_laueft_seit))

    if status_laueft_seit <= 2:                     # in den ersten 2 Tagen machen wir alle x min ein Eintrag
        intervall = ALIVE_INTERVALL_1
    else:                                   # nachher nur noch alle 24 Std
        intervall = ALIVE_INTERVALL_2
        
    if delta > intervall:              #   20 minuten vorbei ?
	    time_old = datetime.now()
	    mypri.myprint (DEBUG_LEVEL0,  "bin am leben..")
    
    return



#------ Funktion do_zuhause ----- wird im callback interrupt aufgerufen --------
def do_zuhause():
    global zuhause
    mypri.myprint (DEBUG_LEVEL2,  "--> do_zuhause called")  

    if not zuhause:     #  was ist der aktive status ?
        zuhause=True 
        if gpio_home_led>0:
            GPIO.output(gpio_home_led, True)        # set led on if at home
           
        mypri.myprint (DEBUG_LEVEL1,  "Jemand daheim, nicht manuelle Dosen aus")   
        for dose in dosen:
            dose.set_zuhause()
    else:
        zuhause=False      #  niemand daheim
        if gpio_home_led>0:
            GPIO.output(gpio_home_led, False)        # set led off if NOT at home
        
        mypri.myprint (DEBUG_LEVEL1,  "Niemand daheim, setzt Dosen gemaess Dosenstatus")
        for dose in dosen:
            dose.set_nichtzuhause()
      
    return()	

#-------Funktion fuer Switcher mit Kippschalter zuhause/nicht zuhause----------------
#------- in neuer Version nicht mehr verwendet, da gibt es nutr noch Pushbutton
def check_home_kippschalter():
    global zuhause, zuhause_old
      
    mypri.myprint (DEBUG_LEVEL2,  "--> switcher2 check_home_kippschalter called")
    
    # Home NoHome Switch pruefen
    # check the Home/nothome switch (nicht den pushbutton !)
    zuhause=not GPIO.input(gpio_home_switch)
 
    if zuhause_old != zuhause:   #  has switch changed ?
        zuhause_old = zuhause
        do_zuhause()   
    
    return()


# ***** Function zum Setzen der hier benoetigteh GPIO Pins **********
def gpio_setup(how):                           #         renamed juni2018
    global GPIO
    global gpio_blink, gpio_home_led, gpio_home_switch,gpio_home_button
    
    mypri.myprint (DEBUG_LEVEL3,  "--> gpio_setup() called, blink:{} homeled:{} homeswitch:{}  homebutton:{}".format (gpio_blink,gpio_home_led,gpio_home_switch,gpio_home_switch))	

    if how == 1:             # 1 means setup  / 0 means clenaup
# set all needed pins as output
        if gpio_blink>0:
            GPIO.setup (gpio_blink, GPIO.OUT)   # Pin als Output
        if gpio_home_led>0:
            GPIO.setup (gpio_home_led, GPIO.OUT)   # Pin als Output
            GPIO.output(gpio_home_led, False)        # set led off bei beginn


        if gpio_home_button > 0:
            GPIO.setup(gpio_home_button, GPIO.IN)         # pushbutton zuhause
        else:
            GPIO.setup(gpio_home_switch, GPIO.IN)          # switch Home / not Home
        
        return
        
    
# cleanup alle benoetigten Pins - und nur diese!!
        if gpio_blink>0:
            GPIO.cleanup(gpio_blink)
        if gpio_home_led>0:
            GPIO.cleanup(gpio_home_led)
        if gpio_home_button>0:
            GPIO.cleanup(gpio_home_button)
        else:
            GPIO.cleanup(gpio_home_switch)


# ***** Function blink-led **************************
def blink_led(blink_pin):  # blink led 3 mal und warten  --> in eigenem Thread !!
    global GPIO

    while True:
        for i in range(2):
            GPIO.output(blink_pin, True)
            sleep(0.1)
            GPIO.output(blink_pin, False)
            sleep(0.1)
        for i in range(4):
            if term_verlangt==1: 
                mypri.myprint (DEBUG_LEVEL1,  "Thread blink_led beendet")	# fuer log und debug
                return
            sleep(1)     
    

#--------------baue status Antwort ---------------------------------------
# wird gesandt, wenn Request 'stat' eingetroffen ist.
def build_stat(was):
    
# Achtung: wir reden von Dose 1 bis 4 in der Umgangssprache.
# aber die Liste dosen[] hat index 0 bis (max_anzahl-1)
# darum kommt da immer wieder ein -1 vor !!!

# was = 1: kleiner status verlangt
# was = 2: grosser Status verlangt
# was = 3: Wetter Status verlangt

    global status_lastaction,status_nextaction,status_laueft_seit

#    print (get_size(my_wetter))
    
    status=""
    mypri.myprint (DEBUG_LEVEL2,  "--> build_stat() called, was: {}".format(was))

    convert = (str(w) for w in info_fuer_webserver)     # string aus liste erstellen
    info_string = ''.join(convert)                      # info meldungen an den Webserver
      
    # status string zusammenbauen, die Dosen anfragen.....
    status=""
    scha_stat=""
    for dose in dosen:    
        sta,schalt = dose.show_status().split(':')
        status = status + ' - ' + sta
        scha_stat = scha_stat + ' - ' + schalt       # schaltart sammeln
 #  Text fuer daheim oder abwesend   
    if zuhause:
        daheim="Jemand zuhause"
    else:
        daheim="Niemand zuhause"

    if status_lastaction[0]==99:                # wohl unnoetig 
        zimm_last="Vorlaeufig unbekannt"
    else:
        zimm_last=dosen[status_lastaction[0]-1].get_zimmer()
    if type(zimm_last) is str:
        pass
    else:
        zimm_last=zimm_last.decode()
        
    if status_nextaction[0]==99:
        zimm_next="Vorlaeufig unbekannt"
    else:
        zimm_next=dosen[status_nextaction[0]-1].get_zimmer()
 
    if type(zimm_next) is str:
        pass
    else:
        zimm_next=zimm_next.decode()
        
    sais=actionpars.get_saison_info()
    
# sais sieht so aus:    
#    [
#    ['swhaus1-test', b'01.April', b'18.September', b'Sommersaison', 'Sommer Test 4D Peter'], 
#    ['swhaus1-test', b'28.September', b'03.M\xc3\xa4rz', b'Wintersaison', 'Winter Test 4D Peter'], 
#    ['swhaus1-test', b' ', b' ', b'Zwischensaison', 'Zwischen Test 4D Peter']
#]
    
    mypri.myprint (DEBUG_LEVEL2, "actionpars.get_season_info() bringt:")
    mypri.myprint (DEBUG_LEVEL2, sais)    
    
    mypri.myprint (DEBUG_LEVEL3,  "build_stat aktive Saison ist: {}".format(aktive_saison))
    if aktive_saison == 0:
        and1=1
        and2=2
    elif aktive_saison ==1:
        and1=0
        and2=2
    elif aktive_saison ==2:
        and1=0
        and2=1
  
  

    if was == 1:                            # kleiner Status verlangt

#   Nun die Antwort an den Clienten zusammenstellen           
#   Zuerst die List abfuellen und diese vor dem Senden in ein JSON wandeln
#
#
        stat_klein = status_klein.copy()        # wir müssen kopie machen, da wir später ev. 4 Elemente abschneiden
        stat_klein[0][1] = status[3:]          # Version
        stat_klein[1][1] = status_nextaction[1]         # Naechste Aktion 
        stat_klein[2][1] = sais[aktive_saison][4]   # ControlfileID
        stat_klein[3][1] = daheim                     # zuhause
        
        if wetter_behandeln == 1:
            int,out = my_wetter.get_wetter_data_part()
            stat_klein[4][1] = int                     # zuhause
            stat_klein[5][1] = out                     # zuhause
        else:
            stat_klein.pop()                        # hinterstes Element der Liste weg
            stat_klein.pop()                        # hinterstes Element der Liste weg
        mypri.myprint (DEBUG_LEVEL2,  "build_stat: sais: {}".format(stat_klein))
  
        
        stat_k=json.dumps(stat_klein)          # umwandeln in JSON Object (also ein String)
        return("stad" + info_string + stat_k)     # Meldungs-ID vorne anhaengen (Statusmeldung)
                                             # und fertig

    if was == 2:                            # kleiner Status verlangt
#           es ist offenbar grosser Status verlangt
  
        mypri.myprint (DEBUG_LEVEL3, "build status: lastaction= {}, waitaction= {}".format (status_lastaction,status_nextaction))
        
    #   Nun die Antwort an den Clienten zusammenstellen           
    #   Zuerst die List abfuellen und diese vor dem Senden in ein JSON wandeln
    
        y = 0
        status_gross[y][1]=str(switcher_version) + " / " + hostname         # Version
        y += 1
        status_gross[y][1]=status_laueft_seit           # Start Dat, laeuft seit
        y += 1
        status_gross[y][1]=str(debug)          # Debug Flag
        y += 1
        status_gross[y][1]=str(testmode)          # testmode aus Config-File
        y += 1
        status_gross[y][1]=scha_stat[3:]          # schaltart aus Config-File
        y += 1
        status_gross[y][1]=JANEIN[info_fuer_webserver[1]]      # Switcher Simulation Ja/Nein
        y += 1
        status_gross[y][1]=time.strftime("%d.%B.%Y")           # Aktuelles Datum
        y += 1
        status_gross[y][1]=wochentage[wochentag]           # Aktueller Tag
        y += 1
        status_gross[y][1]=str(total_aktionen_protag)           # Anzahl Aktionen dieses Tages
        y += 1
        status_gross[y][1]=str(status_anzactions)           # Anzahl Aktionen dieses Tages
        y += 1
        status_gross[y][1]=status[3:]           # Dosenstatus
        y += 1
        status_gross[y][1]=status_currtime           # Aktuelle ZeiT
        y += 1
        status_gross[y][1]=status_waitfor          # Warten auf
        y += 1
        status_gross[y][1]=status_lastaction[1]          # Letzte Aktion
        y += 1
        status_gross[y][1]=zimm_last
        y += 1
        status_gross[y][1]=status_nextaction[1]         # Naechste Aktion 
        y += 1
        status_gross[y][1]=zimm_next
        y += 1
        status_gross[y][1]=sais[aktive_saison][3].decode()   # Aktuelle Saison
        y += 1
        status_gross[y][1]=sais[aktive_saison][1].decode() + " / " + sais[aktive_saison][2].decode()         # Von Bis    
        y += 1
        status_gross[y][1]=sais[aktive_saison][4]   # ControlfileID
        y += 1
        status_gross[y][1]=JANEIN[saison_ist_simuliert]   # Saison Simulation Ja/Nein ""  #Simulation Ja/Nein
        y += 1
        status_gross[y][1]=sais[and1][3].decode()   # Aktuelle Saison                     # leer
        y += 1
        status_gross[y][1]=sais[and1][1].decode() + " / " + sais[and1][2].decode()                           # leer
        y += 1
        status_gross[y][1]=sais[and2][3].decode()   # Aktuelle Saison                                # leer
        y += 1
        status_gross[y][1]=sais[and2][1].decode() + " / " + sais[and2][2].decode()                       # leer
        y += 1
        status_gross[y][1]=daheim                     # leer
        y += 1
        status_gross[y][1]=reset_man[manuell_reset]                   
        y += 1
        status_gross[y][1]=" "                   

 #   print (status_gross)
        stati=json.dumps(status_gross)          # umwandeln in JSON Object (also ein String)
        return("stat" + info_string + stati)                               # Meldungs-ID vorne anhaengen (Statusmeldung)
        
    if was == 3:                            # kleiner Status verlangt
#           es ist offenbar Wetter Status verlangt
        if wetter_behandeln == 1:
            stat_g = my_wetter.get_wetter_data_all()
        else:
            li = [[["Wetter Innen", "Ist nicht konfiguriert"]],[["Wetter Aussen", "Ist nicht konfiguriert"]]]
            stat_g=json.dumps(li)          # umwandeln in JSON Object (also ein String)
            print (stat_g)
#        print ("Switcher bekommt: {}, Type: {}".format(retu, type(retu)))
            
        return("wett" + info_string + stat_g)                               # Meldungs-ID vorne anhaengen (Statusmeldung)
         
    

#-------- Behandlung der Antwort, die via IPC vom Client kam - falls es noch was zu tun gibt
#   Parameter (kommen von ipc_check(): funktion und dosennummer
def  handle_ipc(func,wdose):

    global manuell_reset
    
    mypri.myprint (DEBUG_LEVEL2,  "--> handle_ipc() gestartet mit func: %d  wdose: %d" % (func,wdose))	#        juni2018

# Achtung: wir reden von Dose 1 bis 4 in der Umgangssprache.
# aber die Liste dosen[] hat index 0 bis (max_anzahl-1)
# darum kommt da immer wieder ein -1 vor !!!
    
    if func == 0:                    # nix zu tun, swipc2.py hat schon alles abgehandelt
        return
    elif func == 2:
        dosen[wdose-1].set_manuell(1)                   # schalte dose manuel ein
    elif func == 3:
        dosen[wdose-1].set_manuell(0)                   # schalte dose manuel aus
        pass
    elif func == 4:                                     # dose back to normal und notiere modus normal
        dosen[wdose-1].reset_manuell()                   #
    elif func == 5:                                     # dose back to normal und notiere modus normal
        for i in range(len(dosen)):                     # alle dosen manuell ein
            dosen[i].set_manuell(1)
    elif func == 6:                                     # dose back to normal und notiere modus normal
        for i in range(len(dosen)):                     # alle dosen manuell aus
            dosen[i].set_manuell(0)
        pass
    elif func == 7:                                     # dose back to normal und notiere modus normal
        for i in range(len(dosen)):                     # alle dosen manuell aus
            dosen[i].reset_manuell()
        pass
    elif func == 8:                                     # reset manuelle um Mitternacht
        manuell_reset=1
        pass
    elif func == 9:                                     # Reset Manuelle nie
        manuell_reset=0
        pass      
    elif func == 10:                                     # xor zuhause
        do_zuhause()
        pass      
    
    else:
        mypri.myprint (DEBUG_LEVEL0, "handle_ipc:  falsche func: {}".format(func))

    
    return
    
#****************************************************
#   juni2018
#   Nun feststellen, welche Jahres-Season es momentan ist (Sommersaison/Wintersaison/Zwischensaison)
def get_saison():
    global xmlfile_id
    global saison_simulate

#    saison_simulate[0]=1
#    saison_simulate[1]=1
    sim=0;
    season_ret = [0,0,0,0]
    mypri.myprint (DEBUG_LEVEL1,  "--> get_saison() gestartet")
    season_ret = actionpars.check_saison(saison_simulate)               # ermittle die Saison
    mypri.myprint (DEBUG_LEVEL3, "check_saison() meldet: {}".format(season_ret))
    if  season_ret[0] > 6:                      # hier ist 4 abzuziehen, alles was danach >6 ist Fehler
        print ("Error in ermitteln season")     # ansonsten wird die aktuelle Saison zurueckgegeben
    else:
        mypri.myprint (DEBUG_LEVEL1,  "gemeldete Saison: %s" % season_ret[1])
    if season_ret[2]:
        mypri.myprint (DEBUG_LEVEL1,  "Saison ist simuliert")
        sim = 1
    else:
        mypri.myprint (DEBUG_LEVEL1,  "Saison ist NICHT simuliert")
    
    xmlfile_id = season_ret[3]                  # abfuellen der ID aus dem ML File
    aktive_s = int(season_ret[0])
    mypri.myprint (DEBUG_LEVEL1,  "--> get_saison() beendet, saison ist: {}". format (aktive_s))	#        juni2018    
    return (aktive_s, sim)
    
#  Ende Saisonermittlung -------  juni2018 
#****************************************************

    
# Funktion Dosen kurz einschalten (nur bei testmode="Ja" im configfile)
#------------------------------------------------
def test_dosen():

#  mache dies nicht bei Testmode  Nein und auch nur bei schaltart =1 (testbett)
    if  not testmode:
        return
     
    mypri.myprint (DEBUG_LEVEL1,  "switcher2 testmode=Ja in Configfile=1, also mache Test_dosen")
          
    for dose in dosen:          
        dose.set_auto(1)
        sleep(0.5)
        dose.set_auto(0)
    mypri.myprint (DEBUG_LEVEL2,  "Test_dosen done")
    sleep(0.7)

#  --- Funktion zum Erstellen Liste aller Tage für bestimmte Saison
def alle_tage_pro_saison (liste, saison):
    mypri.myprint (DEBUG_LEVEL2,   "--> alle_tage_pro_saison() called")
    tages_liste = []
    for n in liste[saison]:
        tages_liste.append(n)
    return(tages_liste)

#  --- Funktion zum Erstellen von zwei Listen ----------------
#		a: Liste aller vergangenen 	Aktionen eines Tages
#		b: Liste aller zukünfigen 	Aktionen eines Tages
#		basierend auf aktueller Zeit
def aktionen_pro_tag (liste, wochentag):
    mypri.myprint (DEBUG_LEVEL2,   "--> aktionen_pro_tag() called")

    hhmm_tag = [datetime.now().strftime("%H.%M"),datetime.today().strftime("%w")]    # aktuelle Zeit holen
#	print (hhmm_tag)
    new_list_vergangen = []
    new_list_zukunft =[]
#	print ("liste-wochentag: {}".format(liste[wochentag]))
    for n in liste[wochentag]:
#		print ("n ist: {}".format(n))				# ist aktion
        if hhmm_tag[0] > n[0]:						# hhmm_tag[0] sind Stunden.Minuten, check Actions times to current time
            new_list_vergangen.append(n)		# addiere zur Liste vergangene Aktionen
        else:								
            new_list_zukunft.append(n)				# addiere zur Liste der zukünftigen Aktionen
    return(new_list_vergangen, new_list_zukunft)	# gebe beide Listen zurück
	


#  -------- Function INit ------------------------
def initswitcher(start):
    global actions_only,wochentag
    global GPIO, dosen
    global list_tage,list_dose
    global mypri,ipc_instance
    global debug                # hier global deklariert, weil veraendert wird in dieser Funktion
    global zuhause, zuhause_old
    global actionpars, anz_dosen
    global start_switcher,manuell_reset,switcher_version,startart
    global gpio_home_switch,gpio_home_button,gpio_home_led, gpio_blink, oled_vorhanden, testmode
    global blink_thread,term_verlangt, hostname
    global python_version
    global button_thread
    global info_fuer_webserver
    global mymqtt_client, mqtt_ok, mqtt_setup, wetter_behandeln, my_wetter

#  posit kein keyboard IR
    try:
        startart = start                      # 0= gestartet in switcher2.py / 1= gestartet mit daemon
        start_switcher = date.today()
        error = 0
        term_verlangt = 0
        tmp = 0 
        fortschritt = 0   

        path1 = os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script laeuft
        mypri = MyPrint("switcher2","../switcher2.log",debug)    # Instanz von MyPrint Class erstellen
        hostname = socket.gethostname()                                         # uebergebe appname und logfilename
        if version_info[0] < 3:
            python_version=2
        else:
            python_version=3       
    
        if version_info[0] < 3:
            mypri.myprint (DEBUG_LEVEL0, "switcher2.py laeuft nur richtig unter Python 3.x, du verwendest Python {}".format(version_info[0]))
            error = 9
            return(error);
    
        switcher_version=__VERSION__
        #  get full path of appfile                     juni2018
        path = os.path.realpath(__file__)   
    #  get directory of file
        dirname = os.path.dirname(path)
        modulename = path.replace(  dirname+"/", "")      # juni2018
        
        mypri.myprint (DEBUG_LEVEL0,  "Gestartet: {} Version: {} Python: {}  Startart: {}  Hostname: {}".format (modulename,switcher_version, python_version, startart,hostname))   # print signatur                                                           
        mypri.myprint (DEBUG_LEVEL0,  "--> Initswitcher gestartet")	# wir starten       juni2018
    
        config = ConfigRead(debug)        # instanz der ConfigRead Class
        
        signal.signal(signal.SIGTERM, sigterm_handler)  # setup Signal Handler for Term Signal
        signal.signal(signal.SIGHUP, sigterm_handler)  # setup Signal Handler for Term Signal
        if debug > 0:
            mypri.myprint (DEBUG_LEVEL1,  "Switcher Debug-Output verlangt")	# wir starten       juni2018
    
        configfile=path1 + "/swconfig.ini"
        ret=config.config_read(configfile,"switcher",cfglist_swi)
        if ret > 0:
            print("config_read hat retcode: {}".format (ret))
            sys.exit(2)
    # fertig behandlung confifile
       
       
    # holen diverser Dinge aus der Config-Struktur   
        testmode = False
        y = cfglist_swi.index("testmode")  + 1           # suche den Wert von testmode aus Config-file
        testmode = cfglist_swi[y].decode()
        if  testmode.find("Ja") != -1: 
            testmode = True
            mypri.myprint (DEBUG_LEVEL0, "switcher2 im Config-File testmode=Ja gefunden")
        else:
            testmode = False
    
        y = cfglist_swi.index("setup_mqtt")  + 1     # suche den Wert setup_mqtt aus Config-file
        mqtt_setup = int(cfglist_swi[y])

        y = cfglist_swi.index("wetter")  + 1     # suche den Wert wetter aus Config-file
        wetter_behandeln = int(cfglist_swi[y])

    
        y = cfglist_swi.index("gpio_home_switch")  + 1     # suche den Wert von gpio_home_switch aus Config-file
        gpio_home_switch = int(cfglist_swi[y])
    
        y = cfglist_swi.index("gpio_home_button")  + 1     # suche den Wert von gpio_home_switch aus Config-file
        gpio_home_button = int(cfglist_swi[y])
    
        y = cfglist_swi.index("gpio_home_led")  + 1           # suche den Wert von gpio_home_led aus Config-file
        gpio_home_led = int(cfglist_swi[y])
    
        y = cfglist_swi.index("gpio_blink")  + 1           # suche den Wert von gpio_blink aus Config-file
        gpio_blink = int(cfglist_swi[y])
    
        y = cfglist_swi.index("oled")  + 1           # suche den Wert von oled aus Config-file
        oled_vorhanden = int(cfglist_swi[y])
    
        y = cfglist_swi.index("manuell_reset")  + 1           # suche den Wert von manuall reset aus Config-file
        manuell_reset = int(cfglist_swi[y])
     
        
        if manuell_reset== 1:   # manuelle schaltungen nur bis Mitternacht
            mypri.myprint (DEBUG_LEVEL1,  "Manuelle Schaltungen nur bis Mitternacht")#	      juni2018
        
        if gpio_home_button >0:             # wenn button definiert ist, wird kippschalter ignoriert
            gpio_home_switch = 0
    
    
           #Use BCM GPIO refernece instead of Pin numbers
        GPIO.setmode (GPIO.BCM)
        rev = GPIO.RPI_REVISION
        GPIO.setwarnings(False)             # juni2018 ist neu hier, war in gpio_setup()
    
        gpio_setup(1)  # set GPIO Pins zum Senden  juni2018  renamed
    
        fortschritt = 1
    
        mypri.myprint (DEBUG_LEVEL1, "switcher2 GPIO-Homeswitch: {} GPIO-Homebutton: {} GPIO-Homeled: {} GPIO-Blink: {} Oled: {} ".format(gpio_home_switch,gpio_home_button,gpio_home_led,gpio_blink,oled_vorhanden))
    
    #  vorlaeufug alles aus dem Configfile entnommen
    
        if gpio_home_switch > 0:            # fuer backwards compatibilty mit kippschalter
            zuhause=not GPIO.input(gpio_home_switch)
        if  zuhause :                        # check switch, False means niemand da.
                                            # True means high potential means jemand zuhause - regular betrieb
            mypri.myprint (DEBUG_LEVEL1,   "Jemand zuhause, do nothing")	# wir starten
    
        # ENDE check the Home/nothome switch 
       
       
        # falls ein pushbutton definiert ist fuer zuhause toggle
        if gpio_home_button >0:
            GPIO.add_event_detect(gpio_home_button, GPIO.FALLING, callback = my_callback_zuhause, bouncetime = 300)
    
    # wenn gpio blink angegeben ist (ungleich 0) starten wir den Blink Thread <<---
        if gpio_blink > 0:
            blink_thread = threading.Thread(target=blink_led, args=(gpio_blink,))
            blink_thread.setDaemon (True)                       # damit thread beendet wird, wenn main thread endet
            blink_thread.start()
    #  der Blink Thtread beendet sich bei term_verlangt=1    

        mqtt_ok = 0
        
        if wetter_behandeln == 1:
            info_fuer_webserver[1] = 1
            mqtt_setup = 1
            
            
        if mqtt_setup == 1:            
# Nun wissen wir, ob MQTT Connection nötig ist:
# entweder weil Wetter konfiguriert ist oder weil mind. einen Dose Schaltart 3 hat.
            mypri.myprint (DEBUG_LEVEL1,"MQTT noetig oder verlangt: {}".format(JANEIN[mqtt_setup]))

            mymqtt_client = MQTT_Conn (debug, path1, "switcher2")            
            mqtt_ok = 1


        if wetter_behandeln == 1:                 # wetter ist verlangt, also kreiere instanz der Wetter  Klasse
            my_wetter = Wetter (debug, path1, mymqtt_client)               
                                         # suscriptions werden in der Klasse wetter gemacht            
        fortschritt = 2    
    
    #   Einlesen und Parsen der Steuer-Files fuer alle Seasons             alles neu juni2018
    #   Falls debug output verlangt ist, wird dies fuer das parse-module ausgeschaltet (dieses bringt viel output)
    #   Das Parse Module kann gut stand-alone mit Aufruf von swlist_action2.py debugged werden.
        mypri.myprint (DEBUG_LEVEL1,   "Debugging aus fuer Parse-Module - dies kann mit swlist_action2.py debugged werden.")	
        tmp_debug = debug                # save current debuglevel         #   juni2018
        debug = DEBUG_LEVEL0 
        actionpars = ActionParser(debug,path1)      # Instanz der ActionParser Class
    #    
    # Einlesen und Parsen der Steuer-Files fuer alle Seasons             alles neu juni2018
        ret = actionpars.get_files(list_tage,list_dose,list_zimmer,cfglist_swi)
        if ret > 0:
            mypri.myprint (DEBUG_LEVEL0, "Methode get_files bringt errorcode: {}, kann nicht weiterfahren".format(ret))
            return(ret)
    #
    #   nun sind alle Aktionen aus den XML-Files eingelesen und versorgt in den Listen list_tage, list_dosen und zimmer
    #
        debug = tmp_debug                # reset debuglevel for switcher
        actionpars.set_debug(debug)     # reset debug in actionpars
    
    # Anzahl Dosen feststellen: loop ueber alle Saisons, alle Tage und schauen, wo maximum ist
        anz_dosen = 0
        for y in range (len(list_dose)):
            for i in range (len(list_dose[0])):
                anz =  (len(list_dose[0][i]))
                if anz >  anz_dosen: anz_dosen=anz
        anz_dosen -= 1      # liste hat 5 elemente , es gibt aber -1 dosen
        mypri.myprint (DEBUG_LEVEL1, "Beim Parsen wurden maximal {} Dosen gefunden".format( anz_dosen))
        info_fuer_webserver[0] = anz_dosen
    
        
        mypri.myprint (DEBUG_LEVEL1,  "switcher2: Files parsed, nun geht es los...")	# wir starten
        if actions_only: 
            mypri.myprint (DEBUG_LEVEL1,  "switcher2 Files parsed, nur Aktionsliste drucken...")	# 
            actionpars.print_allactions(list_tage,list_dose)
            sys.exit(2)
    
        zeit = str(datetime.now().strftime("%H.%M"))
        mypri.myprint (DEBUG_LEVEL1,  "Starting with Wochentag: %s / Zeit: %s " % (datetime.today().strftime("%w-%A"), zeit	))	
        if rev == 1:
            mypri.myprint (DEBUG_LEVEL1,  "GPIO-Version 1 has different port numbering - please check program !")
            mypri.myprint (DEBUG_LEVEL1,  "Program was developed for Rev2 and later.")
        mypri.myprint (DEBUG_LEVEL1,  "Raspberry GPIO-Version: %1.1f" % rev)	
        startdat = "%s %s"  % (datetime.today().strftime("%A"), datetime.now().strftime("%d.%m.%Y %H.%M"))
    
         
    #    print (actionpars.__dict__)                            # fuer Tests
    #    print (swparse2.ActionParser.__dict__)
       
        ret = actionpars.check_saison_init()         # zuerst init der Seasonermittlung
        if ret > 0:
            mypri.myprint (DEBUG_LEVEL0,  "Switcher2 beendet wegen Fehler")	# wir starten       juni2018
            sys.exit(2)


        # init switching in der Klasse Dose.py
        # also n Instanzen der Klasse Dose erstellen    
    
        for i in range(anz_dosen):
            dos = Dose(i, testmode, debug, path1, mqtt_ok, mymqtt_client)
            if dos.errorcode == 99:
                mypri.myprint (DEBUG_LEVEL1,  "Dose: {} meldet Fehler {}".format (i+1, dos.errocode))	 
                raise RuntimeError('--> Switcher ernsthafter Fehler, check switcher2.log <----')
            else:
                dosen.append(dos)           # es wird dose 1 bis anz_dosen 
        fortschritt = 3    
     
    #   nun die gefundenen Zimmernamen (aber nur der esten Saison (Sommer) in die Dosen schreiben     
        for i, dose in enumerate(dosen):    
     #       dose.set_zimmer(list_zimmer[i].encode(encoding='UTF-8'))           # keep this
            dose.set_zimmer(list_zimmer[i])
    
            zi = dose.get_zimmer()
            mypri.myprint (DEBUG_LEVEL2,  "Dose: {}  Zimmername gesetzt: {}".format (i+1, zi))	 
          
        test_dosen()                # Dosen kurz ein/aus beim Testen

        # init Interprocess Communication in swipc.py
        ipc_instance = IPC_Server(cfglist_swi,debug)      # instantiieren der Class IPC_Client             # juni2018

        if ipc_instance.get_result() > 0:             # hole result von IPC
            raise RuntimeError                         # Socket Connection nicht ok
        
        fortschritt = 4        
        count_thread = threading.active_count()
        thread_list = threading.enumerate()
        
        mypri.myprint (DEBUG_LEVEL1,"Anzahl Threads: {},  List: {}".format(count_thread,thread_list))
        mypri.myprint (DEBUG_LEVEL1,"Info fuer Webserver: {}".format(info_fuer_webserver))
        
#    sys.exit(2)    # for Tests only !!


    except KeyboardInterrupt:
    # aufraeumem
        mypri.myprint (DEBUG_LEVEL0,  "Keyboard Interrupt in initswitcher, alle Dosen OFF und clean up pins")
        error = 9
        term_verlangt = 1                       # signale to thread to stop
        if fortschritt > 0:
            terminate(fortschritt)
    except Exception:
        #       etwas schlimmes ist passiert, wir loggen dies mit Methode myprint_exc der MyPrint Klasse
        mypri.myprint_exc ("initswitcher: etwas Schlimmes ist passiert.... !")
        error = 9
        term_verlangt = 1                       # signale to thread to stop
        if fortschritt > 0:
            terminate(fortschritt)
    finally: 
    # hierher kommen wir immer, ob Keyboard Exception oder andere Exception oder keine Exception
    
        if mqtt_setup == 1:                     # letzte Aktion vor Ende Init: start mqtt Loop
            mymqtt_client.mqtt_start()

                
        mypri.myprint (DEBUG_LEVEL0,  "--> Initswitcher done")	# wir starten       juni2018
        return(error)




# End Function initswitcher**************************


# --- here is the beef  -------------------------------------------------------------
def runswitch():

    global debug,actions_only,wochentag,status_currtime
    global hhmm_tag  , start_tag                  
    global list_tage,list_dose,status_anzactions,status_waitfor,status_lastaction,status_nextaction
    global total_aktionen_protag, term, manuell_reset,term_verlangt, time_old
    global aktive_saison, saison_ist_simuliert, liste_aller_tage
    global list_aktionen_past, list_aktionen_zukunft

#  -- Funktion: warten bis der nächste wochentag wirklich eintrifft ------------------------------
    def warte_bis_tag_da(wochentag):
        global status_currtime
        mypri.myprint (DEBUG_LEVEL2,   "--> warte_bis_tag_da() called. Es ist tag: {}".format(wochentag))
        while True:
            hhmm_tag = [datetime.now().strftime("%H.%M"),datetime.today().strftime("%w")]  # aktuelle Zeit holen
            status_currtime = hhmm_tag[0]               # fuer status request ===============  juni2018

            wochentag_neu = int(hhmm_tag[1])            # get new weekday
            if wochentag_neu != wochentag:              #  ist neuer Tag ?
                mypri.myprint (DEBUG_LEVEL1,   "Neuer Tag ist da: {}".format(wochentag_neu))
                return (wochentag_neu)
            sleep(SLEEPTIME_DONE)
            mypri.myprint (DEBUG_LEVEL2,   "Timemarching warte auf neuen tag, immer noch tag {} / {}".format(hhmm_tag[1], hhmm_tag[0]))

            do_stuff_regular()
            if  term_verlangt==1:  
                mypri.myprint (DEBUG_LEVEL2,   "Switcher2 wartend auf neuen Tag finds term_verlangt=1")
                return (5)                              # gebe irgendwas zurück, der form halber    
 # --------------------------------------------------       
  
#  --Funktion: warten auf die Zeit der nächsten Aktion ------------------------------
    def warte_bis_zeit_da(zeit):
        global status_currtime

        hhmm_tag = [datetime.now().strftime("%H.%M"),datetime.today().strftime("%w")]    # aktuelle Zeit holen
        mypri.myprint (DEBUG_LEVEL2,   "--> warte_bis_zeit_da() called. naechste Aktion um: {}".format(zeit))

        while True: 
            if hhmm_tag[0] >= aktion[0]:	            #	pruefe ob jetzt die Zeit da ist fuer aktuelle Aktion		
                return
                mypri.myprint (DEBUG_LEVEL1,   "neue Zeit ist da: {}".format(aktion[0]))
                return
            sleep(SLEEPTIME_DONE)
            hhmm_tag = [datetime.now().strftime("%H.%M"),datetime.today().strftime("%w")]    # aktuelle Zeit holen
            mypri.myprint (DEBUG_LEVEL2,   "Timemarching warte auf zeit {}, jetzt ist {}".format (zeit, hhmm_tag[0]))
            status_currtime = hhmm_tag[0]               # fuer status request ===============  juni2018

            do_stuff_regular()                          # mache diese sachen regelmässig...
            if  term_verlangt==1:  
                mypri.myprint (DEBUG_LEVEL2,   "Switcher2 wartend auf neue zeit finds term_verlangt=1")
                break    
                
            pass
 # -------------------------------------------------      
   
   
   # hier beginnt runswitch() ------------------------
    if debug: 
        sleep(3) 
      
    hhmm_tag = [datetime.now().strftime("%H.%M"),datetime.today().strftime("%w")]    # aktuelle Zeit holen
    mypri.myprint (DEBUG_LEVEL0,   "--> Switcher2 Function runswitch(): start switching. Zeit und Wochentag: {}".format(hhmm_tag))

    time_old = datetime.now()                           # fuer Zeitmessung

    aktive_saison, saison_ist_simuliert = get_saison()  # Saison des Jahres ermitteln
    start_tag = int(hhmm_tag[1])                        # heutiger wochentag, starte damit, loop bis tag 6

# aus der grossesn Liste (list_tage) extrahieren: alle Tage der aktuellen Saison
    liste_aller_tage = alle_tage_pro_saison( list_tage, aktive_saison )
# dann extrahieren von vergangenen und zukünftigen Aktionen (gemessen an der Startzeit des Switchers)    
    list_aktionen_past, list_aktionen_zukunft = aktionen_pro_tag (liste_aller_tage, start_tag )

# --  Zuerst die vergagenen Aktionen des Tages behandeln ---
#     dies, falls der Switcher in Laufe des Tages gestartet wird  - damit Status der Dosen aktuell ist
#     gibt es also nur bei Neustart innerhalb des Tages !!!
    mypri.myprint (DEBUG_LEVEL0,   "behandle vergangene aktionen, anzahl: {}".format(len(list_aktionen_past)))
    status_anzactions = 0                               # fuer statusanfrage
    for aktion in list_aktionen_past:                   # liste der vergagnenen aktionen des tages
        dosennu = int(aktion[1])
        ein_aus = int(aktion[2])
        dosen[dosennu-1].set_auto_virtuell(ein_aus)     #   <<<<--------------- schalte die Dose virtuell         uni2018    
                                                        # bei Funkschaltung wollen wir nicht so lanke funken, bis alles abgearbeitet ist      
        status_anzactions+=1                            # increment anzahl getaner Aktionen                

        status_lastaction[1] = "Zeit: %s Dose: %s / %s" % (aktion[0],aktion[1], ONOFF[aktion[2]]  ) 
        status_lastaction[0] = aktion[1]
        status_currtime = hhmm_tag[0]                   # fuer status request ===============  juni201
#       da wir bislang die vergangenen Aktionen virtuell geschaltet haben - also bloss den internen Status gesetzt haben,
#       muessen wir nun noch die Dosen gemaess diesen Stati wirklich schalten.
    for dose in dosen:
        dose.set_nichtzuhause()
        
    mypri.myprint (DEBUG_LEVEL0,   "vergangene aktionen sind erledigt")
# ---- Alle vergangenen Aktionen des Tages erledigt. Nun gehts ans Schalten..
    
    
#  ---- Main Loop -----------------------------------------------------------   

# posit: solange, falls kein Ctlr-C kommt
    try: 
        while True:                                     # MAIN-LOOP  run forever
                                                        # check termination from daemon - signalled via global variable    
            if  term_verlangt==1: break                 # break from main Loop
            mypri.myprint (DEBUG_LEVEL1,   "MAIN-LOOP: starte mit wochentag: {}".format(start_tag))
            
 # LOOP-1 -----------  Loop ueber alle Tage ab start_tag ---------------           
            for wochentag in range(start_tag, 7):
                
                total_aktionen_protag = len (list_aktionen_past) + len(list_aktionen_zukunft)
                if debug:  
                    mypri.myprint (DEBUG_LEVEL1,   "Arbeite an Wochentag: {} hat {} Aktionen, davon {} vergangene bereits erledigt".format( wochentag, total_aktionen_protag, len(list_aktionen_past)) )
                    sleep(2)

                mypri.myprint (DEBUG_LEVEL1,   "Starte Aktionen_loop")

#----- LOOP-2 ueber alle restlichen Actions eines Tages --------------------------------------------------
                for aktion in list_aktionen_zukunft:       
                
                    status_nextaction[1] = "Zeit: %s Dose: %s / %s" % (aktion[0],aktion[1], ONOFF[aktion[2]])
                    status_nextaction[0] = aktion[1]    # fuer status request ===============
                    status_waitfor = aktion[0]          # fuer status request  Zeit auf die wir warten als String===============
                
                    warte_bis_zeit_da (aktion[0])       # hierin wird gewartet, is die Zeit reif ist...
                                   
# ++++++++++++ Hier wird geschaltet +++++++++++		
#  ++++++++++++	Fuehre Aktion aus (Ein oder Aus schalten einer Dose)  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++		
                    mypri.myprint (DEBUG_LEVEL2,  "Schalten der Dose: %d  Zeit: %s %s" % ( aktion[1], aktion[0], ONOFF[aktion[2]]  ))				                         
                    dosennu = int(aktion[1])
                    ein_aus = int(aktion[2])
                    dosen[dosennu-1].set_auto(ein_aus) 
#                                      
#  ++++++++++++ Schalten  fertig ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  ++++++++++++++++++++++++++++++++

#  nun status setzen für Statusanfrage
                    status_lastaction[1] = "Zeit: %s Dose: %s / %s" % (aktion[0],aktion[1], ONOFF[aktion[2]]  ) 
                    status_lastaction[0] = aktion[1]
                    status_anzactions+=1                # increment anzahl getaner Aktionen                

                    sleep(SLEEPTIME)
                    if  term_verlangt==1:               # check in outer loop
                        mypri.myprint (DEBUG_LEVEL2,   "\ninner Loop finds term_verlangt=1")
                        break                       

#----- Ende LOOP-2 ueber alle restlichen Actions eines Tages --------------------------------------------------
                         
                pass
                # hier kommt man, wenn alle Aktionen des aktuellen tages gemacht sind
                # Der Tag ist aber noch nichht vorbei...
                mypri.myprint (DEBUG_LEVEL1,  "All Actions done for day %d , waiting for new day" % wochentag)
                sleep(SLEEPTIME)
#   back in the Main Loop again  
#   hier sind alle aktionen eines Tages abgearbeitet und und der Tag hat geaendert
#   wir loopen bis der Tag wirklich wechselt.
#   fuer den aktuellen Tag gibt es nichts mehr zu tun.....
#   das muss im Status angegeben werden - ueber den naechsten Tag wissen wir nichts
                if  term_verlangt == 1:  
                    mypri.myprint (DEBUG_LEVEL2,   "Switcher2 LOOP-1 finds term_verlangt=1")
                    break                                   # break loop ueber alle actions des Tages


        # wir warten auf den neuen Tag und es gibt keine Aktionen mehr fuer den aktuellen Tag
        # setzen angaben fuer statusabfrage. Wir wissen noch nicht, welche Aktion dann im neuen Tag kommen wird
                status_waitfor = "Neuer Tag"                     
                status_nextaction[1] = "Vorlaeufig unbekannt"      
                status_nextaction[0] = 99                   # damit zimmer unbekannt gesetzt wird    
                status_anzactions = 0                       # anzahl getaner Aktionen pro Tag
                wochentag = warte_bis_tag_da(wochentag)     # hierin wird gewartet, bis der neue tag kommt (mitternacht)

                if  term_verlangt == 1:  
                    mypri.myprint (DEBUG_LEVEL2,   "Switcher2 LOOP-1 finds term_verlangt=1")
                    break                                   # break loop ueber alle actions des Tages
                        
                aktive_saison_old = aktive_saison
                aktive_saison, saison_ist_simuliert = get_saison()     # Saion des Jahres ermitteln
                if aktive_saison != aktive_saison_old:
                    liste_aller_tage = alle_tage_pro_saison( list_tage, aktive_saison )   # liste neu erstellen (neue saison)             
                        
                list_aktionen_past, list_aktionen_zukunft = aktionen_pro_tag (liste_aller_tage, wochentag )
                                       
                                                            # manuell im configfile: 0= forever, 1=nur bis Mitternacht)                                          
                if manuell_reset==1:                        # war manuell im confifile auf 1 ?
                    mypri.myprint (DEBUG_LEVEL1,   "Neuer Tag, loesche manuelle Modi, ist verlangt in Config-File")
                    for dose in dosen:                      # ueber alle dosen
                        dose.reset_manuell()                # rufe die dose auf
                else:
                    mypri.myprint (DEBUG_LEVEL1,   "Neuer Tag, NICHT loeschen der manuellen Modi, ist verlangt in Config-File")
                        
                pass
             
# Ende LOOP-1-----------------------  alle Tage vorbei
    
            start_tag = 0           # fuer neuen durchlauf Main Loop , wir starten dann bei wochentag = 0 (Sonntag)
# Ende Main Loop 
#----------------------------------------
#  Dieser Main Loop wird nur beendet, wenn variable term_verlangt=1 ist oder
#  wenn ein Keyboard interrupt kommt, ctrl-c ----

        mypri.myprint (DEBUG_LEVEL1, "--> Main Loop beendet, wir kommen zum Ende")

    except KeyboardInterrupt:
    # aufraeumem
        mypri.myprint (DEBUG_LEVEL0,  "Keyboard Interrupt, alle Dosen OFF und clean up pins")
        term_verlangt=1
    except Exception:
        #       etwas schlimmes ist passiert, wir loggen dies mit Methode myprint_exc der MyPrint Klasse
        mypri.myprint_exc ("Etwas Schlimmes ist passiert.... !")
        term_verlangt=1
    finally:
    # hierher kommen wir immer, ob Keyboard Exception oder andere Exception oder keine Exception
        mypri.myprint (DEBUG_LEVEL1, "finally reached, term_verlangt={}".format(term_verlangt))
    
        terminate(9)
    
# End Funtion runswitch ********************************

#*********  endebehandlung **********
def terminate(was):
    global GPIO, ipc_instance, mymqtt_client, my_wetter
#
    mypri.myprint (DEBUG_LEVEL0,   "--> terminate() called, was: {}".format(was))			

    if was > 0:
        gpio_setup(0)                   # cleanup GPIO Pins, nur die hier verwendeten Pins   juni2018
    if was > 1:
        blink_thread.join()
    if was > 2:
#           Dosen ausschalten
        for i in range(anz_dosen):
            dosen[i].set_manuell(0)
        for i in range(len(dosen)):     # dosen zerstoeren
            del dosen[0]
            pass
            
    if was > 3:
        del ipc_instance                # terminating INterprocess-Communication, Sockets und so....juni2018
        if mqtt_setup > 0 :
            mymqtt_client.mqtt_stop()   # mqtt client beenden
            del mymqtt_client
        del my_wetter
    mypri.myprint (DEBUG_LEVEL0,   "switcher2 terminating")
    sys.exit(2)                         #  fertig lustig

  # terminating switching    juni2018

#************************************    
	
# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#

    forground=1     # zeigt, dass Programm im Vordergrund laeuft, Main wurde gerufen
    options=argu()                          # get commandline args
    ret=initswitcher(0)  # init stuff, parameter 0 heisst : im switcher2.py gestartet
    if ret==9:
        sys.exit(2)
    runswitch()         #  here is the beef, runs forever
    
    terminate(9)         #  Abschlussvearbeitung

#**************************************************************
#  That is the end
#***************************************************************
#