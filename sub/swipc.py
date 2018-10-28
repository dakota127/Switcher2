#!/usr/bin/python
# coding: utf-8
# ***********************************************
# ***********************************************************
# 	Interprocess Communication
#
#   hier sind 2 Klassen definiert: IPC_CLient und IPC_Server
#   
#   enkapsulieren die Behandlung von IPC
#   
#   August 2018 PBX
#************************************************
#
import os
import sys
import time
from time import sleep
import zmq

from datetime import date
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3


#-------------------------------------------------
# Class IPC_Server, erbt vom Class MyPrint
#   diese Class erbt von der MyPrint Class
#   
#   Interprocess Communication server-part
#   Function check() wird in programm switcher periodisch aufgerufen für check auf request vom client
#   Hier wird ebenfalls die Antwort an den Client gesandt
#   Die Antwort ist ein String und er kann sein:
#   'ackn'  Acknowledge, ja ist ok
#   'nack'  unbekannter command, kann nichts machen
#   'stat ..............' Antwort auf den Status Request, langer string

#--------------------------------------------------
class IPC_Server(MyPrint):
    ' klasse IPC_Server '

#    Definition der Class Variables
    instzahler=0           # Class variable Anzahl  instanzen
    context=0
    socket=0

#-------Constructor der Klasse ------------------------------------------
# init Interprocess Comm, Sockets und so, mittels Module zeroMQ
# siehe hier  http://zeromq.org
#
    def __init__ (self,values,debug_in):
        self.debug=debug_in
        self.resultcode = 0
 # ZMQ context, only need one per application
        self.myprint (DEBUG_LEVEL1,   "--> IPC_Server _init_ called")
        u=values.index("ipc_endpoint_s") + 1           # wo kommt der gelieferte name vor (index)
        IPC_Server.context = zmq.Context()
        IPC_Server.socket = IPC_Server.context.socket(zmq.REP)  # war REP
 #   socket.bind("tcp://*:5555")
 
        try:
            IPC_Server.socket.bind(values[u])
        except:
            self.resultcode = 8
            self.myprint (DEBUG_LEVEL0,   "--> IPC_Server _init_  Socket Connection fehlerhaft")
            self.myprint (DEBUG_LEVEL0,   "--> Eventuell bereits eine Instanz von switcher 2 am Laufen ?!")
            
            
#------------------------------------------------

#-------------Lösche Instanz ------------------------2-----------------
# close sockets und so
    def __del__(self):

#       self.myprint (DEBUG_LEVEL1,   "--> IPC_Server __del__ called")
        if self.resultcode == 0:
            IPC_Server.socket.close()
            IPC_Server.context.term()

#-------------melde resultcode  ------------------------2-----------------
# liefere resultcode
    def get_result(self):

        self.myprint (DEBUG_LEVEL2,   "--> IPC_Server get_result() called")
        return (self.resultcode)


#--------------Check Request ------------------------------------------
# check sockets und hole eingetroffene Meldung
# mit try/except wird eventueller Fehler abgefangen
# d_status ist bereits aufbereitet
    def ipc_check(self,callback):

#   instanz Variablen
        self.anzerr=0
        self.term=0
        self.status=0
        self.retcode=0
        self.request=0
        self.dose=0
        self.message=""
        self.reply=""
        self.delay=0

        self.myprint (DEBUG_LEVEL2,   "--> IPC_Server ipc_check called")
        # wait for incoming message
        try:
            self.message = IPC_Server.socket.recv_string(zmq.DONTWAIT)
            self.myprint (DEBUG_LEVEL2,  "IPC_Server Received request: {} ".format(self.message))
        except zmq.ZMQError as err:

            self.myprint (DEBUG_LEVEL3, "ipc_check: Receive error Socket: " + str(err))
            self.anzerr+=1
            return (0,0,0,0)
        self.reply="ackn"
        self.delay=0
        if self.message:
            if  "mdeb" in self.message.strip():      # start debug
                self.debug=2

            elif  "sdeb" in self.message.strip():    # stop debug
                self.debug=0
            elif  "stop" in self.message.strip():
                self.myprint (DEBUG_LEVEL3, "ipc_check: stop received von client")
                self.term=1
            elif  "stat" in self.message.strip():
                self.reply=callback(2)              # gebe grossen status zurueck     zuerst erstellen
            elif  "stad" in self.message.strip():
                self.reply=callback(1)              # gebe kleinen status zurueck     zuerst erstellen
            elif  "wett" in self.message.strip():
                self.reply=callback(3)              # gebe wetter status zurueck     zuerst erstellen

                
            elif   self.message.find("spez") != -1:
                self.s=int("".join(filter(str.isdigit, self.message)))
                self.myprint (DEBUG_LEVEL3, "Serverdelay: %d" % s)
                self.delay=s/1000

            elif  self.message.find("aein") != -1:     # Command Alle ein
                self.retcode=5                       # 5 means alle ein
            elif  self.message.find("aaus") != -1:     #
                self.retcode=6                       # 6 means alle aus
            elif  self.message.find("anor") != -1:     #
                self.retcode=7                       # 6 means alle reset auf auto
            elif  self.message.find("mmit") != -1:     #
                self.retcode=8                       # 6 means alle reset auf auto
            elif  self.message.find("mnie") != -1:     #
                self.retcode=9                       # 6 means alle reset auf auto
            elif  self.message.find("home") != -1:     #
                self.retcode=10                       # change zuhause status

            elif  self.message.find("ein") != -1:    # Command dXein
                self.dose=int(self.message[1:2])
                self.retcode=2                       # 2 means einschalten
            elif  self.message.find("aus") != -1:     # Command dXaus
                self.dose=int(self.message[1:2])
                self.retcode=3                       # 3 means ausschalten
            elif  self.message.find("nor") != -1:     # Command dXnor
                self.dose=int(self.message[1:2])
                self.retcode=4                       # 4 means normal

            else:                   # unbekannter request
                self.myprint (DEBUG_LEVEL2,   "--> IPC_Server falscher request: {}".format(self.message))
                sleep(0.1)
                self.reply="nack"

            sleep(self.delay)
            IPC_Server.socket.send_string(self.reply)   # sende ack oder nack oder status
            self.myprint (DEBUG_LEVEL3, "IPC_Server This reply sent: {}".format(self.reply))

            self.myprint (DEBUG_LEVEL3, "IPC_Server this return given: {}, {}, {}".format(self.retcode, self.dose, self.term ))

            sleep(0.1)
        return (self.retcode,self.dose,self.term, self.debug)
#--------------------------------------------------------------


#-------------------------------------------------
# Class IPC_Server, erbt vom Class MyPrint
#   diese Class erbt von der MyPrint Class
#   
#   Interprocess Communication server-part
#   Function check() wird in programm switcher periodisch aufgerufen für check auf request vom client
#   Hier wird ebenfalls die Antwort an den Client gesandt
#   Die Antwort ist ein String und er kann sein:
#   'ackn'  Acknowledge, ja ist ok
#   'nack'  unbekannter command, kann nichts machen
#   'stat ..............' Antwort auf den Status Request, langer string

#--------------------------------------------------
class IPC_Client(MyPrint):
    ' klasse IPC_Client '

#    Definition der Class Variables
    instzahler=0           # Class variable Anzahl  instanzen
    context=0
    socket=0



    # Construktor der Class
    #    zeroMQ_setup(debug,REQUEST_TIMEOUT, SERVER_ENDPOINT,REQUEST_RETRIES)
    #-------------------------------------
    def __init__(self,debug_in, timeout, endpoint, retries):
    
    # Instanz Variablen
        self.msg=" "
        self.stop=0
        self.ret=0
        self.poll=0
        self.debug=debug_in
        self.req_timout=0
        self.request_retries=0
        self.server_setup=""
        self.req_timout=timeout
        self.request_retries=retries
        self.server_setup=endpoint

    
        IPC_Client.context = zmq.Context()
        self.myprint (DEBUG_LEVEL2, "IPC_Client Connecting to server...")
        self.myprint (DEBUG_LEVEL3, "timeout: {}".format (timeout))

        IPC_Client.client = IPC_Client.context.socket(zmq.REQ)
        IPC_Client.client.connect(endpoint)
        self.poll = zmq.Poller()
        self.poll.register(IPC_Client.client, zmq.POLLIN)

    # term zeromq
    #-------------------------------------
    def __del__(self):


        self.myprint (DEBUG_LEVEL2, " IPC_Client  __del__  called")

        IPC_Client.client.close()
        IPC_Client.context.term()


    # sending request und warten auf Antwort
    #-------------------------------------
    def ipc_exchange(self,message_in):

        self.myprint (DEBUG_LEVEL2, " IPC_Client ipc_exchange called mit {}".format(message_in))

        self.returnlist=list()
        self.retries_left = self.request_retries
        self.error=0;
        while self.retries_left:

            self.myprint (DEBUG_LEVEL2, " IPC_Client Sending (%s)" % message_in)
            IPC_Client.client.send_string(message_in)
            self.expect_reply = True
            sleep(0.1)
    #                                       https://github.com/zeromq/pyzmq/blob/master/examples/gevent/poll.py
            while self.expect_reply:
                self.myprint (DEBUG_LEVEL3, " IPC_Client polling socket")
                self.msg = dict(self.poll.poll(self.req_timout))
                self.myprint (DEBUG_LEVEL3, " IPC_Client result polling: %s" % self.msg)
    #            if client in msg and msg[client] == zmq.POLLIN:
                sleep(0.2)
                if self.msg.get(IPC_Client.client) == zmq.POLLIN:
                    self.myprint (DEBUG_LEVEL3, " IPC_Client socks.get done2")
                    self.reply=IPC_Client.client.recv_string()
    #                reply=client.recv_string(zmq.DONTWAIT)
                    if not self.reply:                           # ???
                        break

                    self.myprint (DEBUG_LEVEL3, " IPC_Client Server replied this {}".format (self.reply))
                    self.retries_left = self.request_retries
                    self.expect_reply = False
                    self.error=0
                    return([self.error,self.reply])
                else:
                    self.myprint (DEBUG_LEVEL3, "W: No response from server, retrying...")
                # Socket is confused. Close and remove it.
                    IPC_Client.client.setsockopt(zmq.LINGER, 0)
                    IPC_Client.client.close()
                    self.poll.unregister(IPC_Client.client)
                    self.retries_left -= 1
                    if self.retries_left == 0:
                        self.myprint (DEBUG_LEVEL0, " IPC_Client Server seems to be offline, abandoning")
                        self.error=9
                        return([self.error,""])

                    self.myprint (DEBUG_LEVEL2, " IPC_Client Reconnecting and resending (%s)" % message_in)
                # Create new connection
                    IPC_Client.client = IPC_Client.context.socket(zmq.REQ)
                    IPC_Client.client.connect(self.server_setup)
                    self.poll.register(IPC_Client.client, zmq.POLLIN)
                    self.myprint (DEBUG_LEVEL2, " IPC_Client Re-Sending (%s)" % message_in)
                    self.client.send_string(message_in)
                    self.myprint (DEBUG_LEVEL2, " IPC_Client Re-Sending sent")

    #   fertig mit   while expect_reply:

    #-------------------------------------



#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swipc.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
