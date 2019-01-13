
/* **************************************************************************
    Switcher 2  Temp Sensor Sketch fuer BME280
    mit Deep Sleep

    topic für switcher 2 wetter ist : 'switcher2/wetter/data'
    payload :   indoor/battstatus/sensorstatus/Elapsed/TEMP/HUM
    oder
    payload :   outdoor/battstatus/sensorstatus/Elapsed/TEMP/HUM

    Input pin 14 wird benutzt, um indoor oder outdoor zu setzen
    pin14 low:    outdoor
    pin14 high:   indoor

    Programmierung gemäss dieser Quelle im Netz
    https://github.com/z2amiller/sensorboard/blob/master/PowerSaving.md

    Also mit watchdog timer und wifi-Behandlung

    Debug-Output (auf Serial) mittels Preprocessor gemässe Adreas Spiess, siehe YouTube
    https://www.youtube.com/watch?v=1eL8dXL3Wow&t=513s
  
    Dazugehörige Library hier:
    https://youtu.be/1eL8dXL3Wow
    
    Weitere Inspiration zur Energiefrage;
    https://www.bakke.online/index.php/2017/05/21/reducing-wifi-power-consumption-on-esp8266-part-1/

    und auch vor allem von hier:
    https://blog.voneicken.com/2018/lp-wifi-esp8266-1/

    
    
    Battery Level:
    Entweder wird direkt VCC gemessen (wenn ein LiFePo4 direkt angeschlossen ist) 
    oder
    es wird die Batteriespannung mittels einem abschaltbaren Spannungsteiler gemessen. Dies ist bei LiPo
    Accus nötig, da dort ein Voltage Regulator nötig ist (wegen deren max. 4.2 Volt wenn voll geladen).

 
  Januar 2019, by Peter B.
 *************************************************************************************/

// defines für verschiedene Programm-Varianten

// zum inkludieren der richtigen Lib (ESP32 oder ESP8266)
// select ESP8266 or ESP32 mittels define
#define ESP8266
// #define LAST_WILL      // auskommentieren macht keinen MQTT LastWill
#define MQTT_AUTH         // auskommentieren wenn MQTT connect ohne userid/password 
#define DEBUGLEVEL 1      // für Debug Output, für Produktion DEBUGLEVEL 0 setzen !
#define HOSTNAME "mysensor"
#define STAIIC_IP
// ------------------------------------------------------
#define TICKER_TIME_MS     10000  // Zeit für Watchdog Interrrupt

#define   VCC_ADJ   0.975   // Korrekturfaktor bei VCC Messung (kalibriert mit Voltmeter)

// ---- includes -------------------------------------------
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <Ticker.h>
#include <PubSubClient.h>
#include <DebugUtils.h>     // Library von Adreas Spiess
#include <sw_credentials.h>    // eigene crendentials

// esp8266 oder esp32 ----------------------
#if defined ESP8266
  #include <ESP8266WiFi.h>
  const int indoor_outdoor_pin = 14;      // um indoor/outdoor festzustellen
  const int adc_switch_pin = 2;           // 1: spannungsteiler ein, 0: aus
#else
  #include <WiFi.h>
  const int indoor_outdoor_pin = 14;     // um indoor/outdoor festzustellen  
  const int ledpin = 27;      // not used
#endif

//Static IP address configuration
IPAddress staticIP  (192, 168, 1, 999); //ESP static ip
IPAddress gateway   (192, 168, 1, 1);   //IP Address of your WiFi Router (Gateway)
IPAddress subnet    (255, 255, 255, 0);  //Subnet mask
IPAddress dns    (8, 8, 8, 8);  //DNS

const int ipadr_indoor = 161;         // pos 3 der IPAdr, wird zur runtime gesetzt, 
const int ipadr_outdoor = 162;         // nachdem indoor oder outdoor bekannt ist

Ticker sleepTicker;
Adafruit_BME280 bme; // I2C
WiFiClient espClient;
PubSubClient client(espClient);


ADC_MODE(ADC_VCC);          // nötig bei VCC Messung


// Time to deepsleep (in seconds):
//const int sleepTimeS = 30;        // 40 ist etwa 30 Sec 
//const int sleepTimeS = 240;       // 240 ist etwa 4 Minuten
const int sleepTimeS = 2000;        // 240 ist etwa 33 Minuten

// werte kommen aus sw_credentials.h
const char* wifi_ssid =       WAN_SSID;
const char* wifi_password =   WAN_PW;
const char* user_id_mqtt =    MQTT_USER;
const char* password_mqtt =   MQTT_PW;


// IP Adresse des MQTT Brokers
const char* mqtt_server = "192.168.1.153";

//Variables Sensor
int       chk;
float     hum;                    //Stores humidity value
float     temp;                   //Stores temperature value
bool      sensor_status;          // status sensor true/false
long      previousMillis = 0;     // will store last tim
long      interval = 500;        // interval  (milliseconds)
unsigned long startTime;
unsigned long elapsed;
float     voltage_value_raw;      //Define variable to read ADC data
float     voltage_value;          //Define variable to read ADC data

char      battery_string[15];     // für Batterie Zustand
char      sensor_string[15];     // für Sensor Zustand
String    sens_status;    
long      lastMsg = 0;
char      msg[50];
int       value = 0;
String    batt_status;
char*     topic = "switcher2/wetter/data";
char*     topic_lw = "switcher2/wetter/lw";
int       inout_door ;       // HIGH: indoor, LOW: outdoor
String    last_will_msg = "Verbindung verloren zu Sensor: ";
String    the_sketchname;
unsigned long currentMillis;
bool      mqtt_status;
  
// The ESP8266 RTC memory is arranged into blocks of 4 bytes. The access methods read and write 4 bytes at a time,
// so the RTC data structure should be padded to a 4-byte multiple.
struct {
  uint32_t crc32;   // 4 bytes
  uint8_t channel;  // 1 byte,   5 in total
  uint8_t ap_mac[6]; // 6 bytes, 11 in total
  uint8_t padding;  // 1 byte,  12 in total
} rtcData;

// Function Prototypes -----------------------

uint32_t calculateCRC32(const uint8_t *data, size_t length);  // CRC function used to ensure data validity
void printMemory();                 // helper function to dump rtc memory contents as hex
void display_Running_Sketch ();     // anzeige der sketch info
void sleepyTime();                  // Watchdog IR Routine
String batt_voltage () ;            // Messung Batt Voltage
void readSensor ();                 // read sensor
void waitForWifi();                 // wait for Wifi
void setup_wifi();                  // setup wifi
void mqtt_connect();                   // connevt mqtt


//-------- Functions ----------------------------------------
// -------------------------------------
void setup() {

  
   String msg;
   char message[50];
   char elapsed_time[5];
   int ret;
   startTime = millis();   // Loop Begin Zeit

/*
  Use watchdog timers.
  Set a timer for the maximum amount of time your polling loop should run.
  This will prevent your device from sitting there for hours at a time with the WiFi 
  radio on trying to associte if your AP is down, for example. 
  The ESP8266 has a built-in Ticker that takes a timeout and a callback.
*/
  sleepTicker.once_ms (TICKER_TIME_MS, &sleepyTime);

  Serial.begin(115200);
  while (!Serial) { }
  DEBUGPRINTLN0 ("Starting Setup --------"); 
  display_Running_Sketch();
  DEBUGPRINT1 ("sleeptime: ");
  DEBUGPRINTLN1 (sleepTimeS);

  pinMode(indoor_outdoor_pin, INPUT_PULLUP);   // defines indoor-outdoor
  pinMode(adc_switch_pin, OUTPUT);      // Spannungsteiler ein/aus     
  digitalWrite(adc_switch_pin, LOW);    // Spannungsteiler aus
  
  inout_door = digitalRead  (indoor_outdoor_pin);
  if (inout_door == HIGH) {
     DEBUGPRINTLN1 ("Bin Indoor");
     last_will_msg = last_will_msg + "indoor"; 
  }
  else {
     DEBUGPRINTLN1 ("Bin Outdoor");
     last_will_msg = last_will_msg + "outdoor";
  }


  DEBUGPRINTLN1 ("\nMache WiFi Begin --------");
  // We start by connecting to a WiFi network
  DEBUGPRINT1 ("Connecting to: ");
  DEBUGPRINTLN1 (wifi_ssid);

// setzt static IP je nach indoor/outdoor
  if (inout_door == HIGH) {staticIP[3] = ipadr_indoor;}
  else {staticIP[3] = ipadr_outdoor;}
      
  WiFi.mode(WIFI_STA);
  WiFi.config( staticIP, gateway, subnet ,dns);  
  WiFi.begin( wifi_ssid, wifi_password ); 
  
  elapsed = millis() - startTime;  // Zeit Messung <------------------------------
  Serial.print("bis nach wifi setup msec: "); // time since program started
  Serial.println (elapsed);
    
  // default settings for bme280 I2C
  sensor_status = bme.begin();  
  if (!sensor_status) {
     DEBUGPRINTLN0 ("Could not find a valid BME280 sensor, check wiring!");
 //    while (1);        
   }

   if (sensor_status) {
    sens_status = "OK";
   }
   else
   {
    sens_status = "Fehler";
   }
    // sens_stat wird später im MQTT payload verwendet
    
   elapsed = millis() - startTime;  // Zeit Messung <------------------------------
   DEBUGPRINT1  ("Until setup done msec: "); // time since program started
   DEBUGPRINTLN1 (elapsed);
   DEBUGPRINTLN1 ("\nSetup Done...");

//---------------------------
// nun Sensor lesen, warten auf wiFi und dann MQTT

   readSensor ();
   batt_status = batt_voltage ();
   delay(10);
    
   waitForWifi();           // connect to WiFi

   elapsed = millis() - startTime;  // Zeit Messung <------------------------------
   DEBUGPRINT1  ("Until wifi da msec: "); // time since program started
   DEBUGPRINTLN1  (elapsed);
   mqtt_connect();             // connect to MQTT broker

    elapsed = millis() - startTime;  // Zeit Messung <------------------------------
    DEBUGPRINT1  ("Until mqtt connect msec: "); // time since program started
    DEBUGPRINTLN1 (elapsed);
    
    elapsed = (int)elapsed;
    sprintf(elapsed_time, "%5d", elapsed);
    
    if (inout_door == HIGH) {
      msg = msg + "indoor/";
    }
    else{
      msg = msg + "outdoor/";
    }
    msg = msg + batt_status;
    msg = msg + "/" + sens_status;
    msg = msg + "/" + elapsed_time;
    msg = msg + "/";
    msg = msg + temp;
    msg = msg + "/";
    msg = msg + hum;
  msg.toCharArray(message,50);
  
 //   publish sensor data to MQTT broker

    if (!mqtt_status)  {
     DEBUGPRINTLN1  ("Skip sending MQTT, no connection");       
    }
    else
    { 
      DEBUGPRINTLN1  ("Sending this message to MQTT Broker:");
      DEBUGPRINT1   ("topic:   ");
      DEBUGPRINTLN1  (topic);
      DEBUGPRINT1   ("payload: ");
      DEBUGPRINTLN1  (message);
      ret = client.publish (topic, message,1);            // QoS ist 1

      DEBUGPRINT1  ("mqtt publish returns: ");
      DEBUGPRINTLN1  (ret);
    
      currentMillis = millis();

      if(currentMillis - previousMillis > interval) {
    // save the last time 
        delay(1);
        previousMillis = currentMillis;   
        }

    }
    
   sleepyTime();
 
}


//------------------------------------------------
void loop() {
 
}

//------------------------------------------------
uint32_t calculateCRC32(const uint8_t *data, size_t length) {
  uint32_t crc = 0xffffffff;
  while (length--) {
    uint8_t c = *data++;
    for (uint32_t i = 0x80; i > 0; i >>= 1) {
      bool bit = crc & 0x80000000;
      if (c & i) {
        bit = !bit;
      }
      crc <<= 1;
      if (bit) {
        crc ^= 0x04c11db7;
      }
    }
  }
 //   DEBUGPRINT1  ("CRC: ");
 //   DEBUGPRINTLN1  (crc);
  return crc;
}
//---------------------------------------------
//prints all rtcData, including the leading crc32
void printMemory() {

   return;
  
  char buf[3];
  uint8_t *ptr = (uint8_t *)&rtcData;
  for (size_t i = 0; i < sizeof(rtcData); i++) {
    sprintf(buf, "%02X", ptr[i]);
    Serial.print(buf);
    if ((i + 1) % 32 == 0) {
      DEBUGPRINTLN1 ();
    } else {
      DEBUGPRINT1 (" ");
    }
  }
  DEBUGPRINTLN1 ();
}


//------------------------------------------------
// displays at startup the Sketch running in the Arduino
void display_Running_Sketch (void){
  String the_path = __FILE__;
  int slash_loc = the_path.lastIndexOf('/');
  String the_cpp_name = the_path.substring(slash_loc+1);
  int dot_loc = the_cpp_name.lastIndexOf('.');
//  String the_sketchname = the_cpp_name.substring(0, dot_loc);
  the_sketchname = the_cpp_name.substring(0, dot_loc);

  
  DEBUGPRINT1 ("\nRunning Sketch: ");
  DEBUGPRINTLN1 (the_sketchname);
  DEBUGPRINTLN1 ("Compiled on: ");
  DEBUGPRINT1 (__DATE__);
  DEBUGPRINT1 (" at ");
  DEBUGPRINT1 (__TIME__);
  DEBUGPRINT1 ("\n");
}

//-------------------------------------
void deepsleep() {
  
  DEBUGPRINTLN1 ("Going into deep sleep...");
  ESP.deepSleep(sleepTimeS * 1000000, WAKE_RF_DEFAULT);
  // It can take a while for the ESP to actually go to sleep.
  // When it wakes up we start again in setup().

// wird nie ausgeführt...
  DEBUGPRINTLN1 ("Nach deep sleep...");
  yield();

  
}
//--- Watchdog Interrupt Routine ---------------------------------------------
void sleepyTime() {
//  const int elapsed = millis() - startTime;
  elapsed = millis() - startTime;
  
  DEBUGPRINT1  ("\nsleepyTime, arbeit fertig in: ");
  DEBUGPRINT1  (elapsed);
  DEBUGPRINTLN1 (" ms\n");
  
  // Wenn Watchdog bellt, weill Operation zu lange dauerte
  // Clear Wifi state.
  yield();
  if (elapsed <= TICKER_TIME_MS) {
      DEBUGPRINTLN1 ("elapsed time kleiner Tickertime");
    }
  else {
      DEBUGPRINTLN1 ("Ticker interrupt");
      delay(1);
//    ESP.restart();
  
    if (WiFi.status() == WL_CONNECTED) {
      DEBUGPRINTLN1 ("WiFi disconnect..");
      WiFi.disconnect( true );
      delay( 1 );
      WiFi.mode( WIFI_OFF );
      currentMillis = millis();

      if(currentMillis - previousMillis > interval) {
    // save the last time 
        delay(1);
        previousMillis = currentMillis;   
      }
    }
    else {
       DEBUGPRINTLN1 ("WiFi not connected");
    }
   
   }
   
   deepsleep();

}

//------------------------------------------------
String batt_voltage () {
  
  String bat_str;
//  digitalWrite  (adc_switch_pin, HIGH);    // Spannungsteiler einschalten
  delay (100);

  voltage_value_raw = ESP.getVcc();
  voltage_value = (voltage_value_raw / 1024.0) * VCC_ADJ ;
//  voltage_value = analogRead(A0);       //Read ADC
 
  DEBUGPRINT1   ("ADC Value RAW: ");       //Print Message
  DEBUGPRINTLN1   (voltage_value_raw);             //Print ADC value
  DEBUGPRINT1   ("VCC: ");       //Print Message
  DEBUGPRINT1   (voltage_value);             //Print ADC value
  DEBUGPRINTLN1  (" Volt"); 
  delay(1);                             //

  dtostrf(voltage_value, 4, 2, battery_string);
  
//  digitalWrite(adc_switch_pin, LOW);    // Spannungsteiler ausschalten
    
  battery_string[4] = '\0';
  bat_str= String(battery_string);
    
  if (voltage_value > 3.0) {
    bat_str = bat_str + " - Perfekt";
    }
  else {
    if (voltage_value > 2.8) {
    bat_str = bat_str + " - Gut";
    }
    else
    {
     bat_str = bat_str + " - Achtung"; 
    }
  } 

 //  DEBUGPRINTLN1  (bat_str); 
      
  return (bat_str);
  
}

//------------------------------------------------
void readSensor () {

    if (!sensor_status) {
      DEBUGPRINT1 ("\n");
      DEBUGPRINTLN1 ("Sensorfehler, keine Messung ");
      temp = 11.1;
      hum  = 11.1;
      return;
    }
    
    DEBUGPRINT1 ("\n");
    DEBUGPRINTLN1 ("Messung: ");
    temp = bme.readTemperature();
    hum = bme.readHumidity();
    hum = round(hum*10) / 10.0;
    temp = round(temp*10) / 10.0;
    DEBUGPRINT1  ("Temperature = ");
    DEBUGPRINT1 (temp);
    DEBUGPRINTLN1 (" *C");

    DEBUGPRINT1 ("Humidity = ");
    DEBUGPRINT1 (hum);
    DEBUGPRINTLN1 (" %");

}

//------------------------------------------------
void waitForWifi() {
  DEBUGPRINT1 ("\n");
  DEBUGPRINTLN1 ("Wait for WiFi.");

int retries = 0;
int wifi_status = WiFi.status();

  delay (300);        // inital delay, weniger als 300 dauert es sowieso nicht...

  while( wifi_status != WL_CONNECTED ) {
  retries++;
   
    if  ( retries == 150 ) {
    // Maybe Quick connect is not working, reset WiFi and try regular connection
      DEBUGPRINTLN1 ("Nach 150 Versuchen");
      DEBUGPRINT1 ("WiFi Status");
      DEBUGPRINTLN1 (wifi_status);
      WiFi.disconnect();
      delay( 10 );
      WiFi.forceSleepBegin();
      delay( 10 );
      WiFi.forceSleepWake();
      delay( 10 );
      WiFi.config( staticIP, gateway, subnet ,dns);  
      WiFi.begin( wifi_ssid, wifi_password );
      yield();
    }
    if  ( retries == 250 ) {
    // Giving up after 30 seconds and going back to sleep
      DEBUGPRINTLN1 ("Nach 250 Versuchen");
      WiFi.disconnect( true );
      delay( 1 );
      WiFi.mode( WIFI_OFF );
      yield();
      deepsleep();
    }
                    // warten bis zum nächsten check
  delay(20);        // kleine granularität für schnelleres recovery
  yield();
  wifi_status = WiFi.status();    // check again
  }

// we are connected ...
  DEBUGPRINT1  ("Connected to:");
  DEBUGPRINTLN1 ( wifi_ssid);
  DEBUGPRINT1  ("IP address: ");
  DEBUGPRINTLN1  (WiFi.localIP());
  DEBUGPRINT1  ("Anz retries: ");
  DEBUGPRINTLN1  (retries);
  DEBUGPRINTLN1  ("\nWiFi Details:");
  WiFi.printDiag(Serial);

}


//------------------------------------------------
void mqtt_connect() {
  // Verbindung zum MQTT Broker
  // Mache 2 Versuche zu verbinden

  mqtt_status = false;
  for (int i=0; i < 2; i++) {

    DEBUGPRINT1 ("\nAttempting MQTT connection...Client-ID: ");
    client.setServer(mqtt_server, 1883);
    // Create a random client ID
    String clientId = the_sketchname;
    clientId += String(random(0xffff), HEX);
    DEBUGPRINTLN1 (clientId);

    char last_will[45];
    last_will_msg.toCharArray(last_will,45);

#if defined LAST_WILL
// connect mit Angabe eines last will
   if (client.connect(clientId.c_str(), user_id_mqtt,password_mqtt, topic_lw ,0 , false,last_will))
#else
 // connect OHNE Angabe eines last will
     if (client.connect(clientId.c_str(), user_id_mqtt,password_mqtt ))

#endif
    if (client.connected()) {
      DEBUGPRINTLN1  ("MQTT connected");
      mqtt_status = true;
      break;
       }
    
     DEBUGPRINT1 ("MQTT connect failed, rc=");
     DEBUGPRINT1 (client.state());
     DEBUGPRINTLN1 (" try again in 1 second");
    // Wait  1 seconds before retrying
     currentMillis = millis();
    if(currentMillis - previousMillis > interval * 2) {
    // save the last time 
      delay(1);
      previousMillis = currentMillis;   
      }
  }
} //end mqtt_connect()
//------------------------------------------------



//---------------------------------------------
