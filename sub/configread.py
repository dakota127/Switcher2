#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class ConfigRead 
#   
#   zum Lesen eines Config Files im Format .ini
#
#   diese Class erbt von der MyPrint Class
#
#   stellt eine einzige public method config_read zur Verfügung
#   mit welcher Configfiles gelesen und geparst werden können
#   Input Parm ist eine List, welche die Namen/Wert Paare enthält
#   Dise Paare müssen auch im Konfig File vorkommen in einer bestimmten Sektion
#
#   Es gibt auch ein Test-Programm testconfig.py für Tests
#
#   August 2018, Peter K. Boxler
#
## ***** Imports ******************************
import sys, getopt, os
from configparser import SafeConfigParser
from sub.myprint import MyPrint
from datetime import date, datetime
# ***** Konstanten *****************************

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
#


#-------------------------------------------------
#   function to read configfile
#   all parameters are passen in directory configval
#   entries filename and section are removed later
#   so only config-entry key remain
#-------------------------------------------------
#----------------------------------------------------
# Class Definition Aktor, erbt vom MyPrint
#----------------------------------------------------
class ConfigRead (MyPrint):
    ' klasse ConfigRead '
    instzahler=0               # Class Variable
    
#--- INit Methode dieser Klasse ----------------------------    
    def __init__(self, debug_in):  # Init Funktion
        self.nummer = ConfigRead.instzahler
        self.debug=debug_in        
        self.myprint (DEBUG_LEVEL1,"--> ConfigRead {} init called".format (self.nummer))
        self.counter=0
        ConfigRead.instzahler +=1            # erhögen dosenzahler
        self.parser=0
        self.ret = 0
#--- Methode config_read dieser Klasse ---------------------------- 
#   Parameter value ist Python List
#  definiert in swcfg_switcher.py   
    def config_read(self,filename,sektion,values):
        self.counter=0
        self.myprint (DEBUG_LEVEL1,"--> ConfigRead configRead called, File: {}, Sektion:{} ".format(filename,sektion))
        
        options=list()
        retconfigval=list()
        self.myprint (DEBUG_LEVEL3,"ConfigRead Liste VOR read file: \n{}".format (values))

        
        self.filename=filename              # entnehme den Config Filename
        self.section=sektion               # entnehme die section ID
    
        if self.debug > DEBUG_LEVEL2:
            print ("config_read: default-values (vor read): ")
            print (values)   
            for z in range(0,(len(values)-1),2):
                print (values[z],values[z+1])
            
#        for i in range (4):     # dann nehme ersten 2 paare weg, die geben wir nicht zurück
#            values.pop(0)


        self.parser = SafeConfigParser()         # eine Instanz der Klasse SafeConfigParser machen
        
        if not os.path.isfile(self.filename):
            self.myprint (DEBUG_LEVEL0, "ConfigRead Configfile {} nicht gefunden".format(self.filename))
            return(9)
            
        fp = open(self.filename)   
        ret=self.parser.readfp (fp)  
#        ret=self.parser.read(self.filename)
  
        if self.parser.has_section(self.section):
            pass 
        else:
            self.myprint (DEBUG_LEVEL0,"ConfigRead Abschnitt {} fehlt in Configfile {}".format(self.section,self.filename)) 
            return(9)

        if self.debug > DEBUG_LEVEL2:
            for name, value in self.parser.items(self.section):   # returns a list of tuples containing the name-value pairs.
                print ("Name: {}  Value: {} ".format(name, value))
        pass
        for name, value in self.parser.items(self.section):     # returns a list of tuples containing the name-value pairs.
            try:
                u=values.index(name)              # wo kommt der gelieferte name vor (index)
                values[u+1]=value.encode(encoding='UTF-8')              # versorge value dort.
#                values[u+1]=value.decode              # versorge value dort.                
                self.counter +=1                  # anzahl gefundene Name erhöhen
            except:
                self.myprint (DEBUG_LEVEL0,"ConfigRead Name {} not found in uebergebener liste {}".format(name, values)) 
                
        if self.counter ==0:
            self.myprint (DEBUG_LEVEL0,"ConfigRead Null Namen gefunden in interner List für section {}".format(self.section)) 
            self.ret=8
        else: self.ret=0
        fp.close()
        self.myprint (DEBUG_LEVEL3,"ConfigRead Liste NACH read file: \n{}".format (values))
        return(self.ret)

#--- Methode get_value dieser Klasse ---------------------------- 
#   Parameter values ist Python List   
#  definiert in swcfg_switcher.py   
    def get_value(self, values,name):
        self.myprint (DEBUG_LEVEL2,"--> ConfigRead get_value {} called".format (name))
    
        try:
            u=values.index(name) + 1           # wo kommt der gelieferte name vor (index)
            return(values[u])
        except:
            self.myprint (DEBUG_LEVEL0, "ConfigRead Name {} nicht gefunden".format(name))
        
            return(9999)


#--- Methode write_value dieser Klasse ---------------------------- 
#     
# hier wird der file swdosen.ini gelsen und die dort gespeicherte Anzahl Dosen zurückgegeben
# neu im Januar 2019
    def read_dosenconfig (self,filename):
    
        found = False
        self.myprint (DEBUG_LEVEL2,"--> ConfigRead read_dosenconfig called")
       
        try:                                # prüfen, ob der File schon existiert
            fp = open(filename)
            self.ret=self.parser.readfp (fp) 
            if self.parser.has_section("anzdosen"):     # sektion vorhanden ?

                for name, value in self.parser.items("anzdosen"):   # returns a list of tuples containing the name-value pairs.
                    if self.debug > DEBUG_LEVEL2:
                        print ("Name: {}  Value: {} ".format(name, value))
                    if name == "anzahl":
                        dosen= int(value)               # entnehme die anzahl
                        found = True     
                fp.close()                      # close file           
            else:
                self.myprint (DEBUG_LEVEL0,"ConfigRead Abschnitt {} fehlt in Configfile {}".format("anzdosen","swdosen.ini"))  
            
            self.myprint (DEBUG_LEVEL2,"Dosen anzahl gefunden: {}".format(dosen))
        except FileNotFoundError:
            self.myprint (DEBUG_LEVEL0,"File swdosen.ini nicht gefunden")

        if found == True:
            self.myprint (DEBUG_LEVEL2,"--> ConfigRead read_dosenconfig anzahl gefunden. {}". format (dosen))
        else:
            self.myprint (DEBUG_LEVEL0,"--> ConfigRead read_dosenconfig nehme defaultwert 4 dosen")
            dosen = 4        
  
        return (dosen)


#--- Methode write_value dieser Klasse ---------------------------- 
#     
# hier wird der config-File dosen.ini jedesmal neu geschrieben, er enthält nur eine Sektion mit zwei tuples 
# neu im Januar 2019
    def write_value (self, filename, wert):
        dosen= 99                   # default wert bei not found
        found = False
        self.myprint (DEBUG_LEVEL2,"--> ConfigRead write_value {} called".format (wert))
# zuerst alle Werte im config löschen, damit nur die neuen Tuple geschrieben werden.
        
        for section in self.parser.sections():
            self.parser.remove_section(section)
       
        try:                                # prüfen, ob der File schon existiert
            fp = open(filename)
            self.ret=self.parser.readfp (fp) 
            if self.parser.has_section("anzdosen"):     # sektion vorhanden ?

                for name, value in self.parser.items("anzdosen"):   # returns a list of tuples containing the name-value pairs.
                    if self.debug > DEBUG_LEVEL2:
                        print ("Name: {}  Value: {} ".format(name, value))
                    if name == "anzahl":
                        dosen= int(value)               # entnehme die anzahl
                        found = True     
                fp.close()                      # close file           
            else:
                self.myprint (DEBUG_LEVEL0,"ConfigRead Abschnitt {} fehlt in Configfile {}".format("anzdosen","swdosen.ini"))  
            
            self.myprint (DEBUG_LEVEL2,"Dosen anzahl gefunden: {}".format(dosen))
        except FileNotFoundError:
            self.myprint (DEBUG_LEVEL2,"File swdosen.ini nicht gefunden, wird neu erstellt")

        self.myprint (DEBUG_LEVEL3,"--> ConfigRead write_value found: {} gefunden. {} neu: {}". format (found, dosen, str(wert)))

        if (dosen != wert):
        
        # zuerst alle Werte im config löschen, damit nur die neuen Tuple geschrieben werden.
            self.myprint (DEBUG_LEVEL2,"--> ConfigRead write_value nun schreiben")       
            for section in self.parser.sections():
                self.parser.remove_section(section)

            cfgfile = open(filename,'w')

            self.parser.add_section('anzdosen')
            self.parser.set('anzdosen', 'anzahl', str(wert)) 
            self.parser.set('anzdosen', 'written', str(datetime.now()))

# Writing our configuration file to 'swdosen.ini'
            self.parser.write(cfgfile)
            cfgfile.close()
            self.myprint (DEBUG_LEVEL0,"--> ConfigRead write file swdosen.ini geschrieben, Anzahl: {}".format(str(wert))) 
        else:
            self.myprint (DEBUG_LEVEL1,"--> ConfigRead write anzahl dosen identisch, nichts schreiben")


# --------------------------

            
# *************************************************
# Program starts here
# *************************************************

# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("configread.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
#**************************************************************
#  That is the end
#***************************************************************
#