
/* --------------------------------------------------
    Switcher 2  Temp Sensor Sketch fuer DHT22

    topic für switcher 2 wetter ist : 'switcher2/in/wetter'
    payload :   indoor/23.5/56.5/1
    oder
    payload :   outdoor/23.5/56.5/1

    Input pin 14 wird benutzt, um indoor oder outdoor zu setzen
    pin14 low:    outdoor
    pin14 high:   indoor

    Sensor Lesen:
    Es wird eine spezielle Library benutzt, um den Sensor auszulesen. Die normalerweise verwendete Lib
    DHT.h macht Probleme bei der schnellen CPU im ESP32. Es wird daher die Lib dhtnew.h vewendet.
    Die Dateien dhtnew.cpp und dhtnew.h wurden in den Arduino Lib Ordner gespeichert, im Folder dhtnew
    
    Details siehe hier:
      https://forum.arduino.cc/index.php?topic=521494.0
      https://github.com/RobTillaart/Arduino/tree/master/libraries/DHTNEW

    Battery Level:
    In der Payload ist ein Flag vorgesehen, der den Batterie-Zustand meldet: 1=ok, 0=schwach.
    Zur Zeit (okt.2018) ist dies jedoch noch nicht implementiert.

    
  Oktober 2018, by Peter B.
 */
 

#define ESP32

/* select ESP8266 or ESP32 mittels define */

#if defined ESP8266
#include <ESP8266WiFi.h>
const int DHTPin = 33;   
const int testpin = 14;
const int ledpin = 27;
#else
#include <WiFi.h>
// DHT Sensor
const int DHTPin = 33;   
const int testpin = 14;
const int ledpin = 27;
#endif

#include <dhtnew.h>         // read sensor lib
#include <PubSubClient.h>

#define WAN_SSID "P-NETGEAR"
#define WAN_PW  "hermannelsa"

const char* ssid = WAN_SSID;
const char* password =  WAN_PW;
const char* user_id="switcher2";
const char* password_mqtt =  "itscool";

#define DHTTYPE DHT22       // DHT 22 (AM2302), AM2321


// Initialize DHT sensor.
DHTNEW mySensor(DHTPin);


// Update these with values suitable for your network.
const char* mqtt_server = "192.168.1.145";

//Variables Sensor
int chk;
float hum;  //Stores humidity value
float temp; //Stores temperature value

WiFiClient espClient;
PubSubClient client(espClient);
long lastMsg = 0;
char msg[50];
int value = 0;
char* topic = "switcher2/wetter/data";
char* topic_lw = "switcher2/wetter/lw";
int led_status;
int  inout_door ;
String last_will_msg = "Verbindung verloren zu Sensor: ";
String the_sketchname;

//------------------------------------------------
// displays at startup the Sketch running in the Arduino
void display_Running_Sketch (void){
  String the_path = __FILE__;
  int slash_loc = the_path.lastIndexOf('/');
  String the_cpp_name = the_path.substring(slash_loc+1);
  int dot_loc = the_cpp_name.lastIndexOf('.');
//  String the_sketchname = the_cpp_name.substring(0, dot_loc);
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
void test()
{
  // READ DATA
  uint32_t start = micros();
  int chk = mySensor.read();
  uint32_t stop = micros();

  switch (chk)
  {
    case DHTLIB_OK:
      Serial.print("OK,\t");
      break;
    case DHTLIB_ERROR_CHECKSUM:
      Serial.print("Checksum error,\t");
      break;
    case DHTLIB_ERROR_TIMEOUT:
      Serial.print("Time out error,\t");
      break;
    default:
      Serial.print("Unknown error,\t");
      break;
  }
  
  // DISPLAY DATA
  Serial.print(mySensor.humidity, 1);
  Serial.print(",\t");
  Serial.print(mySensor.temperature, 1);
  Serial.print(",\t");
  uint32_t duration = stop - start;
  Serial.print(duration);
  Serial.print(",\t");
  Serial.println(mySensor.getType());
  delay(500);
}

//------------------------------------------------


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

// -------------------------------------
void setup() {

  Serial.begin(115200);
 delay(3000);
   display_Running_Sketch();
   Serial.println();
  Serial.println("Starting Setup --------");
  pinMode(ledpin, OUTPUT);  
  pinMode(testpin, INPUT);  
  digitalWrite(ledpin, HIGH);   // LED on
   delay(500);
  digitalWrite(ledpin, LOW);   // LED on
  inout_door = digitalRead(testpin);
  if (inout_door == HIGH) {
      Serial.println("Bin Indoor");
      last_will_msg = last_will_msg + "indoor";
      
  }
  else {
          Serial.println("Bin Outdoor");
          last_will_msg = last_will_msg + "outdoor";
    }
    
    setup_wifi();

    test(); 
    mySensor.setHumOffset(0);
    test();
    mySensor.setTempOffset(0);
    test();

 

  Serial.println("\nSetup Done...");

}

//------------------------------------------------
void callback(char* topic, byte* payload, unsigned int length) 
{
  static char input[3];
  int p;
  Serial.println("Callback called-------------");
  Serial.print("Command is : [");
  Serial.print(topic);
  Serial.println("]");
 

  switch (length)
  {
  case 0: 
    Serial.println("No payload, lenght is null");
    break;
  case 1:
    p =(char)payload[0]-'0';
    break;
  case 2:
    input[0]=(char)payload[0];
    input[1]=(char)payload[1];
    input[2] = '\0';
    p = atoi( input );
    break;
   default:
   Serial.print("ERROR,length payload: ");
   Serial.println(length);
   p=99;  // error value
  }
    Serial.print("Payload is : [");
    Serial.print(p);
   Serial.println("]");
   
 // Bemerkung:
 // single char convert to int   int someInt = someChar - '0';
 //-------------

 switch (p)
 { 
  
  case 0:
    digitalWrite(ledpin, LOW);   // Turn the LED on (Note that LOW is the voltage level
    Serial.println("Message received to turn off led");
    break;
  
  case 1:
    digitalWrite(ledpin, HIGH);   // LED on
    Serial.println("Message received to turn on led");
   
  break;
  case 23:
    Serial.println("tue etwas anderes.....");
  default:
   
    // nothing to do
  break;
 }  
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

//  if (client.connect("peter01",user_id,password_mqtt)) //put your clientId/userName/passWord here
//  if (client.connect(clientId.c_str(), topic_lw ,0 , false,last_will))

    char last_will[45];
    last_will_msg.toCharArray(last_will,45);

// connect mit Angabe eines last will
   if (client.connect(clientId.c_str(), user_id,password_mqtt, topic_lw ,0 , false,last_will))
  
    {
      Serial.println("connected");
     //once connected to MQTT broker, subscribe command if any
      client.subscribe("inTopic");
      client.setCallback(callback);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 6 seconds before retrying
      delay(6000);
    }
  }
} //end reconnect()
//------------------------------------------------

void loop() {

   if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  long now = millis();
  // read DHT22 sensor every 6 seconds
    if (now - lastMsg > 9000) {
    lastMsg = now;
    
    mySensor.read();

    hum = mySensor.humidity;
    temp = mySensor.temperature;
    Serial.print ("Read: ");
    Serial.print(temp, 1);
    Serial.print(",\t");
    Serial.println(hum, 1);
    delay(250);
    
    led_status = digitalRead(ledpin);
    String msg;

    if (inout_door == HIGH) {
      msg = msg + "indoor/";
    }
    else{
      msg = msg + "outdoor/";
    }
    msg = msg + temp;
    msg = msg + "/";
    msg = msg + hum;
    if (led_status == 1) { msg = msg + "/" + "1"; }
    else { msg = msg + "/" + "0" ; }

  
    char message[25];

    
    msg.toCharArray(message,25);
 
 //   publish sensor data to MQTT broker
  
    Serial.println("Sending this message to MQTT Broker:");
    Serial.println (topic);
    Serial.println (message);
    client.publish (topic, message,1);            // QoS ist 1
   
    }  
}
