#!/usr/bin/python
# coding: utf-8
# 
# ***********************************************************
# 	Class Dose 
#   
#   enkapsuliert Dosenmanagement
#   Funktionen zum Schalten der Dosen
#
#   diese Class erbt von der MyPrint Class
#   
#   folgende public methods stehen zur Verfügung:
#       display_anzahl()
#       display_status()
#       set_zuhause()
#       set_nichtzuhause()
#       set_manuell()
#       reset_manuell()
#       set_auto()
#       show_status()
#   
#   Juli 2018
#************************************************
#



from sub.swcfg_switcher import cfglist_dos       # struktur der Dose Config im Config File  
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.configread import ConfigRead
import os
from datetime import date, datetime, timedelta

# -- Konstanten -----------------------------
DEBUG_LEVEL0 = 0
DEBUG_LEVEL1 = 1
DEBUG_LEVEL2 = 2
DEBUG_LEVEL3 = 3      
WAIT_STATUS_MELDUNG = 30                  
#--------------------------------------------------
class Dose(MyPrint):
    ' klasse dose '
    dosenzahler=0           # Class variable Anzahl Dosen
#
    def __init__(self, dose,testmode_in,debug_in, path_in, mqtt_status_in, mqttc_in):   # Init Methode der Dose, setzt Instanz Variablen
        self.errorcode = 8          # initwert, damit beim Del des Aktors richtig gehandelt wird
        self.nummer = Dose.dosenzahler      
        self.status_intern = 0          # interner Status der Dose, gemäss programmierten Aktionen
        self.status_extern = 0          # externer Status der Dosen (für Status-Anzeige)
                                        # die folgenden drei variablen beeinflussen die Art und weise des schaltens der Dose
        self.schaltart = 0              # technische schaltart, bestimmt den Aktor, der benutzt werden muss
        self.schaltmodus = 0            # 0=auto, 1=manuell
        self.schaltprio = 0             # 1: normal, 2: dose schalten ohne berücksichtigung zuhause/nicht zuhause 

        self.zuhause = False            # False=abwesend, True=zuhause
        self.debug = debug_in
        self.zimmer_name = ""      
        Dose.dosenzahler += 1           # erhögen dosenzahler
        self.status_extern = 0
        self.path = path_in             # pfad  main switcher
        self.dosen_nummer = Dose.dosenzahler
        self.myprint (DEBUG_LEVEL1, "--> dose {} dosen_init called, debug: {}  testmode: {}".format (self.dosen_nummer,debug_in,testmode_in))
        self.testmode = testmode_in
        self.mqttc = mqttc_in           # instanz mqtt client
        self.mqtt_status = mqtt_status_in
        self.msg_variante = 1           # default wert Test Pyload
        self.subscribe = 0
        self.time_last_aktion = 0               
        self.e = []
        self.debug_level2_mod = DEBUG_LEVEL2
        self.tmp = 0
        self.schalt = ""                # hilfsfeld    
 # nun schaltart für die Dosen  aus config holen
        
        config=ConfigRead(self.debug)        # instanz der ConfigRead Class
        configfile=self.path + "/swconfig.ini"
        ret=config.config_read(configfile,"dose",cfglist_dos)
        if ret > 0:
            self.myprint (DEBUG_LEVEL0, "dosen init: config_read hat retcode: {}".format (ret))
            self.errorcode=99
            return None

        self.myprint (DEBUG_LEVEL3, "dose {} dosen_init: dose {} configfile read {}".format (self.nummer,self.dosen_nummer, cfglist_dos))

        self.schalt = "dose_" + str(self.dosen_nummer) + "_schaltart"
        y=cfglist_dos.index(self.schalt)  + 1           # suche den Wert von schaltart aus Config-file
        self.schalt=cfglist_dos[y].decode()
     
        self.tmp = "dose_" + str(self.dosen_nummer) + "_schaltprio"
        y=cfglist_dos.index(self.tmp)  + 1           # suche den Wert von modus aus Config-file
        self.schaltprio = int(cfglist_dos[y].decode())

        y=cfglist_dos.index("debug_schalt")  + 1           # suche den Wert von debug_schalt aus Config-file
        tmp = int(cfglist_dos[y].decode())
        if tmp > 0:
            self.debug_level2_mod  =  DEBUG_LEVEL0
            self.myprint (DEBUG_LEVEL0, "dosen init: dose {} , alle schaltaktionen werden logged (in configfile)".format(self.dosen_nummer))

        if self.schaltprio == 2 :
            self.myprint (DEBUG_LEVEL0, "dosen init: dose {} , dose hat modus_1 = 2".format(self.dosen_nummer))

            
            
         # schaltart auswerten....   
        if len(self.schalt) == 0:
            self.myprint (DEBUG_LEVEL0, "dosen init: dose {} , Schaltart ungültig, nehme default 1".format(self.dosen_nummer))
            self.schalt = "1,1,1"
        if len(self.schalt) == 1:
            self.schaltart  = int(self.schalt)    
        if len(self.schalt) > 1:
            self.e=self.schalt.split(",")
        if len(self.e) > 1:
            self.schaltart = int(self.e[0])
            self.msg_variante = int(self.e[1])
        if len(self.e) > 2: 
            self.subscribe = int(self.e[2])
            
            
        if  self.schaltart == 3:
            self.myprint (DEBUG_LEVEL1, "dosen init: dose {} , Schaltart: {}, MQTT_status: {}, msg_var:{}, subscribe:{}".format(self.dosen_nummer,self.schaltart, self.mqtt_status, self.msg_variante, self.subscribe))
        else:
            self.myprint (DEBUG_LEVEL1, "dosen init: dose {} , Schaltart: {}".format(self.dosen_nummer,self.schaltart))
        
        
        if self.testmode:
            self.myprint (DEBUG_LEVEL0, "dosen init: dose {} , nehme Schaltart 1 wegen Testmode !".format(self.dosen_nummer))
            self.schaltart = 1
        
        if self.schaltart == 3 and self.mqtt_status == 0:
            self.myprint (DEBUG_LEVEL0, "dosen init: dose {} , nehme Schaltart 1 da MQTT nicht definiert oder fehlerhaft ist !".format(self.dosen_nummer))
            self.schaltart = 1
                
# plausicheck 
        if  self.dosen_nummer > 4 :
            if self.schaltart == 1 or self.schaltart == 3:     # dosennummer 5 und ev. 6 dürfen nicht schaltart 2 haben (Funksteckdosen)
                pass
            else:  
                self.myprint (DEBUG_LEVEL0, "dosen init: dose {} , darf nur Schaltart 3 oder 1 haben, nehme 1".format(self.dosen_nummer))
                self.schaltart = 1;

            
        if self.schaltart == 1:
            import sub.swaktor_1 
            self.myaktor=sub.swaktor_1.Aktor_1(self.dosen_nummer,self.debug,self.path)          # Instanz der Aktor Class erstellenb
        elif self.schaltart == 2:
            import sub.swaktor_2 
            self.myaktor=sub.swaktor_2.Aktor_2(self.dosen_nummer,self.debug,self.path)          # Instanz der Aktor Class erstellenb
        elif self.schaltart == 3:
            import sub.swaktor_3         
            self.myaktor=sub.swaktor_3.Aktor_3(self.dosen_nummer,self.debug,self.msg_variante,self.subscribe,self.path, self.mqttc, self.aktor_callback)          # Instanz der Aktor Class erstellenb
        elif self.schaltart == 4:
            import sub.swaktor_4         
            self.myaktor=sub.swaktor_4.Aktor_4(self.dosen_nummer,self.debug,self.path)          # Instanz der Aktor Class erstellenb
        elif self.schaltart == 5:
            import sub.swaktor_5         
            self.myaktor=sub.swaktor_5.Aktor_5(self.dosen_nummer,self.debug,self.path)          # Instanz der Aktor Class erstellenb

        else:
            self.myprint (DEBUG_LEVEL0, "dose {} falsche Schaltart {}".format (self.nummer,self.schaltart))
            self.myprint (DEBUG_LEVEL0, "dose {} Nehme Default-Schaltart 1".format (self.nummer))
            import swaktor_1 
            self.myaktor=swaktor_1.Aktor_1(self.dosen_nummer,self.debug)          # Instanz der Aktor Class erstellenb
           

        if self.myaktor.errorcode == 99:
            self.myprint (DEBUG_LEVEL1,  "Aktor: {} meldet Fehler {}".format (self.dosen_nummer, self.myaktor.errorcode))	 
            raise RuntimeError('---> Switcher ernsthafter Fehler, check switcher2.log <----')

        self.time_last_aktion =  datetime.now()         # zeit merken 

        self.myprint (DEBUG_LEVEL2, "dose {} ausschalten (init dose), schaltart: {}".format (self.nummer, self.schaltart))
        self.myaktor.schalten(0,  self.debug_level2_mod)
        self.errorcode = 0          # init der Dose ok 

# Funktion dispay_anzahl()  gibt die Anzahl der instantiierten Dosen zurück
#--------------------------------------------------------------------------
    def display_anzahl(self):
        return(Dose.dosenzahler)

# Funktion dispay_anzahl()  gibt status aus auf stdout
#--------------------------------------------------------------------------
    def display_status(self):
       self.myprint (DEBUG_LEVEL2, "Dose: {} Status intern {} Status extern {} Modus {} Zuhause {}".format (self.nummer, self.status_intern,self.status_extern,self.schaltmodus, self.zuhause))
       
# Funktion set_zuhause()  schaltet dose aus, falls Modus nicht manuell ist, setzt externen Status
#--------------------------------------------------------------------------
    def set_zuhause(self):
# 
        self.myprint (self.debug_level2_mod ,  "--> dose {} set_zuhause called, zuhause: {}" .format (self.dosen_nummer, self.zuhause))
        self.zuhause=True
        if self.schaltmodus == 1: 
            return            # wenn modus manuell mach nichts weiter

        if self.schaltprio == 2: 
            return            # wenn modus_1 = 2 mach nichts weiter, dose wir von zuhause/nicht zuhause nicht beeinflusst
       
        self.time_last_aktion =  datetime.now()         # zeit merken 
        
        self.status_extern=0
        self.myprint (self.debug_level2_mod, "dose {} ausschalten , schaltart: {}".format (self.dosen_nummer, self.schaltart))
        self.myaktor.schalten(0,  self.debug_level2_mod)

# ---- Funktion set_dosen_nichtzuhause ------------------------------
#      schaltet die Dose ein, falls interner Status 1 ist - aber nicht, wenn Modus =manuell ist 
    def set_nichtzuhause(self):
# 
        self.myprint (self.debug_level2_mod ,  "--> dose {} set_nicht zuhause called, zuhause: {}" .format (self.dosen_nummer, self.zuhause))
        self.zuhause=False
        if self.schaltmodus == 1: 
            return   # manuell, wir machen nichts
        if self.schaltprio == 2: 
            return            # wenn modus_1 = 2 mach nichts weiter, dose wir von zuhause/nicht zuhause nicht beeinflusst
       
        self.time_last_aktion =  datetime.now()         # zeit merken 
            
        if self.status_intern==1:
            self.status_extern=1
            self.myprint (self.debug_level2_mod, "dose {} einschalten , schaltart: {}".format (self.dosen_nummer, self.schaltart))
            self.myaktor.schalten(1,  self.debug_level2_mod)
        else:
            self.status_extern=0
            self.myprint (self.debug_level2_mod, "dose {} ausschalten , schaltart: {}".format (self.dosen_nummer, self.schaltart))
            self.myaktor.schalten(0,  self.debug_level2_mod)

# ---- Funktion set_dosen_wiestatus ------------------------------
#      schaltet die Dose ein, falls interner Status 1 ist - aber nicht, wenn Modus =manuell ist 
    def set_dosen_wiestatus(self):
# 
        self.myprint (self.debug_level2_mod ,  "--> dose {} set_dose_wiestatus called, zuhause: {}" .format (self.dosen_nummer, self.zuhause))
        if self.schaltmodus == 1: 
            return   # manuell, wir machen nichts

        self.time_last_aktion =  datetime.now()         # zeit merken 
            
        if self.status_intern==1:
            self.status_extern=1
            self.myprint (self.debug_level2_mod, "dose {} einschalten , schaltart: {}".format (self.dosen_nummer, self.schaltart))
            self.myaktor.schalten(1,  self.debug_level2_mod)
        else:
            self.status_extern=0
            self.myprint (self.debug_level2_mod, "dose {} ausschalten , schaltart: {}".format (self.dosen_nummer, self.schaltart))
            self.myaktor.schalten(0,  self.debug_level2_mod)



# ---- Funktion set_dosen_manuell ------------------------------
#      schaltet die Dose gemäss Parameter how ein/aus, setzt Modus auf manuell
#       Parameter how= 1 für ein, 0 für aus
    def set_manuell(self, how):

        self.myprint (self.debug_level2_mod ,  "--> dose {} set_manuell called, how: {}  zuhause: {}".format (self.dosen_nummer,how, self.zuhause))
    
        self.status_extern = how
        self.schaltmodus = 1
        self.time_last_aktion =  datetime.now()         # zeit merken 

        self.myprint (self.debug_level2_mod, "dose {} manuell schalten , schaltart: {}".format (self.dosen_nummer, self.schaltart))
        self.myaktor.schalten(how,  self.debug_level2_mod)
        
# ---- Funktion reset manuell ------------------------------
#   setzt Modus auf Auto (0) und schaltet Dose gemäss dem aktuellen internen Status
    def reset_manuell(self):
        self.myprint (self.debug_level2_mod,  "--> dose {} reset_manuell called, modus: {}, status_intern: {}".format (self.dosen_nummer, self.schaltmodus, self.status_intern))
        if self.schaltmodus == 0:
            return                  # wir behandlen nur Dosen mit modus manuell
        self.time_last_aktion =  datetime.now()         # zeit merken 
            
        self.schaltmodus = 0
        if self.status_intern == 1:   
            self.status_extern = 1
            self.myprint (self.debug_level2_mod , "dose {} reset_manuell: einschalten , schaltart: {}".format (self.dosen_nummer, self.schaltart))
            self.myaktor.schalten(1,  self.debug_level2_mod)
        else:
            self.status_extern = 0
            self.myprint (self.debug_level2_mod , "dose {} reset_manuell: ausschalten , schaltart: {}".format (self.dosen_nummer, self.schaltart))
            self.myaktor.schalten(0,  self.debug_level2_mod)
  
          
 
# ---- Funktion set_auto,  ------------------------------
#   schaltet dose gemäss how, jedoch nur, wenn Modus 'Auto' ist (bei Modus 'Manuell' wird nicht geschaltet)  
    def set_auto(self, how):
# how= 1 für ein, 0 für aus
        self.myprint (self.debug_level2_mod ,  "--> dose {} set_auto called, how: {}  modus: {}  zuhause: {}".format (self.dosen_nummer,how,self.schaltmodus,self.zuhause))
   
        self.status_intern = how      # interner status wird in jedem Fall nachgeführt
 
        if self.zuhause :
            if self.schaltprio == 1:
                return                  # wenn jemand da ist wird bloss interner status nachgeführt
    
    
        if self.schaltmodus == 0:           # Nur wirklich schalten, wenn modus auto ist - externer status nachführen
            self.status_extern=how
            self.time_last_aktion =  datetime.now()         # zeit merken 

            self.myprint (DEBUG_LEVEL2,  "dose {} auto schalten {}".format (self.dosen_nummer, how))
            self.myaktor.schalten(how,  self.debug_level2_mod)

# ---- Funktion set_auto_virtuell,  ------------------------------
#   schaltet dose nicht, setzt aber internen Status gemäss how
#   wird bei der Abarbeitung der vergangenen Aktionen des Tages benutzt im Switcher
#   bei Funk wollen wir nicht so lange funken, bis alles abgearbeitet ist
    def set_auto_virtuell(self, how):
# how= 1 für ein, 0 für aus
        self.myprint (DEBUG_LEVEL2,  "--> dose {} set_auto_virtuell called, how: {}  modus: {}".format (self.dosen_nummer,how,self.schaltmodus))
   
        self.status_intern=how      # interner status wird in jedem Fall nachgeführt


# ---- Callback Aktor ------------------------------
#   der smart switch hat eine statusmeldung (ON oder OFF) gesendet.
#   Voraussetzung: der smart switch sendet immer eine statusmeldung, sowohl wenn vom switcher geschaltet,
#   als auch, wenn von Hand an der dose geschaltet. Wir müssen die beiden Dinge aber irgendwie unterscheiden.
#   dies machen wir so:
#   statusmeldungen, die innerhalb von 30 sekunden kommen, nachdem switcher2 selbst geschaltet hat,
#   werden ignoriert. Dies, weil der Switcher (also die Dose) den internen/externen Status bereits selbst gesetzt hat.
#   statusmeldungen hingegen, die mehr als 30 sekunden später eintreffen, werden betrachtet als von HAND AN DER DOSE
#   geschaltet. Dies kann ja irgendwann passieren. In diesen Fall wird der status der dose verändert.
#   ist etwas krude, tut aber den Dienst.
    def aktor_callback(self,payload_in):
        
        time_new =  datetime.now() 
        delta = time_new - self.time_last_aktion
        delta = int(delta.seconds)     # delta in sekunden
        self.myprint (DEBUG_LEVEL0,  "--> dose {} aktor_callback() called, payload: {}, zeit seit letzter aktion: {} sek.".format (self.dosen_nummer, payload_in, delta))
        if delta > WAIT_STATUS_MELDUNG:
        
            if payload_in == "ON" :
                self.status_extern = 1          # dose wurde eingeschaltet
                self.schaltmodus = 1            # sie ist manuell eingeschaltet
                self.myprint (DEBUG_LEVEL2,  "--> dose {} aktor_callback() setze dose ein/maunell ".format (self.dosen_nummer))
            if payload_in == "OFF" :
                self.myprint (DEBUG_LEVEL2,  "--> dose {} aktor_callback() setze dose aus/maunell ".format (self.dosen_nummer))
                self.status_extern = 0          # dose wurde ausgeschaltet
                self.schaltmodus = 1            # schaltmodus nun manuell
        else:
             self.myprint (DEBUG_LEVEL1,  "--> dose {} aktor_callback() zeitdiff kleiner als: {} sek, mache nichts".format(self.dosen_nummer,WAIT_STATUS_MELDUNG))
 

# ---- Funktion set Zimmer ------------------------------
#       setzen Zimmer Name
    def set_zimmer(self,namezimmer):
        self.myprint (DEBUG_LEVEL2,  "--> dose {} set_zimmer called: {}".format (self.dosen_nummer,namezimmer))
        
        self.zimmer_name=namezimmer
            
# ---- Funktion get Zimmer ------------------------------
#       setzen Zimmer Name
    def get_zimmer(self):
        self.myprint (DEBUG_LEVEL2,  "--> dose {} get_zimmer called".format (self.dosen_nummer))
        
        return (self.zimmer_name)

        
# ---- Funktion show_status ------------------------------
#       gibt string zurück mit externem status plus decorator m oder h
    def show_status(self):
# how= 1 für ein, 0 für aus
        self.myprint (DEBUG_LEVEL2,  "--> dose {} show_status called".format (self.dosen_nummer))

        ret=str(self.status_extern)
        if  self.schaltmodus == 1:
            ret = ret+"m"
            
        if self.zuhause and self.schaltprio == 1:
            ret = ret+"h"
            
        if self.schaltprio == 2:
            ret = ret+"i"                       # überschreibt alle anderen werte
        pass
        ret = ret + ":" + str(self.schaltart)     # die schaltart noch dazu
        self.myprint (DEBUG_LEVEL2,  "--> dose {} show_status returns: {}".format (self.dosen_nummer, ret))        
        return(ret)



            
# Destruktor der Class Dose
#------------------------------------------------
    def __del__(self):
        # beenden, dose off setzen
        if self.errorcode == 0:         # bei initwert 8 wird demnach nichts gemacht
        
            del self.myaktor
        self.status_extern=0
        self.status_intern=0

#------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swdose.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
