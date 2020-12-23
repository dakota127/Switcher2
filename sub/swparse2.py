#!/usr/bin/python
# coding: utf-8
# ***********************************************************
# 	Class ActionParser 
#   
#   enkapsuliert die Behandlung der XML Steuerfiles
#   Read, Parse, Ausgabe der Aktionsliste
#
#   diese Class erbt von der MyPrint Class
#   
#   folgende public methods stehen zur Verfügung:
#       get_file()
#       print_actions()
#       check_saison_init()
#       check_saison()
#       list_saison()
#       set_debug()
#       get_saison_info
#
#   folgende privat methods gibt es:
#       __posanz()
#       __setburn()
#       __parse_file()
#       __datechange()
#
#   Verbessert Januar 2015, P.K. Boxler     , angepasst für Switcher2 im Juli 2018
#
# ***** Imports *********************************************
import sys, getopt, os
import xml.dom.minidom
from datetime import date
import datetime
import math
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sys import version_info

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

#-------------------------------------------------
# Class Parser, erbt vom Class MyPrint
#--------------------------------------------------
class ActionParser(MyPrint):
    ' klasse ActionParser '
    
#    Definition der Class Variables
    parserzahler=0           # Class variable Anzahl Parser instanzen
    python_version=2
# List of List für Saison-Bearbeitung 
# Elemente der inneren Liste: 
#    Element [0] (string) : filename Hauptteil für Controlfile
#    Element [1] (string) : Startdatum Tag und Datum des Wechsels in diese Season
#    Element [2] (string) : Enddatum   Tag und Datum des Wechsels in diese Season
#    Element [3] (string) : Name der Season für Listen und so... aus dem XML File
#    Element [4] (string) : String kommt aus dem XML File, ID des Files
    
    saison_list=[[""," "," "," "," "],[""," "," "," "," "],[""," "," "," "," "]]
    monate={"Januar":"Jan","Februar":"Feb","März":"Mar","April":"Apr","Mai":"May","Juni":"Jun","Juli":"Jul", "August":"Aug","September":"Sep","Oktober":"Oct","November":"Nov","Dezember":"Dec"} 
        
# Konstruktor der Class ------------------------        
    def __init__(self,debug_in, path_in):   # Init Methode der Dose, setzt Instanz Variablen
#
#   Defintion der Instanz Variablen ----------
        self.Weekdays={0: "Sonntag", 1:"Montag", 2: "Dienstag",3: "Mittwoch",4: "Donnerstag",5: "Freitag", 6: "Samstag"}
        self.onoff={1:'ON', 0:'OFF'}
        self.maxlen=90
        self.maxdose=8                  # Platz für maximal 8 Dosen 
        self.maxday=7
        self.season=0
        self.woche2=list()  
        self.timelin3="17       18        19        20        21        22        23        24        01        02"
        self.debug=debug_in
        self.path=path_in       # pfad wo switcher2 läuft
        self.myprint (DEBUG_LEVEL2,  "--> ActionParser init called")
        self.dates=[[] for i in range (2)]
        self.heute=0


        if version_info[0] < 3:
            ActionParser.python_version=2
        else:
            ActionParser.python_version=3       
# -- private Methode  um Position und Länge für Chr X zu ermitteln auf der gedachten Zeitachse
#
#   Die grafische Zeitachse ist 90 Positionen lang, diese decken die Zeit von 17.00 bis 02.00 ab
#   Alle Schaltzeiten ausserhalb dieses Bereiches werden nicht berücksichtigt
#   Schaltzeiten, die in den Bereich hineinragen (vorher oder nachher), werden entsprechend berücksichtigt
#   Für Stunden 0 und 1 (nach Mitternacht) wird je 24 addiert.
#
#   nach diversen Tests funktioniert folgender Code - ist aber nicht komplett fehlerfrei   
#
    def __posanz (self,start,end):
        self.myprint (DEBUG_LEVEL1,  "--> ActionParser posanz called")

        returnvalue=[[0],[0]]
    
        self.myprint (DEBUG_LEVEL3,  "ActionParser Pos und Anz ermitteln fuer: %4.2f/%4.2f ---------------" % (start, end))
        s1=math.modf(start)
        e1=math.modf(end)
# s1[0] = dezimal Minuten
# s1[1] = Ganzahl Stunden
    
        self.myprint (DEBUG_LEVEL3,  "ActionParser Anfang/Ende in Std: %s/%s  %s/%s " % (s1[1], s1[0], e1[1],e1[0])  )

        std_anfang=s1[1]               # stunden Start
#    if ((std_anfang==0) or (std_anfang==1)):        
        if ((std_anfang>=0) and (std_anfang<12)):        
            std_anfang=std_anfang+24          # ajustiere für nach Mitternacht

        std_ende=e1[1]               # stunden ende
        if ((std_ende>=0) and (std_ende<12)):        
            std_ende=std_ende+24          # ajustiere für nach Mitternacht
    
        star=int(math.floor((s1[0]*100)+(std_anfang*60)))  # berechne start in Minuten (ab 0.00)
        end=int(math.floor((e1[0]*100)+(std_ende*60)))   # berechne Minuten der Endezeit
        self.myprint (DEBUG_LEVEL3,  "ActionParser Anfang/Ende Min: %s  %s " % (star, end)  )

    
        if (((end < 1020) and (star < 1020))) or  \
            (((star >1560) and (end > 1560))):  # diese kommen nicht in Frage
#    if ((std_ende < 17) and (std_ende > 2)):  # diese kommen nicht in Frage
            returnvalue[0]=0
            returnvalue[1]=0
            self.myprint (DEBUG_LEVEL3,  "ActionParser Kommt nicht in Frage")
            return (returnvalue)

    
        self.myprint (DEBUG_LEVEL3,  "ActionParser Anfang/Ende  2 Std: %s  %s " % (std_anfang, std_ende) ) 
    
    
        if star < 1020:                             # wenn Start kleiner 17.00
            pos=0
            star=1020                               # setze Start 17.00
  
        else:    
            pos= int(math.floor((star-1020)/6))     # berechne Position ab welcher Zeichen

#nun die dauer
        std=e1[1]                                   # Stunden der EndeZeit
        if ((std==0) or (std==1) or (std==2)):        
            std=std+24                              # ajustiere für nach Mitternacht
        self.myprint (DEBUG_LEVEL3,  "    Ende Std: %s" % std  )  
        end=int(math.floor((e1[0]*100)+(std*60)))   # berechne Minuten der Endezeit
        self.myprint (DEBUG_LEVEL3,  "    Ende 1: %s" % end)
        if end < 1020:                              # wenn Ende kleiner 17 Uhr
            end=1560                                # setze Ende auf 02.00 Uhr
        elif end > 1560:                            # wenn Ende grösser 02.00 Uhr setze Ende 02.00
            end=1560    
        self.myprint (DEBUG_LEVEL3,  "    Ende 2: %s" % end  )
        dauer=end-star                              # Leuchtdauer in Minuten juni2018
        self.myprint (DEBUG_LEVEL3,  "    Brenndauer: %s" % dauer)
        if dauer < 0:
            returnvalue[0]=0
            returnvalue[1]=0
            return (returnvalue)

        if dauer <= 6: anz=1
        else:
            div=dauer/6
            anz=int(math.floor(div))
            self.myprint (DEBUG_LEVEL3,  "    Position: %s  Anzahl: %s" % (pos,anz))
    
        returnvalue=(pos,anz)
    
        return (returnvalue)
#-----------------------------------------

#  --- Funktion zum Erstellen (Extrahieren) Liste aller Tage für bestimmte Saison
    def alle_tage_pro_saison (self,liste, saison):
        tages_liste = []
        for n in liste[saison]:
            tages_liste.append(n)
        return(tages_liste)


# --- Private Methode  um Char X in die Zeile zu setzen -----------------
    def __setburn (self,woch ,z,y, pos,anz):
        self.myprint (DEBUG_LEVEL2,  "--> ActionParser setburn called")

        self.myprint (DEBUG_LEVEL3,  "ActionParser setchar:  Tag: %d  Dose: %d Pos: %d  Anz: %d " % (z,y, pos,anz))

        j=0
        for i in range (anz):       # anz = Anzahl der Char zu setzen
#        print ("Anz %d / %d" % (i,z))
            woch[z][y-1][pos+j]='0'           # z=tag / y=Dose  (muss -1 sein, da dosen mit 1-4 bezeichnet sind)
            j=j+1
            if (pos+j) >=self.maxlen: break         # ueberlauf vermeiden

        return(0)

#-----------------------------------------------------------
# ---- Private Methode um TT.MM in Linux Format umzuwandeln, mit Jahr
    def __datechange(self,ttmm):

        ret=[0,0]
        self.myprint (DEBUG_LEVEL2,   "-->  __datechange called mit %s" % ttmm)
    # zuerst deutschen Monat in Linux Monat übersetzten und auch korrekte Schreibweise prüfen
    # dann aktuelles Jahr anhängen und Resultat zurückgeben
    
        if ActionParser.python_version > 2:
            a=ttmm[3:].decode()
            b=ttmm.decode()
        else:
            a=ttmm[3:]
            b=ttmm
       
        if a not in ActionParser.monate:
            self.myprint (DEBUG_LEVEL0,   "ActionParser Monat change to %s hat Format-Fehler" % b) 
            self.myprint (DEBUG_LEVEL0,   "ActionParser Monatsangaben im Steuerfile überprüfen !") 
            
            ret[0]=9
            return(ret)
        b=b.replace(a, ActionParser.monate[a])
        b=b.replace(".", " ")
        c=datetime.datetime.strptime(b, '%d %b').date().replace(year=self.heute.year)
        c=datetime.datetime.combine(c, datetime.datetime.min.time())
        ret[0]=0
        ret[1]=datetime.datetime.combine(c, datetime.datetime.min.time())
        return (ret)
#----------------------------------------------------------- 

# ---- Public Method: Setup der Saison-Liste----------------
#  sammle Sommeranfang/Ende und Winteranfang/Ende in Liste dates
#  do this über die ersten 2 Saisons
    def check_saison_init(self):
        self.heute = date.today()
        self.heute=datetime.datetime.combine(self.heute, datetime.datetime.min.time())
        self.myprint (DEBUG_LEVEL2, "--> ActionParser check_season_init called")
#  sammle Sommeranfang/Ende und Winteranfang/Ende in Liste
#  do this über die ersten 2 Saisons
        for i in range(2):
            ret=self.__datechange((ActionParser.saison_list[i][1]))
            if ret[0]==9: 
                self.myprint (DEBUG_LEVEL0, "ActionParser Monat change to %s hat Format-Fehler" % ActionParser.saison_list[i][0]) 
            else: 
                self.dates[i].append(ret[1])
            ret=self.__datechange((ActionParser.saison_list[i][2]))
            if ret[0]==9: 
                self.myprint (DEBUG_LEVEL0,  "ActionParser Monat change to %s hat Format-Fehler" % ActionParser.saison_list[i][0]) 
            else: 
                self.dates[i].append(ret[1])
#           loop fertig            
            
        if self.debug > 1:          # gefundene Liste ausgeben test
            print ("check_saison_init dates:")
            print (self.dates)

        return (int(ret[0]))
#--------------------------------------------------


# ---- Public Method zum Ermitteln der aktuellen Saison (Sommer/Winter/Zwischen)
#       Falls Simulation aktiviert ist, wird zu simulierende Saison returned
#   return ist einen Liste
#       Element 0: entweder (0=Sommer,1=Winter,2=Zwischen  ODER >6 ist Error)
#       Element 1: aktuelle Saison im Textformat
#       Element 3: diese Saison ist simuliert
#       Element 4: ControlFile ID
    def check_saison(self,season_simulate):
        self.myprint (DEBUG_LEVEL1, "--> ActionParser check_season called mit simulate {}".format(season_simulate))

#   Beim testen kann hier aktuelles Datum für Tests angegegeben werden.
#   für Produktion auskommentieren
#-----------
#    self.heute=date(2018, 8, 10)
#    self.heute=datetime.datetime.combine(defglobal2.heute, datetime.datetime.min.time())
#---------------
        retcode=[0,0,0,0]
#   zuerst Plausi-Kontrolle der Daten Sommer und Winter, Zwischensaison hat keine Daten.

        for i in range(3):
            self.myprint (DEBUG_LEVEL3, "Liste Saison2: {}".format(ActionParser.saison_list[i]))

 #       print (self.dates)
        if self.dates[0][0] >= self.dates[0][1]:
            retcode[0]=9
            retcode[1]="Sommer daten falsch"
            return(retcode)
        if self.dates[1][1] >= self.dates[1][0]:
            retcode[0]=9
            retcode[1]="Winter daten falsch"
            return(retcode)

# aktuellen Tag ermitteln
        self.heute = date.today()
        self.heute=datetime.datetime.combine(self.heute, datetime.datetime.min.time())
    # Jahresanfang und Jahresende ermitteln (des aktuellen Jahres !)
        anfang = datetime.datetime(2016,1,1,0,0,0)
        anfang = anfang.date().replace(year=self.heute.year)
        anfang=datetime.datetime.combine(anfang, datetime.datetime.min.time())
        ende = datetime.datetime(2016,12,31,0,0,0)
        ende = ende.date().replace(year=self.heute.year)
        ende=datetime.datetime.combine(ende, datetime.datetime.min.time())

        self.myprint (DEBUG_LEVEL2, "--> get saison SA:{} SE:{}  WA:{} WE:{}".format (self.dates[0][0],self.dates[0][1],self.dates[1][0],self.dates[1][1]))    
        self.myprint (DEBUG_LEVEL2, "--> get saison JA:{} JE:{}  HEUTE:{}".format (anfang, ende, self.heute) )   
# Aktuelle Saison finden, das mache ich so:
#
#       if Jahresanfang <= heute <= Winterende      = winter
#       if Winterende   <= heute < Sommeranfang    = zwischen
#       if Sommeranfang <= heute <= Sommerende      = sommer
#       if Sommerende   <= heute < Winteranfang    = zwischen
#       if Winteranfang <= heute <= Jahresende      = winter

        if anfang <= self.heute < self.dates[1][1]:
            retcode[0]=1    #  1 = winter
            retcode[1]=ActionParser.saison_list[1][4]
            self.myprint (DEBUG_LEVEL1, "--> get_saison findet winter 1 ")    

        elif self.dates[1][1] <= self.heute < self.dates[0][0]:
            retcode[0]=2        # 2= zwischensaison
            retcode[1]=ActionParser.saison_list[2][3]
            self.myprint (DEBUG_LEVEL1, "--> get_saison findet zwischensaison (1) ")    

        elif self.dates[0][0] <= self.heute <= self.dates[0][1]:
            retcode[0]=0            # 0= sommer
            retcode[1]=ActionParser.saison_list[0][3]
            self.myprint (DEBUG_LEVEL1, "--> get_saison findet sommersaison ")  

        elif self.dates[0][1] <= self.heute < self.dates[1][0]:
            retcode[0]=2        # 2= zwischensaison
            retcode[1]=ActionParser.saison_list[2][3]
            self.myprint (DEBUG_LEVEL1, "--> get_saison findet zwischensaison (2) ")    

        elif self.dates[1][0] <= self.heute <= ende:
            retcode[0]=1    #  1 = winter
            retcode[1]=ActionParser.saison_list[1][4]
            self.myprint (DEBUG_LEVEL1, "--> get_saison findet wintersaison (2) ")    
          
         
# Nun aber noch prüfen, ob Saison simuliert werden soll und welche  
#   ob simuliert werden soll, steht in   season_simulate[0] und in season_simulate[1] steht, welche saison simuliert werden soll
        if  season_simulate[0]==1:              # 1 heisst simulate saison
            retcode[0]=season_simulate[1]    # simulierte saison        
            retcode[1]=ActionParser.saison_list[ retcode[0]] [3]  # aktuelle saison im Textformat
            retcode[2]=1        # dies heisst: die gemeldete saison ist simuliert

        else:
            retcode[2]=0
#   ein paar variable füllen betreffend saison...
        retcode[3]= ActionParser.saison_list[retcode[0]][4]  
 #       saison_akt=retcode[0]
#   return ist Liste, Erklärung siehe im Kopf
        self.season=int(retcode[0])
        retcode[1]=retcode[1]
        return(retcode)                 # format retcode siehe oben
        
# ---Ende - Funktion und festzustellen, ob aktuell Winter oder Sommerzeit ist


#------- Public Method to set debug -------------------
    def set_debug(self,debug_in):
        self.myprint (DEBUG_LEVEL2, "--> ActionParser set_debug called mit {}".format(debug_in))
    
        self.debug=debug_in




#------Public Methode um Liste der Saisons auszugeben ---------------------------------------
    def list_saison(self):
        print ("\n---------- Liste der Saisons ----------------------------------------- ")
        
        print (ActionParser.saison_list)
        print ("777777777777777777777777777777")
        for i in range(len(ActionParser.saison_list)):

            print ("Saison : {:18}  Start : {:18} Ende : {:18} File-ID : {:30}".format(str(ActionParser.saison_list[i][3]) , \
                str(ActionParser.saison_list[i][1]),str(ActionParser.saison_list[i][2]),ActionParser.saison_list[i][4]))
        print ("---------- Ende Liste der Saisons ------------------------------------- ")
         
        for i in range(len(ActionParser.saison_list)):
            self.myprint (DEBUG_LEVEL3, "Liste Saison1: {}".format(ActionParser.saison_list[i]))


#------ Public Method print alle actions für alle 3 saisons------------------
    def print_allactions(self,li_tage,li_dose):
        self.myprint (DEBUG_LEVEL2, "--> ActionParser print_allactions called ")
    
        for i in range (len(ActionParser.saison_list)):
            self.print_actions(i,li_tage,li_dose)	 # alle gefundenen Saisons in Listen ausgeben    if actions_only: sys.exit(2)
	
	
	
#------ Public Method gebe Saison Info zurück ---------------
    def get_saison_info(self):
        self.myprint (DEBUG_LEVEL1, "--> ActionParser get_season_info called ")
 
        return (ActionParser.saison_list)
      


# ***** Public Method print alle Aktionen in Liste 1, 2 und 3 *************
    def print_actions(self,season_in,li_tage,li_dose, li_zimmer):
    
        print ( "\n-----------------------------------------------------------------------")
        print (  "---- Liste aller Aktionen in Steuerfile: %s " % ActionParser.saison_list[season_in][4])
        print (  "-----------------------------------------------------------------------")

    
    #  Folgende liste woche2 nur für die grafische Darstellung der Schaltzeiten   
    #  dies sind die Zeilen: für jeden der 7 Wochentage 8 Zeilen (für die maximal 8 Dosen)  
            
        self.woche2 = [
            [ [] for z in range (self.maxdose)] for z in range (7)
        
            ]   
   
       
    #  alle Zellen init mit "-"
        for z in range (self.maxday):            # init alle Zeilen für alle Tage mit '-'
            for i in range (self.maxdose):
                for k in range(self.maxlen):
                    self.woche2[z][i].append('-')
    # nun ist die grafische Darstellung vorbereitet...
    
    #
    #  Liste 1 *********************************************
    #
        print( "Liste 1:  Aktionen pro Wochentag ---------------\n")
        liste_aller_tage = self.alle_tage_pro_saison(li_tage,season_in )    # extrakt liste alle Tage der gegebenen saison

        for wochentag,tag in enumerate(liste_aller_tage):       # loop über alle Tage 
  
            l = len(tag)                # hat Tag überhaupt Aktionen ?
            if l != 0:                              # ja, hat er
                print (  "Wochentag: %s - Anzahl Aktionen: %d" % (self.Weekdays[wochentag], l))
                for aktion in tag:      # loop über alle Aktionen eines Tages
                    switch = "On"
	# hole ein/aus für action j am tag i			
                    if aktion[2] == 0:
                        switch = "Off"
                    print ( "Zeit: %s Dose: %s  Switch %s" % (aktion[0],aktion[1], switch))
        print (  "Ende Liste Aktionen pro Wochentag ----------------------\n")
    
    #
    #  Liste 2 ***********************************************
    #
        print ( "Liste 2: Aktionen pro Dose ----------------------\n")
        
      
        tag_dose_liste = self.alle_tage_pro_saison(li_dose,season_in )    # extrakt liste alle Tage der gegebenen saison
     
        for workday, tag in enumerate (tag_dose_liste):             # loop über alle Tage
            print (  "---- %s  ----------------" % self.Weekdays [workday] )
            for dosennummer, dose in enumerate(tag):                # loop ueber alle dosen des tages
                anzact = len(dose)                                    # number of actions for this dose on this day
       
                if anzact == 0:
                    continue     #  keine Aktionen, also skip 
                print ("---- Dose %d, Anzahl Actions %d " % ((dosennummer),anzact))

                if anzact % 2:
                    print ("Error, Dose %s hat ungerade Anzahl Actions -------"   %  anzact  )     
#                 
                for k in range(0,anzact,2): # loop über alle Aktionen einer Dose
                    print ("Zeit: %s, Action: %s" % (dose[k][0],self.onoff[dose[k][1]])  )
                    print ("Zeit: %s, Action: %s" % (dose[k+1][0],self.onoff[dose[k+1][1]])  )
                
                #  anzahl und position feststellen für gedachte Zeitachse 
                    ret=self.__posanz( float(dose[k][0] ) , float(dose[k+1][0]) )
                    self.myprint (DEBUG_LEVEL3, "    Return: Pos: %d  Len: %d" % (ret[0], ret[1])  )
                
                # Nun den gewählten Charakter an die ermittelte Position und Länge in der passenden Zeile (Zeitachse) schreiben
                    self.__setburn (self.woche2, (workday), (dosennummer) ,ret[0],ret[1])    # i=tag / j= dose / ret[0]=Position / ret[1]= Länge

                pass
# -----------------------------
## Ende einer Dose
#-----------------------------
        pass
# -----------------------------
# Ende aller Dosen
#-----------------------------

        pass

# -----------------------------
# Ende aller Tage
#-----------------------------
        print (  "Ende Liste Aktionen pro Dose ------------------------\n")
        print ('\r' )

    #
    #  Liste 3 ***************************************************
    #
        print (  "Liste 3: Schaltaktionen Graphisch ------------\n")

        for i in range(self.maxday):             # über alle Tage
            print ("%s" % self.Weekdays[i]  )
            print ("%s" % self.timelin3  )

            for k in range (self.maxdose):       # über alle Dosen
                for u in range(self.maxlen):     # Zeitachse hat 90 Stellen
                    sys.stdout.write(self.woche2[i][k][u])
                print ("  Dose %d" % (k+1)  )  # Am Ende anfügen Dosennummer 
          #  print ('\r')
            print ("\r")
 
        print (  "-----------------------------------------------------------------------")
        print (  "---- ENDE Liste aller Aktionen in Steuerfile: %s " % ActionParser.saison_list[season_in][4])
        print (  "-----------------------------------------------------------------------")


# *************************************************

    def getText(self,nodelist):
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
        return ''.join(rc)


# ***** Public Method readfile (xml-file) and parse ***************
#       lesen des für die verlangte Saison (season_input) passenden XML Files und versorgen der Daten in
#       den listen li_tage und li_dosen der entsprechenden Saison
    def __parse_file (self, filename,season_input,li_tage,li_dose,li_zimmer):
        ret=0
 
 
        
        self.myprint (DEBUG_LEVEL2,  "ActionParser Start Parsing Inputfile: %s season_in: %d" % (filename, season_input))
        try:
            DOMTree = xml.dom.minidom.parse(filename)
            aktionen = DOMTree.documentElement
        except xml.parsers.expat.ExpatError as e:
            self.myprint (DEBUG_LEVEL0,  "ActionParser: XML File ist nicht ok, not well formed, muss aufhoeren")
            self.myprint (DEBUG_LEVEL0,  "Parser meldet dies:")        
            self.myprint (DEBUG_LEVEL0,  "{}".format(e))   
            ret=9
            return(ret)
#  ok, xml file scheint io

        if aktionen.hasAttribute("saison"):
            saison = aktionen.getAttribute("saison")
            ActionParser.saison_list[season_input][3] = saison
  
# Hole Identifier aus dem File - der sagt was aus über den File

        
        try:
            ActionParser.saison_list[season_input][4] = aktionen.getElementsByTagName("file_id")[0].firstChild.data
        except:
            self.myprint (DEBUG_LEVEL0,  "Element file_id  nicht gefunden im File: {}" .format(filename))
            ret=9
            return(ret)
        try:
            ActionParser.saison_list[season_input][1] = aktionen.getElementsByTagName("from_date")[0].firstChild.data
        except:
            pass
        try:
            ActionParser.saison_list[season_input][2] = aktionen.getElementsByTagName("to_date")[0].firstChild.data
        except:
        
            pass

#   Note ActionParser.saison_list[season_input][0]  wurde bereits in get_files() abgefüllt 
#
        ActionParser.saison_list[season_input][1] = ActionParser.saison_list[season_input][1].encode(encoding='UTF-8') 
        ActionParser.saison_list[season_input][2] = ActionParser.saison_list[season_input][2].encode(encoding='UTF-8')         
        ActionParser.saison_list[season_input][3] = ActionParser.saison_list[season_input][3].encode(encoding='UTF-8') 
    
        action=list()
        actionListperDay=list()

 #       print (ActionParser.saison_list)
        d=0
        s=0

        if ret >0: 
            return(ret)
#   Erklärung des Elements list_tage: das ist eine Liste von Listen
#   -----------------------------------------------------------
#   Nämlich:
#   Eine Liste von 3 Elementen, je eines für die 3 Saisons, jedes dieser Elemente enthält:
#   Eine Liste von 7 Elementen Weekday (eines für jeden Wochentag 0-7) 
#   Jedes Element Weekday ist eine Liste von Schaltaktionen (actions) für den Wochentag
#   Jede Schaltaktion (action) ist ebenfalls einen Liste (Zeit, Dose, On/Off)
#
#
#   Element action = (Zeit, Dose, ON/OFF)
#
#        
#
#   Erklärung des Elements liste_dose : das ist eine Liste von Listen von Listen
#   ----------------------------------------------------------------------
#   Nämlich:
#   Eine Liste von 3 Elementen, je eines für die 3 Saisons, jedes dieser Elemente enthält:
#   Eine Liste von 4 Dosen-Elementen (eines für jede Dose 0-3) 
#   Jedes Dosen-Element besteht Wochentages-Elementen (0-7)
#   Jedes Wochentag-Element besteht aus einer Liste von Schaltaktionen
#   Jede Schaltaktion (action2) ist ebenfalls einen Liste (Zeit, On/Off)
#
    
        dosen = aktionen.getElementsByTagName("dose")
        anzdosen = len (dosen)
        
        for i in range(7):
            li_dose[season_input].append([])     # append tageslist zu season
            li_tage[season_input].append([])     # append tageslist zu season
            for y in range (len(dosen)+1):
                li_dose[season_input][i].append([])  
            
#        print ("Anzahl Tage: {} ". format(len(li_tage[0])))

#
 
#   Main Loop for parsing -----------------
        for dose in dosen:                              # loop über alle Dosen im File
            self.myprint (DEBUG_LEVEL3,  "Anzahl Dosen: %d " % len(dosen))
            
            if dose.hasAttribute("name"):
                zimmer = dose.getAttribute("name")
        
#           d+=1                    # dose 0 skippen 
            dosennummer = int(dose.getElementsByTagName("dose_nr")[0].firstChild.data)
          
            li_zimmer.append(zimmer)

            self.myprint (DEBUG_LEVEL3,  "Process Dosennummer: {}  Zimmer: {} -----------------".format(dosennummer,zimmer))
                
# get days for a Dose
            days = dose.getElementsByTagName("tag")	
            self.myprint (DEBUG_LEVEL3,  "Anzahl Tage : %s " % len(days))

  #      print (li_tage)

            for day in days:                            # loop über alle Tage einer Dose
# get weekday number for a day	

                if day.hasAttribute("nummer"):
                    wochentag = int(day.getAttribute("nummer"))
                
                self.myprint (DEBUG_LEVEL3, "--------------------------------------")
                self.myprint (DEBUG_LEVEL3,  "Process     weekday: %s" % wochentag)
# get off/on sequences for a weekday
                sequenzen = day.getElementsByTagName("sequence")	
                self.myprint (DEBUG_LEVEL3,  "Anzahl Sequenzen: {}".format(len(sequenzen)))
                for sequenz in sequenzen:
                    s+=1
                    start = str(sequenz.getElementsByTagName("ON")[0].firstChild.data)
                    stop = str(sequenz.getElementsByTagName("OFF")[0].firstChild.data)
                    self.myprint (DEBUG_LEVEL3, "Dose: %d Wochentag: %d  %s/%s" % ( dosennummer,wochentag, start,stop ))
                    self.myprint (DEBUG_LEVEL3, "Processing Dose %s  Wochentag %s " % (dosennummer,wochentag)	)		
# create list action und list action2  from a sequence
          # für startzeit  <-----
                    action= [start,dosennummer,1]                   # action ist list aus 3 Elementen
                    li_tage[season_input][wochentag].append(action)       # append this action zum Wochentag
                    action2=[start,1]                               # action2 ist list aus 2 Elementen      
                    li_dose[season_input][wochentag][dosennummer].append(action2)       # append this actions zum Wochentag und Dosennummer

                    self.myprint (DEBUG_LEVEL3, "Action start fuer Dose: %s  Wochentag: %s action: %s" % (dosennummer,wochentag,action) )
                    self.myprint (DEBUG_LEVEL3, "Action2 start fuer Dose: %s  Wochentag: %s action2: %s" % (dosennummer,wochentag,action2) )

                    self.myprint (DEBUG_LEVEL3, "Action1 fuer Dose: %s  Wochentag: %s Action: %s ON" % (dosennummer,wochentag,action[0]) )

          # ditto für stopzeit  <-----
                    action= [stop,dosennummer,0]                   # action ist list aus 3 Elementen
                    li_tage[season_input][wochentag].append(action)      # append this action zum Wochentag
                    action2=[stop,0]                               # action2 ist list aus 2 Elementen  
                    li_dose[season_input][wochentag][dosennummer].append(action2)       # append this actions zum Wochentag und Dosennummer
                    self.myprint (DEBUG_LEVEL3,  "Test:") 
                    self.myprint (DEBUG_LEVEL3,  li_tage[season_input][wochentag])

                    self.myprint (DEBUG_LEVEL3, "Action stop fuer Dose: %s  Wochentag: %s action: %s" % (dosennummer,wochentag,action) )
                    self.myprint (DEBUG_LEVEL3, "Action2 stop fuer Dose: %s  Wochentag: %s action2: %s" % (dosennummer,wochentag,action2) )

                    self.myprint (DEBUG_LEVEL3, "Action2 fuer Dose: %s  Wochentag: %s Action: %s OFF" % (dosennummer,wochentag,action[0]) )
		
# done with wochentag -------------------------------------
                self.myprint (DEBUG_LEVEL2,  "Done with Dose: {} Tag: {}".format(dosennummer,wochentag))
            
           
# done with a day ----------------------------------------
            self.myprint (DEBUG_LEVEL2, "Done with Days for Dose {}".format(dosennummer))

# done with dosen ----------------------------------------
        self.myprint (DEBUG_LEVEL2,  "Done with Dosen   ")

        for i in range(len(li_tage[season_input])):       # ueber alle tage
#        x=li_tage[i].pop(0)
#        x=li_tage[season_input][i].pop(0)             # dose 0 war zuviel, wegen Art der nummerierung der Dosen !!
            li_tage[season_input][i].sort()
    						
        self.myprint (DEBUG_LEVEL2, "\nAnzahl Dosen gefunden: {}".format(len(dosen)))
        self.myprint (DEBUG_LEVEL2, "Anzahl Sequenzen gefunden: {}".format(s))
        self.myprint (DEBUG_LEVEL2, "ActionParser Done Parsing Inputfile")
        self.maxdose = len(dosen)               # uebernehme dies für printout anzahl dosen
        return(ret)
# *************************************************

#-------------------------------------------
# Public Method: Einlesen und Parsen der Steuerfiles
#  Parameter li_tage und li_dosen  sind zwei Listen, die vom Caller übergeben werden
#   sie werden hier abgefüllt mit den Daten aus dem XML File 
#   values ist liste der Daten aus dem Config-File, dort finden wir XML-Filename-Prefix und den namen der saison
#------------------------------------------
    def get_files(self,li_tage,li_dose,li_zimmer,values):
        ret=0
#   Etablieren des Pfads der Steuerfiles, sind im Subdir xml des switcher dirs
        self.path=self.path + "/xml"
        self.myprint (DEBUG_LEVEL1,  "ActionParser Pfad fuer Steuerfiles: {}".format(self.path))
# Einlesen und Parsen der Steuer-Files für alle ActionParser.saison_list             alles neu juni2018
#-------------------------------------------------------   
#    zuerst namen der Files aus dem Congi-File holen - die Werte stehen schon in values
        v = values["xmlfile_prefix"]      

        for i in range (3):      
            u = values["saison_" + str(i+1)]    # wir etablieren die Position der aktuellen saison
            print (v,u)                              
#  Lesen des xml Steuer-Files , Filename erstellen--------------    
            xmlfile1=self.path + "/" + v + "-" + u
 
            xmlfile1=xmlfile1 + ".xml" 
            ActionParser.saison_list[i][0]=v          # Hautteil des Filenamens abfüllen in die Klassen Variable
            
#            ActionParser.saison_list[i][0]=values[1+(i*2)]          # Hautteil des Filenamens abfüllen in die Klassen Variable
                                                                    # wird aber nirgends verwendet.....
# check ob file existiert
            if os.path.exists(xmlfile1):
                self.myprint (DEBUG_LEVEL1, "ActionParser XML Steuerfile gefunden: %s" % xmlfile1)	# file found
            else:
                self.myprint (DEBUG_LEVEL0, "ActionParser XML Steuerfile %s nicht gefunden" % xmlfile1)	# file not found      
                sys.exit(2)
 
            self.myprint (DEBUG_LEVEL3, "filename: %s  Season: %s" % (xmlfile1, ActionParser.saison_list[i][0]))
#       File found, nun parsen und versorgen 
            ret=self.__parse_file(xmlfile1,i,li_tage,li_dose,li_zimmer)			# parse Input Datei (XML) 	and fill lists with data
            if ret > 0:
                self.myprint (DEBUG_LEVEL0, "ActionParser Fehler bei Parsen von File: {}".format(xmlfile1))
                break
        #   Ende des for loops über alle ActionParser.saison_list....
#---- Ende Loop über alle Steuerfiles ----------------------


        self.myprint (DEBUG_LEVEL2,  "ActionParser Parsing done, retcode: {}".format(ret))	
#   
#       bei grossem debug die Liste aller Aktionen ausgeben
        if self.debug > DEBUG_LEVEL2:
            for y in range(len(li_tage[0])):
                print ("Tag: {}".format(y))
                for i in range(len(li_tage[0][y])):
                    print (li_tage[0][y][i])
#       bei grossem Debug die Liste aller gefundenen Zimmer ausgeben
            print ("\nDiese Zimmer in den 3 XML Files gefunden:")
            for item in li_zimmer:
                print ("Zimmer: {}".format(item.encode(encoding='UTF-8')))
       
        return(ret)
#---------------------------------------------------------
#


#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swparse2.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    

