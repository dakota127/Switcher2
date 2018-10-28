# Switcher2
Version 2 of 'Switch Lights When Not at Home' with Raspberry Pi
This is a much extended version of the old switcher that was published in 2015. It acts as a IoT Gateway.

This documentation describes a Raspberry Pi gadget that is used to switch lights or other appliances on/off when not at home. 
Up to 4 power outlets are supported, mutiple on/off sequences for every switch per day are possible. Switcher 2 supports the older 433Mhz outlets 
as well as the more modern Wi-Fi enabled outlets (Smart Switches) used in Smart Home applications. 
The sequence is repeated every week. Switching times (ON/OFF) for every power outlet are defined in 3 XML files. 
This version 2 of the Switcher supports 3 seasons and switches unattended to another season if needed.  
XML files are parsed at start time. A external toggle-switch known as the ‚At Home switch‘ 
is used to stop switching lights when at home. Manual switching of outlets is also supported
thereby overriding and suppressing the automated switching.
A Flask-based webserver allows remote control of switcher2 with responsive webdesign.
All Code in Python. New Version uses Python logging with RotatingFileHandler.

Documentation and code on GitHub. 
Documentation (pdf, >35 pages in Docu folder) is in German, with English Abstract.  

Free to use, modify, and distribute with proper attribution.
Frei für jedermann, vollständige Quellangabe vorausgesetzt.

