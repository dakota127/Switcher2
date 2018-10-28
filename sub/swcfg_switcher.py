# coding: utf-8
#  Global Variables für Config-Read- --------------------
#   Version 2  Juni 2018

# ***** Variables *****************************
#   Struktur (Liste) der Daten, die aus dem Configfile swconfig.ini gelesen werden
# s  hier die defaultwerte der 'variablen'
cfglist_swi=[
        "abschnitt", 'switcher',     
        "testmode", "Nein",                         #
        "saison_1" , "summer" ,
        "saison_2" , "winter",
        "saison_3" , "zwischen",         
        "xmlfile_prefix",'xmlprefix',               #
        "setup_mqtt", 0,
        "wetter", 0,
        "ipc_endpoint_c",'defaultipc_client',       #
        "ipc_endpoint_s",'defaultipc_serv',         #
        "gpio_home_led" , 0,                        #
        "gpio_home_switch" , 13,     
        "gpio_home_button" , 15,                              
        "gpio_blink" , 0,
        "oled", 0,                             #
        "mqtt_ipadr" , "",
        "mqtt_port" ,  1883,
        "mqtt_keepalive_intervall" , 45,
        "mqtt_client_id" , "switcher2",   

        "schalter", "00000",                        #
        "manuell_reset", 0,                               # manueller Dosenstatus: 0= er bleibt für immer, 1= bis Mitternacht
        "reserve", 'reservedefault'                 #
        ]

#  Parameter für Config Read der Aktor-Klassen -------------------
#  Aktor Klasse Aktor

# ***** Variables *****************************
#   Struktur (Liste) der Daten, die aus dem Configfile swconfig.ini gelesen werden
#   hier die defaultwerte der 'variablen'
cfglist_akt=[
        "abschnitt", 'aktor_1',     
        "gpio_1" , 12,
        "gpio_2" , 19,
        "gpio_3" , 20,
        "gpio_4" , 21,
      

        "abschnitt", 'aktor_2',     
        "gpio_1" , 17,
        "repeat", 10,
        "codelength", 24,
        "send_dat_1_ein" , "66897,320,1",
        "send_dat_1_aus" , "66900,319,1",
        "send_dat_2_ein" , "69983,319,1",
        "send_dat_2_aus" , "69972,319,1",
        "send_dat_3_ein" , "70737,319,1",
        "send_dat_3_aus" , "70740,319,1",
        "send_dat_4_ein" , "70929,320,1",
        "send_dat_4_aus" , "70932,319,1",
   
        "abschnitt" , "aktor_3",
        "zurzeit_leer" , "",
 
        
        "abschnitt", 'aktor_4',     
        "gpio_1" , 4,
        "gpio_2" , 22,
        "gpio_3" , 18,
        "gpio_4" , 25,
        "gpio_5" , 23,
        "gpio_6" , 24,

        "abschnitt", 'aktor_5', 
        "gpio_send", 0,    
        "system_code" , '11101',
        "pfad_1" , '/home/pi/switcher2/' ,
              
        ] 
        
        #  Parameter für Config Read der Dosen-Klasse -------------------
#  Dosen Klasse

# ***** Variables *****************************
#   Struktur (Liste) der Daten, die aus dem Configfile swconfig.ini gelesen werden
#   hier die defaultwerte der 'variablen'
#
#   Achtung:
#   Schaltart 1 ist für Testumgebung. 
#   wenn eine dose 1 schaltart 1 hat, müssen die anderen Dosen auch schaltart 1 haben
#   script sorgt dafür (mit Warnung), dass dies eingehalten wird.
#   Amsonsten ist schaltart frei wählbar

cfglist_dos=[
        "abschnitt", 'dose', 
        "dose_1_schaltart" , 1,
        "dose_2_schaltart" , 1,
        "dose_3_schaltart" , 1,
        "dose_4_schaltart" , 1,
        "dose_5_schaltart" , 1,  
        "dose_6_schaltart" , 1,
#                                         
        "debug_schalt" , 1,
        ] 
        