#!/usr/bin/python3
# coding: utf-8
#
# *******************************************************************
#   Python Webservers auf Basis flask für  Switcher2
#   Einfacher geht es gar nicht mehr.......
#
#  
#   Anleitung hier
#   https://prateekvjoshi.com/2016/03/08/how-to-create-a-web-server-in-python-using-flask/
#
#
# ----> läuft nur mit python3 !!!!!!!!!!
# 
#
#   Eine coole Sache !
#   siehe hier: https://www.sigmdel.ca/michel/program/python/python3_venv_01_en.html
#   
#   Juli 2018, PBX
#*********************************************************************
#
# import zmq_client
from flask import Flask
from flask import render_template,  request
from sub.swipc import IPC_Client        # class IPC_Client
import json
import signal, os
from time import sleep
from sub.swcfg_switcher import cfglist_swi
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.configread import ConfigRead
import sys
from sys import version_info
import argparse
import subprocess

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

# Info die vom switcher2 geliefert wird und welche für den Server wichtig ist
anz_dosen_konfiguriert = 0
wetter_konfiguriert = 0
reserve1 = 0
reserve2 = 0

                
                
REQUEST_TIMEOUT=3500
REQUEST_RETRIES=3
debug=0
ipc=0
mypri=0
AKTION=["Eingeschaltet","Ausgeschaltet","Zurückgesetzt auf Auto"]
app = Flask(__name__)
pfad =""
info_fuer_webserver = []
                                    # liste von 10 ints wird als string vom Switcher gesandt beim Status request
                                    # index 0 : anzahl Dosen 
                                    # index 1 : switcher mit wettermessung
                                    # index 2-9: for future use
anzdosn_gemeldet = 0;
wetter_konfiguriert = 0;

#  liste der html files: für Auswahl der Anzahl konfigurierten Dosen
select_anzdosen_htmlfiles = [
            "empty",
            "anzdosen_select1.html",
            "anzdosen_select2.html",
            "anzdosen_select3.html",
            "anzdosen_select4.html",
            "anzdosen_select5.html",
            ]

#  liste der html files: für Schalten der Dosen, verschieden Anzahl Dosenw
select_dosenschalt_htmlfiles = [
            "empty",
            "dosen_schalt1.html",
            "dosen_schalt2.html",
            "dosen_schalt3.html",
            "dosen_schalt4.html",
            "dosen_schalt5.html",
            ]
            
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

#--------------------------------------------
def setup_server():
    global mypri, ipc_data, pfad
    error=0
    
    signal.signal(signal.SIGTERM, sigterm_handler)  # setup Signal Handler for Term Signal
    pfad=os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft
    mypri=MyPrint("swserver2","../switcher2.log",debug)    # Instanz von MyPrint Class erstellen
                                                        # übergebe appname und logfilename
    config=ConfigRead(debug)        # instanz der ConfigRead Class

    ret=config.config_read(pfad + "/swconfig.ini","switcher",cfglist_swi)
    if ret > 0:
        mypri.myprint (DEBUG_LEVEL0, "config_read hat retcode: {}".format (ret))
        error=8

    if version_info[0] < 3:
        mypri.myprint (DEBUG_LEVEL0, "swserver2.py läuft nur richtig unter Python 3.x, du verwendest Python {}".format(version_info[0]))
        error=9

    try:
        u=cfglist_swi.index("ipc_endpoint_c")  + 1           # suche den Wert von oled aus Config-file
        ipc_data=int(cfglist_swi[u])
    except:
        ipc_data= "tcp://localhost:5555"

    mypri.myprint (DEBUG_LEVEL0, "--> swserver2.py gestartet, ipc_endpoint:{}".format(ipc_data))
    mypri.myprint (DEBUG_LEVEL1, "swserver2.py setup Server done")
    return(error);

#-- Function to handle kill Signal ---------------------
def sigterm_handler(_signo, _stack_frame):

    # Raises SystemExit(0):
#    terminate()
    sys.exit(0)

#----------- Function to reag switcher log ---------------
def do_getlog():

    zeilen=[]

    command = "tail -n 70 " + pfad + "/switcher2.log"
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
 
    (output, err) = p.communicate()
## Wait for date to terminate. Get return returncode ##
    p_status = p.wait()
    
    #  damit auch alle chars kommen...
    # https://stackoverflow.com/questions/21129020/how-to-fix-unicodedecodeerror-ascii-codec-cant-decode-byte
    if isinstance(output, str):
        output = output.decode('ascii', 'ignore').encode('ascii') #note: this removes the character and encodes back to string.
    elif isinstance(output, str):
        output = output.encode('ascii', 'ignore')
    
    
    if type(output) is str:
#        print ("type ist str")
        pass
    else:
        try:
            output=output.decode()
        except:
            mypri.myprint (DEBUG_LEVEL0,"switcher2.log string kann nicht decodiert werden\nEnthaelt ev. Umlaute")
            output = "Fehler im Server:\nswitcher2.log string kann nicht decodiert werden\nEnthaelt ev. Umlaute"
#    print ("Command output : ", output)
#    print ("Command exit status/return code : ", p_status)
    zeilen = list(output.split("\n"))   # convert string mit NewLine into list

    return(zeilen)
    

#--------------------------------------------
#   tue etwas und gebe dann output zurück 
#   dies wird dann in html code eingesetzt
def togggle_zuhause():
    meld2=[]
    retco=[]
    global ipc


    mypri.myprint (DEBUG_LEVEL1,"togggle_zuhause() called")
    
    message="home"
    text="Zuhause/Nicht Zuhause umgeschaltet"
            

    ipc_instance=IPC_Client(debug,REQUEST_TIMEOUT, ipc_data ,REQUEST_RETRIES)

    retcode=ipc_instance.ipc_exchange(message) 
    if retcode[0] == 9:                        # server antwortet nicht
        retco.append(9)
        retco.append("Switcher antwortet leider nicht...")
        
        del ipc       #  lösche Instanz von IPC_Client

        return(retco)     
      
    if  (retcode[1].find('ackn') != -1):        # switcher sendet ackn, very good
        retco.append(0)
        retco.append(text)
    else:
        retco.append(8)
    return(retco)     


#--------------------------------------------
#   tue etwas und gebe dann output zurück 
#   dies wird dann in html code eingesetzt
def reset_manuell(how):
    meld2=[]
    retco=[]
    global ipc


    mypri.myprint (DEBUG_LEVEL1, "reset_manuell() called, reset: {}".format(how))
    
    if how == 1:
        message="mmit"
        text="Manuell geschaltete Dosen werden um Mitternacht zurückgesetzt"
        
    if how == 2:
        message="mnie"
        text="Manuell geschaltete Dosen werden nie zurückgesetzt"

 

    mypri.myprint (DEBUG_LEVEL1, "reset_manuell() called, reset: {}".format(how))
    
    ipc_instance=IPC_Client(debug,REQUEST_TIMEOUT,  ipc_data ,REQUEST_RETRIES)

    retcode=ipc_instance.ipc_exchange(message) 
    if retcode[0] == 9:                        # server antwortet nicht
        retco.append(9)
        retco.append("Switcher antwortet leider nicht...")
        
        del ipc       #  lösche Instanz von IPC_Client

        return(retco)     
      
    if  (retcode[1].find('ackn') != -1):        # switcher sendet ackn, very good
        retco.append(0)
        retco.append(text)
    else:
        retco.append(8)
    return(retco)     

#--------------------------------------------
#   tue etwas und gebe dann output zurück 
#   dies wird dann in html code eingesetzt
def set_anzdosen (anzahl):
    meld2=[]
    retco=[]
    global ipc

    text="Neue Anzahl Dosen gesetzt, Reboot Switcher, bitte warten..."
    
    mypri.myprint (DEBUG_LEVEL1, "set_anzdosen() called, reset: {}".format(anzahl))
    
    
    message = "dos" + str(anzahl)
  
    
    ipc_instance=IPC_Client(debug,REQUEST_TIMEOUT,  ipc_data ,REQUEST_RETRIES)

    retcode=ipc_instance.ipc_exchange(message) 
    if retcode[0] == 9:                        # server antwortet nicht
        retco.append(9)
        retco.append("Switcher antwortet leider nicht...")
        
        del ipc       #  lösche Instanz von IPC_Client

        return(retco)     
      
    if  (retcode[1].find('ackn') != -1):        # switcher sendet ackn, very good
        retco.append(0)
        retco.append(text)
    else:
        retco.append(8)
        retco.append("Setzen Anzahl Dosen fehlgeschlagen")
    return(retco)     


#--------------------------------------------
#   tue etwas und gebe dann output zurück 
#   dies wird dann in html code eingesetzt
def dose_behandeln(dos,was):
    meld2=[]
    retco=[]
    global ipc
    message="not defined"

    mypri.myprint (DEBUG_LEVEL1, "dose_behandeln() called, dos: {}  was: {} ".format(dos,was))
    

    
    if dos==0:                    # 0 heisst: alle dosen schalten
        text="Alle Dosen wurden: "
        mypri.myprint (DEBUG_LEVEL2, "dos ist null")
        if was==2:                # alle ein schalten
            message="aaus"
            text=text+"ausgeschaltet"
        elif was==1:              # alle einschalten
            message="aein"
            text=text+"eingeschaltet"
    
        elif was==3:
            message="anor"          # alle auf auto zurücksetzen
            text=text+"auf Auto zurückgesetzt"
           
    else:
        mypri.myprint (DEBUG_LEVEL2, "nun kommt else..")
        if was==1:                            # dos enthäkt dosennummer
            text="Dose " + str(dos) + " wurde eingeschaltet"
            message="d" + str(dos) + "ein"      # einschalten
        elif was==2:
            message="d" + str(dos) + "aus"      # ausschalten
            text="Dose " + str(dos) + " wurde ausgeschaltet"            
        elif was==3:
            message="d" + str(dos) + "nor"      # reset to auto
            text="Dose " + str(dos) + " wurde auf Auto zurückgesetzt"
      
       
#    print (message) 

    
    ipc_instance=IPC_Client(debug,REQUEST_TIMEOUT, ipc_data ,REQUEST_RETRIES)

    retcode=ipc_instance.ipc_exchange(message) 
    if retcode[0] == 9:                        # server antwortet nicht
        retco.append(9)
        retco.append("Switcher antwortet leider nicht...")
        
        del ipc       #  lösche Instanz von IPC_Client

        return(retco)     
      
    if  (retcode[1].find('ackn') != -1):        # switcher sendet ackn, very good
        retco.append(0)
        retco.append(text)
    else:
        retco.append(8)
    return(retco)     



#--------------------------------------------
#   tue etwas und gebe dann output zurück 
#   dies wird dann in html code eingesetzt
def get_status(status_art):
    meld2=[]
    retco=[]
    global ipc_instance, anzdosn_gemeldet, wetter_konfiguriert
    global info_fuer_webserver

    mypri.myprint (DEBUG_LEVEL2," get_status started".format(status_art))
    
    info_fuer_webserver = []        # liste leer setzen, info kommt mit jeder meldung von Switcher
    if status_art == 1:
        message="stad"      # kurzer status
    elif status_art == 2:                       
        message="stat"      # longer status
    elif status_art == 3:                       
        message="wett"      # longer status
   
        
    ipc_instance=IPC_Client(debug,REQUEST_TIMEOUT, ipc_data ,REQUEST_RETRIES)

    retcode=ipc_instance.ipc_exchange(message) 
    if retcode[0] == 9:                        # server antwortet nicht
        retco.append(9)
        retco.append("Switcher antwortet leider nicht...")
        del ipc_instance

        return(retco)     
 
    if debug > 1:
        print ( "--> diese meldung gekommen: ")
        print (retcode[1])  
    meldung=retcode[1][4:]      # wir nehmen die ersten 4 Char nicht
  
    if debug > 1:
        print ( "--> diese meldung gekommen nach strip command: ")
        print (meldung)     
    try:
        meld=json.loads(meldung)   # JSON Object wird in Python List of List gewandelt
    except:
        mypri.myprint (DEBUG_LEVEL2, "Status string ist nicht gut...")
        retco.append(9)
        return(retco)

    if debug > 1:
        print ( "--> diese meldung als liste gekommen nach json.loads: ")
        print (meld)     
        
    # antwort besteht aus einer Liste mit Einträgen
    # index[0] sind die Daten an den Webserver
    # restliche einträge sind die DAten
    
    if debug > 0:
        print ( "Info fuer den Webserver: -------------")  
        for i in range(len(meld[0])):
            print ("{:18}:  {:<18}".format (meld[0][i][0]  ,meld[0][i][1]))
  
    for i in range(int(meld[0][0][1])):
        info_fuer_webserver.append(meld[0][i][1])
    
    print ("info webserver: {}". format(info_fuer_webserver))
    
    anzdosn_gemeldet = int(info_fuer_webserver[1])
    wetter_konfiguriert = int(info_fuer_webserver[2])
 
    print ("Anzahl Dosen gemeldet vom Switcher2: {}".format(anzdosn_gemeldet))
    print ("Wetter Konfig gemeldet vom Switcher2: {}".format(wetter_konfiguriert))  
   
    meld.pop(0)             # liste mit info an den webserver wegpoppen
    if debug > 0:      
        print ("Und nun die Daten: ------------------- len(meld): {}". format (len(meld)))  
    
#  wetterdaten ist liste laenge 2
        if len(meld) == 2 :   
            for item1 in meld :    
                for item2 in item1 :
                    print ("{:18}:  {:<18}".format (item2[0]  ,item2[1]))
        else:       # andere daten haben liste mit mehr als 2 items
            for item1 in meld :    
                print ("{:18}:  {:<18}".format (item1[0]  ,item1[1]))    

    
    del ipc_instance                # delete ipc instance

    retco.append(0)
    retco.append(meld)
    return(retco)     

   
    
#----------------------------------------------
# Callback für index.html
#--------------------------------------------
@app.route('/index.html', methods=['GET', 'POST'])
@app.route('/')
def home (name = None):
    stat_list = []
    dosen = 3
                          #  ruft  get_status(1) auf und setzt den returnwert in die variable statklein
    ret = get_status(1)     # verlange kurzen status
    mypri.myprint (DEBUG_LEVEL2, "get_status(1) bringt returncode: {}".format(ret))
    if ret[0] == 0:

        for i in range(len(ret[1])):
            stat_list.append("{:<19} {:>18}".format(ret[1][i][0]  + ": " ,ret[1][i][1] ))

     #   ret[1]=["aa","vv"]
        print ("---- dosen: {}". format(dosen))
        mypri.myprint (DEBUG_LEVEL1, "going to render index.html")      
        return render_template('index.html', statklein = stat_list, html_file2 = select_dosenschalt_htmlfiles [anzdosn_gemeldet])
    else:
        # switcher gibt Fehlerzurück oder reagiert nicht
        mypri.myprint (DEBUG_LEVEL1, "going to render other.html")      

        return render_template('other.html', name = ret[1])
        
#----------------------------------------------
# Callback für status.html   (voller Status)        
#--------------------------------------------
@app.route('/status.html')
def status(name=None):
    stat_list=[]

    mypri.myprint (DEBUG_LEVEL1, "app.route /status called")   
                            #  ruft  get_status(2) auf und setzt den returnwert in die variable name
    ret=get_status(2)     # verlange kurzen status
    mypri.myprint (DEBUG_LEVEL2, "get_status(2) bringt returncode: {}".format(ret))
    if ret[0]==0:
        for i in range(len(ret[1])):
 #           print (ret[1][i][0])
#          print (ret[1][i][1])

            stat_list.append("{:<19} {:>18}".format(ret[1][i][0]  + ": " ,ret[1][i][1] ))
    
     #   ret[1]=["aa","vv"]
        mypri.myprint (DEBUG_LEVEL1, "going to render status.html")      

        return render_template('status.html', name=stat_list, html_file = select_anzdosen_htmlfiles[anzdosn_gemeldet])
    else:
        # switcher gibt Fehlerzurück oder reagiert nicht
        mypri.myprint (DEBUG_LEVEL1, "going to render other.html")      

        return render_template('other.html', name=ret[1])

#----------------------------------------------
# Callback für about.html     
#--------------------------------------------
@app.route('/about.html')
def about():

    mypri.myprint (DEBUG_LEVEL1, "going to render about.html")      

    return render_template('about.html')

#----------------------------------------------
# Callback für log.html     
#--------------------------------------------
@app.route('/swlog.html')
def log():
    mypri.myprint (DEBUG_LEVEL1, "app.route /swlog called")     

    zeilenlist = do_getlog()
    mypri.myprint (DEBUG_LEVEL1, "going to render swlog.html")      

    return render_template('swlog.html',logzeilen = zeilenlist)

#----------------------------------------------
# Callback für wetter.html   (Wetterdaten)        
#--------------------------------------------
@app.route('/wetter.html')
def wetter(name=None):
    list_indoor=[]
    list_outdoor=[]
    mypri.myprint (DEBUG_LEVEL1, "app.route /wetter called")     

                            #  ruft  get_status(3) auf und setzt den returnwert in die variable name
    ret=get_status(3)     # verlange wetterdaten 
    mypri.myprint (DEBUG_LEVEL2, "get_status(3) bringt returncode: {}".format(ret))
    if ret[0]==0:
#        print (len(ret[1][0]))
        for i in range(len(ret[1][0])):             # länge der ersten liste
           list_indoor.append("{:<19} {:>18}".format(ret[1][0][i][0]  + ": " ,ret[1][0][i][1] ))
 

        for i in range(len(ret[1][1])):
#            print (ret[1][0][i][0])
#            print (ret[1][0][i][1])
           
            list_outdoor.append("{:<19} {:>18}".format(ret[1][1][i][0]  + ": " ,ret[1][1][i][1] ))
#            print (list_outdoor)


     #   ret[1]=["aa","vv"]
        mypri.myprint (DEBUG_LEVEL1, "going to render wetter.html")      
        return render_template('wetter.html', name = list_indoor, name2 = list_outdoor)
    else:
        # switcher gibt Fehlerzurück oder reagiert nicht
        mypri.myprint (DEBUG_LEVEL1, "going to render other.html")      
        return render_template('other.html', name=ret[1])

#----------------------------------------------
# Callback für manuelles schalten, kommt von Form zurück     
@app.route('/ackno', methods=['GET', 'POST'])
def ackno():
    error0=False 
    error1=False 
    error2=False 
    error3=False
    ret=[0,0]
 
    mypri.myprint (DEBUG_LEVEL1, "app.route /ackno called")     
#  die verschiedenen input felder untersuchen, schauen, was gekommen ist.   
#
#   zuerst umschaltung zuhase prüfen
    try:
        daheim=int(request.form['zuhause'])
    except:
        error0=True
        mypri.myprint (DEBUG_LEVEL1, "Input check: zuhause nichts gekommen")

#   schauen, ob eine dose gewählt wurde

    try:
        dose=int(request.form['seldose'])
    except:
        error1=True
        mypri.myprint (DEBUG_LEVEL1, "Input check: dose nichts gekommen")
        dose=99
        
#   schauen, ob bei Aktion für Dose etwas gewählt wurde        
    try:
        aktion=int(request.form['select'])
    except:
        error2=True
        mypri.myprint (DEBUG_LEVEL1, "Input check: aktion nichts gekommen")
        aktion=99

#   schauen, ob bei Reset Manuell etwas gewählt wurde                
    try:
        reset=int(request.form['reset_manuell'])
    except:
        error3=True
        mypri.myprint (DEBUG_LEVEL1, "Input check: manuell nichts gekommen")
        reset=99
  
#  Nun Kombinationen prüfen 
    if error0 and error1 and error2 and error3  :
        ret[1]="nichts eingegeben"
        return render_template('other.html', name=ret[1])
    
    if error3:
        if (error1 and not error2) or (error2 and not error1):
            ret[1]="Dose oder Aktion falsch"
            return render_template('other.html', name=ret[1])
          
         
          
    if not error0:
        ret=togggle_zuhause()             #  zuhause nicht zuhause umschalten
    elif not error3:
        ret=reset_manuell(reset)        #   reset manuell geschaltetete Dosen wann
    else:
    #   nun antwort behandeln 
        ret=dose_behandeln(dose,aktion)  #       kurzer oder langer Status erstellen

    mypri.myprint (DEBUG_LEVEL1, "going to render ackno.html")    
    if ret[0]==0:                       # Ackno.html ausgeben mit Angabe der gemachten Aktion
        return render_template('ackno.html', returncode=ret[0], textfeld = ret[1])
    else:
        mypri.myprint (DEBUG_LEVEL1, "going to render other.html")        
        # switcher gibt Fehlerzurück oder reagiert nicht
        return render_template('other.html', name=ret[1])
    
 #----------------------------------------------
# Callback für manuelles schalten, kommt von Form zurück     
@app.route('/set_dosen', methods=['GET', 'POST'])
def set_dosen():
    error0=False 
    error1=False 
    error2=False 
    error3=False
    ret=[0,0]
    dosenanz = 0
    mypri.myprint (DEBUG_LEVEL1, "app.route /set_dosen called") 
#  das input felder (anzahl dosen untersuchen, schauen, was gekommen ist.   
#

    try:
        dosenanz = int(request.form['anzahl_dosen'])
        mypri.myprint (DEBUG_LEVEL1, "Anzahl dosen bestehend: {}, anzahl neu: {}". format(anzdosn_gemeldet,dosenanz) )   
    
        ret = set_anzdosen (dosenanz)    

    except:
        error0=True
        mypri.myprint (DEBUG_LEVEL1, "Input check: anzahl_dosen nichts gekommen")
        ret[0] = 9
 
    mypri.myprint (DEBUG_LEVEL1, "going to render ackno.html")    
    if ret[0]==0:                       # Ackno.html ausgeben mit Angabe der gemachten Aktion
        return render_template('ackno.html', returncode=ret[0], textfeld = ret[1])
    else:
        mypri.myprint (DEBUG_LEVEL1, "going to render other.html")       
        # switcher gibt Fehlerzurück oder reagiert nicht
        return render_template('other.html', name=ret[1])
    
       

#----------------------------------------------
# Programm startet hier....
#----------------------------------------------
if __name__=='__main__':

    options=argu()    
    sleep(2)
    ret = setup_server()                                             # do setup
    if ret > 0:
        mypri.myprint (DEBUG_LEVEL0, "swserver2: terminiert nach setup() wegen Fehler {}".format (ret))
        sys.exit(2)
        
    if debug==0:
        app.run(host='0.0.0.0',debug=False, port=4000)       # run the webserver

    else: 
        app.run(host='0.0.0.0',debug=True, port=4000)       # run the webserver
        
   
# end of Programm
#---------------------------------------------- 
#
#   