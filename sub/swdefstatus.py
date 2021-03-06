# coding: utf-8
#  Global Variable StatusInfo für Switcher-Daemon --------------------
# Status (Klein) Info Switcher
#   ist List of List - wird gefüllt und dann in ein JSON konvertiert (was einen String ergibt)
#   dieser String wird vom Switcher an den Client übergeben ,
#   dieser wandelt das Json Object wieder in einen Python List um.
#

info_server = [
                ["Anz Infotuples", "5"],
                ["Anz Dosen konfig", " "],
                ["Wetter konfig", " "],
                ["Reserve1"," "],             
                ["Reserve2"," "],            
                ]
                
status_klein = [
                info_server,
                            
                ["Dosenstatus", " " ],
                ["Nächste Aktion", " " ],
                ["File-ID", " " ],       
                ["Zuhause", " " ],
                ["Temperatur Innen", " " ],       
                ["Temperatur Aussen", " " ],
              
                
                ]
#-------------------------------------
#  Global Variable StatusInfo für Switcher-Daemon --------------------
# Status Info Switcher
#   ist List of List - wird gefüllt und dann in ein JSON konvertiert (was einen String ergibt)
#   dieser String wird vom Switcher an den Client übergeben ,
#   dieser wandelt das Json Object wieder in einen Python List um.
#
status_gross = [
                info_server,
            
                ["Version / Hostname / Dosen", " " ],
                ["Laufzeit Tage", " " ], 
                ["Debug_Status"," " ],
                ["Testmode"," " ],
                ["Schalt-Art", " "],
                ["Wetter"," " ],
                ["Aktuelles Datum", " " ],                
                ["Aktueller Tag", " " ],
                ["Aktionen an diesem Tag", " " ],                
                ["Davon ausgeführt", " " ],
                ["Dosenstatus", " " ],
                ["Aktuelle Zeit", " " ],
                ["Wartend bis"," " ],
                ["Letzte Aktion"," " ],
                ["Zimmer"," " ],
                ["Naechste Aktion", " " ],
                ["Zimmer"," " ],                
                ["Aktuelle Saison", " " ],
                ["Von/Bis", " " ],
                ["File-ID", " " ],
                ["Ist simuliert", " " ],
                ["Weitere Saison", " " ],
                ["Von/Bis", " " ],
                ["Weitere Saison", " " ],
                ["Von/Bis", " " ],               
                ["Zuhause", " " ],
                ["Reset Manuelle", " " ],
                ["MQTT Status", " "],
               
                
                ]
#-------------------------------------
#  Global Variable StatusInfo für Switcher-Daemon --------------------
# Status Info Switcher fuer Wetter
#   ist List of List - wird gefüllt und dann in ein JSON konvertiert (was einen String ergibt)
#   dieser String wird vom Switcher an den Client übergeben ,
#   dieser wandelt das Json Object wieder in einen Python List um.
#

status_wetter_innen = [
               ["Temperatur Innen", " " ],
               ["Feuchtigkeit Innen"," " ],
               ["Messung am", " " ],              
               ["Max.Temp. Innen", "" ],
               ["Gemessen am", "" ], 
               ["Min.Temp. Innen", "" ],
               ["Gemessen am", "" ], 
               ["Max.Feucht. Innen", "" ],
               ["Gemessen am", "" ], 
               ["Min.Feucht. Innen", "" ],
               ["Gemessen am", "" ], 
               ["Batterie Innen", ""],  
                ["Sensorstatus", ""],  
                ["Dauer ms", ""],                          

                ]

status_wetter_aussen = [
               ["Temperatur Aussen", "" ],
               ["Feuchtigkeit Aussen","" ],
               ["Messung am", "" ],              
               ["Max.Temp. Aussen", "" ],
               ["Gemessen am", "" ], 
               ["Min.Temp. Aussen", "" ],
               ["Gemessen am", "" ], 
               ["Max.Feucht. Aussen", "" ],
               ["Gemessen am", "" ], 
               ["Min.Feucht. Aussen", "" ],
               ["Gemessen am", "" ], 
               ["Batterie Aussen", ""],            
                ["Sensorstatus", ""],  
                ["Dauer ms", ""],                          

                ]

#-                
#-------------------------------------


