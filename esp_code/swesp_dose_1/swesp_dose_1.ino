/* --------------------------------------------------
    Switcher2 Dosentest Smart Switch
           
    for proof of concept Switcher 2 MQTT
    schaltet led ein und aus je nach empfangenre payload

    Pin 12/14 werden für Dosen-Select verwendet

    0/0  -> Dose 1
    0/1  -> Dose 1
    1/0  -> Dose 3
    1/1  -> Dose 4
    
    Pin 13 hat LED, welche Dose simuliert

    Script subskribiert Topic switcher2 

    kann als Beispiel für eigene Weuterentwicklung dienen.
    Ideen von hier (mit Dank)
    http://esp8266-server.de/EEPROM.html

    Peter K. Boxler, September 2018
/* --------------------------------------------------*/

#define ESP8266

/* select ESP8266 or ESP32 mittels define */

#if defined ESP8266
#include <ESP8266WiFi.h>
const int led = 13;   // use 13 für Huzzah 6288 
const int pin1 = 12;   // Dosenselect 1          
const int pin2 = 14;   // Dosenselect 2   
#else
#include <WiFi.h>
const int led = 13;   // andere Werte für esp32 ! 
const int pin1 = 12;   // Dosenselect 1          
const int pin2 = 14;   // Dosenselect 2   
#endif

#include <PubSubClient.h>
#include <EEPROM.h>

/* diese Werte anpassen   <<--------- */
const char* ssid = "P-NETGEAR";           // WLAN SSID
const char* password = "hermannelsa";    // WLAN Passwort
const char* ip_adr_broker = "192.168.1.145";
/* diese Werte anpassen   <<--------- */


const char* user_id="admin";            // falls mqtt Broker anmeldung verlangt    
const char* password_mqtt="tabstop";



int stat_pin1;
int stat_pin2;
int dosennummer;
long time_lastMsg = 0;

// IP-Adr des MQTT Brokers  
const char* mqtt_server = ip_adr_broker;        // IP-AD MQTT Broker

WiFiClient espClient;
PubSubClient client(espClient);

char msg[50];
int value = 0;

struct Dose_struct {
  unsigned long id;
  int dosennummer;
  int einaus;
};
int nekst_free;
String the_sketchname;

//------------------------------------------------
// displays at startup the Sketch running in the Arduino
void display_Running_Sketch (void){
  String the_path = __FILE__;
  int slash_loc = the_path.lastIndexOf('/');
  String the_cpp_name = the_path.substring(slash_loc+1);
  int dot_loc = the_cpp_name.lastIndexOf('.');
  the_sketchname = the_cpp_name.substring(0, dot_loc);

  Serial.print("\nRunning Sketch: ");
  Serial.println(the_sketchname);
  Serial.print("Compiled on: ");
  Serial.print(__DATE__);
  Serial.print(" at ");
  Serial.print(__TIME__);
  Serial.print("\n");
}


//------------------------------------------------ 
// Write any data structure or variable to EEPROM
int EEPROMAnythingWrite(int pos, char *zeichen, int lenge)
{
  for (int i = 0; i < lenge; i++)
  {
    EEPROM.write(pos + i, *zeichen);
    zeichen++;
  }
  return pos + lenge;
}

 //------------------------------------------------
// Read any data structure or variable from EEPROM
int EEPROMAnythingRead(int pos, char *zeichen, int lenge)
{
  for (int i = 0; i < lenge; i++)
  {
    *zeichen = EEPROM.read(pos + i);
    zeichen++;
  }
  return pos + lenge;
}

//------------------------------------------------
void setup_wifi() {
   delay(100);

    Serial.println("Conneting to WiFi --------");
  // We start by connecting to a WiFi network
    Serial.print("Connecting to ");
    Serial.println(ssid);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) 
    {
      delay(500);
      Serial.print(".");
    }
  randomSeed(micros());
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
   
  Serial.println("Done Conneting to WiFi --------");
  
}
//------------------------------------------------

void schalten (unsigned int dos, unsigned int how)
{
  Dose_struct dose;
  Dose_struct dose2;
// feststellen, ob Meldung für mich ist (Dose)
 if (dos != dosennummer) 
    {
      Serial.println("Nicht für mich !");
      return;
    }
     Serial.println("Oh, ist ja für mich !");
   // Led ein oder ausschalten
 switch (how)
 { 
  
  case 0:
    digitalWrite(led, LOW); 
    Serial.println("Muss Led ausschalten");
    break;
  
  case 1:
    digitalWrite(led, HIGH);   // LED on
    Serial.println("Muss Led einschalten");
    // Store structure (struct) to EEPROM 
    break;
    
  default:
    Serial.println("Error: Ist weder ein noch aus");
   // nothing to do
  break;
  
 } 
  Serial.println("Schreibe Zustand nach EEProm");
    dose.id=123456;
    dose.dosennummer = dosennummer;
    dose.einaus=how;
    nekst_free =  EEPROMAnythingWrite(100, reinterpret_cast<char*>(&dose), sizeof(dose)); 

  EEPROM.commit();
  
  Serial.println("Check Read struct dose");
  // Read structure (struct) from EEPROM
  nekst_free = EEPROMAnythingRead(100, reinterpret_cast<char*>(&dose2), sizeof(dose2));
  Serial.println("DoseID = " + String (dose2.id) + " Dosennumer = " + String(dose2.dosennummer) +  " , einaus = " + String(dose2.einaus));
  Serial.println("");
    
}
//------------------------------------------------
void callback(char* topic, byte* payload, unsigned int length) 
{
  static char input[3];
  int p;
  int dosein;
  int einaus;
  
  
  Serial.println  ("Message eingetroffen-------------");
  Serial.print    ("Topic ist : [");
  Serial.print    (topic);
  Serial.println  ("]");
  Serial.print    ("Payload Länge ist: ");
  Serial.println  (length);

  
  switch (length)
  {
  case 0: 
    Serial.println("No payload, lenght is null");
    break;
  
  case 3:                   // so muss es sein
  case 4:
    input[0]=payload[0];
    input[1] = '\0';        // gültigen C string erstellen
    dosein = atoi( input );
    Serial.print    ("Betrifft Dose: ");
    Serial.println  (dosein);

    input[0]=payload[1];
    input[1]=payload[2];
    input[2] = '\0';
    if (input[1] == 'F') { einaus = 0;}
    else {einaus=1;}
    
 
    Serial.print  ("Ein oder Aus: ");
    Serial.println(einaus);
    break;
    
   default:
   Serial.print("ERROR,Länge Payload: ");
   Serial.println(length);
   return;
  }
 

    schalten(dosein,einaus);
  
  Serial.println();
} //end callback
//------------------------------------------------


//------------------------------------------------
void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) 
  {
     Serial.print("Attempting MQTT connection...Client-ID: ");
    client.setServer(mqtt_server, 1883);
    // Create a random client ID
    String clientId = the_sketchname;
    clientId += String(random(0xffff), HEX);
    Serial.println (clientId);
    // Attempt to connect
    //if you MQTT broker has clientID,username and password
    //please change following line to    if (client.connect(clientId,userName,passWord))
//	if (client.connect("peter01",user_id,password_mqtt)) //put your clientId/userName/passWord here

    if (client.connect(clientId.c_str()))
    {
      Serial.println("connected to broker");
     //once connected to MQTT broker, subscribe command if any
      client.subscribe("switcher2/out");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      Serial.println("Ist IP-Adr des brokers richtig ?");
      // Wait 6 seconds before retrying
      delay(6000);
    }
  }
} //end reconnect()
//------------------------------------------------

void setup() {

  Dose_struct dose2;

  Serial.begin(115200);
  delay(3000);
    EEPROM.begin(255);
   Serial.println();
  Serial.println("Starting Setup --------");
   display_Running_Sketch();
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  pinMode(led, OUTPUT);
  pinMode(pin1, INPUT);
  pinMode(pin2, INPUT);
  
  stat_pin1 = digitalRead(pin1);
  stat_pin2 = digitalRead(pin2);
  digitalWrite(led, LOW);         // led aus bei start
 

  if (stat_pin1 == LOW and stat_pin2 == LOW)
    dosennummer = 1;
  if (stat_pin1 == LOW and stat_pin2 == HIGH)
    dosennummer = 2;
  if (stat_pin1 == HIGH and stat_pin2 == LOW)
    dosennummer = 3;
   if (stat_pin1 == HIGH and stat_pin2 == HIGH)
    dosennummer = 4;
   Serial.print ("Ich bin Dose: ");
   Serial.println (dosennummer);

   Serial.println("Read struct dose");
  // Read structure (struct) from EEPROM
  nekst_free = EEPROMAnythingRead(100, reinterpret_cast<char*>(&dose2), sizeof(dose2));
  Serial.println("DoseID = " + String (dose2.id) + " Dosennumer = " + String(dose2.dosennummer) +  " , einaus = " + String(dose2.einaus));
   if (dose2.id != 123456) {
    Serial.println("id nicht passend, also nichts machen");
    }
  else {
    Serial.println("alte Werte gefunden, also entsprechend schalten");
    schalten(dose2.dosennummer,dose2.einaus);
    
  }
   
   Serial.println("Done Setup --------");
}

//------------------------------------------------
void loop() {
  if (!client.connected()) {
    reconnect();
    }
  client.loop();

  long now = millis();
  
  if (now - time_lastMsg > 24000) {
  	Serial.println("keep myself busy...");
     time_lastMsg = now;
 
     String msg="bin immer noch da...";
     char topic[20];
     sprintf(topic,"switcher2/in/dose%d",dosennummer);

     
     char message[40];
     msg.toCharArray(message,40);
     Serial.println("Sende dies zum MQTT Broker:");
     Serial.print(topic);
     Serial.print(" ");
     Serial.println(message);
     //publish sensor data to MQTT broker
      client.publish(topic, message);
  }
}

/* ---------------------------------------------*/

