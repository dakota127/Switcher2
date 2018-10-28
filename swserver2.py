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


REQUEST_TIMEOUT=3500
REQUEST_RETRIES=3
debug=0
ipc=0
mypri=0
AKTION=["Eingeschaltet","Ausgeschaltet","Zurückgesetzt auf Auto"]
app = Flask(__name__)
pfad =""
info_fuer_webserver = 0
                                    # liste von 10 ints wird als string vom Switcher gesandt beim Status request
                                    # index 0 : anzahl Dosen 
                                    # index 1 : switcher mit wettermessung
                                    # index 2-9: for future use

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
    global ipc_instance
    global info_fuer_webserver

    mypri.myprint (DEBUG_LEVEL2," get_status started".format(status_art))
    
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
        
    meldung=retcode[1][4:]      # wir nehmen die ersten 4 Char nicht
 
    tmp_stri = meldung [0:10]   # die nächsten 10 bytes sind info für uns, den webserver
                                # damit meldet uns der switcher, was zu tun ist,
    info_fuer_webserver = [int(i) for i in str(tmp_stri)]
    
    meldung = meldung [10:]      # nehme ab pos 10 
    mypri.myprint (DEBUG_LEVEL1, "Info fuer Webserver: {}".format(info_fuer_webserver))
   
    try:
        meld=json.loads(meldung)   # JSON Object wird in Python List of List gewandelt
    except:
        mypri.myprint (DEBUG_LEVEL2, "Status string ist nicht gut...")
        retco.append(9)
        return(retco)
        
      
  # keep this might need it again....    
 #   print ("Meldung sieht so aus")
 #   print (len(meld),meld)
    
    
    del ipc_instance                # delete ipc instance

    retco.append(0)
    retco.append(meld)
    return(retco)     

   
    
#----------------------------------------------
# Callback für index.html
#--------------------------------------------
@app.route('/index.html')
@app.route('/')
def home(name = None):
    stat_list = []
                          #  ruft  get_status(1) auf und setzt den returnwert in die variable statklein
    ret = get_status(1)     # verlange kurzen status
    mypri.myprint (DEBUG_LEVEL2, "get_status(1) bringt returncode: {}".format(ret))
    if ret[0] == 0:

        for i in range(len(ret[1])):
            stat_list.append("{:<19} {:>18}".format(ret[1][i][0]  + ": " ,ret[1][i][1] ))

     #   ret[1]=["aa","vv"]
        return render_template('index.html', statklein = stat_list)
    else:
        # switcher gibt Fehlerzurück oder reagiert nicht
        return render_template('other.html', name = ret[1])
        
#----------------------------------------------
# Callback für status.html   (voller Status)        
#--------------------------------------------
@app.route('/status.html')
def status(name=None):
    stat_list=[]
       
                            #  ruft  get_status(2) auf und setzt den returnwert in die variable name
    ret=get_status(2)     # verlange kurzen status
    mypri.myprint (DEBUG_LEVEL2, "get_status(2) bringt returncode: {}".format(ret))
    if ret[0]==0:
        for i in range(len(ret[1])):
 #           print (ret[1][i][0])
#          print (ret[1][i][1])

            stat_list.append("{:<19} {:>18}".format(ret[1][i][0]  + ": " ,ret[1][i][1] ))
    
     #   ret[1]=["aa","vv"]
        return render_template('status.html', name=stat_list)
    else:
        # switcher gibt Fehlerzurück oder reagiert nicht
        return render_template('other.html', name=ret[1])

#----------------------------------------------
# Callback für about.html     
#--------------------------------------------
@app.route('/about.html')
def about():
    return render_template('about.html')

#----------------------------------------------
# Callback für log.html     
#--------------------------------------------
@app.route('/swlog.html')
def log():
    zeilenlist = do_getlog()
    return render_template('swlog.html',logzeilen = zeilenlist)

#----------------------------------------------
# Callback für wetter.html   (Wetterdaten)        
#--------------------------------------------
@app.route('/wetter.html')
def wetter(name=None):
    list_indoor=[]
    list_outdoor=[]

                            #  ruft  get_status(3) auf und setzt den returnwert in die variable name
    ret=get_status(3)     # verlange wetterdaten 
    mypri.myprint (DEBUG_LEVEL2, "get_status(3) bringt returncode: {}".format(ret))
    if ret[0]==0:
        for i in range(len(ret[1][0])):
#            print (ret[1][0][i][0])
#            print (ret[1][0][i][1])
           
            list_indoor.append("{:<19} {:>18}".format(ret[1][0][i][0]  + ": " ,ret[1][0][i][1] ))
        for i in range(len(ret[1][1])):
#            print (ret[1][0][i][0])
#            print (ret[1][0][i][1])
           
            list_outdoor.append("{:<19} {:>18}".format(ret[1][1][i][0]  + ": " ,ret[1][1][i][1] ))



     #   ret[1]=["aa","vv"]
        return render_template('wetter.html', name = list_indoor, name2 = list_outdoor)
    else:
        # switcher gibt Fehlerzurück oder reagiert nicht
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

    if ret[0]==0:                       # Ackno.html ausgeben mit Angabe der gemachten Aktion
        return render_template('ackno.html', returncode=ret[0], dose=ret[1])
    else:
    
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