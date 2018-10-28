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

#--- Methode config_read dieser Klasse ---------------------------- 
#   Parameter configval ist Python List   
    def config_read(self,filename,sektion,values):
        self.counter=0
        self.myprint (DEBUG_LEVEL1,"--> ConfigRead configRead called, File: {}, Sektion:{} ".format(filename,sektion))
        
        options=list()
        retconfigval=list()
        self.myprint (DEBUG_LEVEL2,"ConfigRead Liste VOR read file: \n{}".format (values))

        
        self.filename=filename              # entnehme den Config Filename
        self.section=sektion               # entnehme die section ID
    
        if self.debug > DEBUG_LEVEL2:
            print ("config_read: default-values: ")
            print (values)   
            for z in range(0,(len(values)-1),2):
                print (values[z],values[z+1])
            
#        for i in range (4):     # dann nehme ersten 2 paare weg, die geben wir nicht zurück
#            values.pop(0)


        parser = SafeConfigParser()         # eine Instanz der Klasse CinfigParser machen
        
        if not os.path.isfile(self.filename):
            self.myprint (DEBUG_LEVEL0, "ConfigRead Configfile {} nicht gefunden".format(self.filename))
            return(9)
        ret=parser.read(self.filename)
  
        if parser.has_section(self.section):
            pass 
        else:
            self.myprint (DEBUG_LEVEL0,"ConfigRead Abschnitt {} fehlt in Configfile {}".format(self.section,self.filename)) 
            return(9)

        if self.debug > DEBUG_LEVEL2:
            for name, value in parser.items(self.section):
                print ("Name: {}  Value: {} ".format(name, value))
        pass
        for name, value in parser.items(self.section):     
            try:
                u=values.index(name)              # wo kommt der gelieferte name vor (index)
                values[u+1]=value.encode(encoding='UTF-8')              # versorge value dort.
#                values[u+1]=value.decode              # versorge value dort.                
                self.counter +=1                  # anzahl gefundene Name erhöhen
            except:
                self.myprint (DEBUG_LEVEL0,"ConfigRead Name {} not found in list configval".format(name)) 
                
        if self.counter ==0:
            self.myprint (DEBUG_LEVEL0,"ConfigRead Null Namen gefunden in interner List für section {}".format(self.section)) 
            ret=8
        else: ret=0
        
        self.myprint (DEBUG_LEVEL3,"ConfigRead Liste NACH read file: \n{}".format (values))
        return(ret)

#--- Methode config_read dieser Klasse ---------------------------- 
#   Parameter configval ist Python List   
    def get_value(self, values,name):
        self.myprint (DEBUG_LEVEL2,"--> ConfigRead get_value {} called".format (name))
    
        try:
            u=values.index(name) + 1           # wo kommt der gelieferte name vor (index)
            return(values[u])
        except:
            self.myprint (DEBUG_LEVEL0, "ConfigRead Name {} nicht gefunden".format(name))
        
            return(9999)


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