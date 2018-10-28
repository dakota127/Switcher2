# coding: utf-8
#  Global Variable StatusInfo für Switcher-Daemon --------------------
# Status (Klein) Info Switcher
#   ist List of List - wird gefüllt und dann in ein JSON konvertiert (was einen String ergibt)
#   dieser String wird vom Switcher an den Client übergeben ,
#   dieser wandelt das Json Object wieder in einen Python List um.
#
status_klein = [
 
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
                ["Version / Hostname", " " ],
                ["Laufzeit Tage", " " ], 
                ["Debug_Status"," " ],
                ["Testmode"," " ],
                ["Schalt-Art", " "],
                ["Wetter"," " ],
                ["Aktuelles Datum", " " ],                
                ["Aktueller Tag", " " ],
                ["Aktionen/Tag", " " ],                
                ["Aktionen done", " " ],
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
                ["Reserve", " "],
               
                
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
               ["Letzte Messung um", " " ],              
               ["Max.Temp. Innen", "" ],
               ["War am", "" ], 
               ["Min.Temp. Innen", "" ],
               ["War am", "" ], 
               ["Max.Feucht. Innen", "" ],
               ["War am", "" ], 
               ["Min.Feucht. Innen", "" ],
               ["War am", "" ], 
               ["Batterie Innen", ""],            

                ]

status_wetter_aussen = [
               ["Temperatur Aussen", "" ],
               ["Feuchtigkeit Aussen","" ],
               ["Letzte Messung um", "" ],              
               ["Max.Temp. Aussen", "" ],
               ["War am", "" ], 
               ["Min.Temp. Aussen", "" ],
               ["War am", "" ], 
               ["Max.Feucht. Aussen", "" ],
               ["War am", "" ], 
               ["Min.Feucht. Aussen", "" ],
               ["War am", "" ], 
               ["Batterie Aussen", ""],            

                ]

#-                
#-------------------------------------


