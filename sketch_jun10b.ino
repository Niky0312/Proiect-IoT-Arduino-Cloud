#include <EEPROM.h>


const int pinLED = 3;
const int pinLM35 = A0;
const int pinApa = A1;


const int PRAG_INUNDATIE = 400; 


const int ADRESA_START_MESAJE = 0;

const int ADRESA_START_INUNDATII = 200; 

int indexMesajCurent = 0; 
int indexInundatieCurent = 0;
bool stareInundatieAnterioara = false;

void setup() {
  Serial.begin(9600);
  pinMode(pinLED, OUTPUT);
  digitalWrite(pinLED, LOW);
  
  
  indexMesajCurent = EEPROM.read(500) % 10;
  indexInundatieCurent = EEPROM.read(501) % 10;
}

void loop() {
  
  int valoareLM35 = analogRead(pinLM35);
  float tensiune = valoareLM35 * (5.0 / 1023.0);
  float temperatura = tensiune * 100.0;

  
  int nivelApa = analogRead(pinApa);
  bool esteInundatie = (nivelApa > PRAG_INUNDATIE);

  
  Serial.print("DATA: Temp=");
  Serial.print(temperatura);
  Serial.print("|Apa=");
  Serial.print(nivelApa);
  Serial.print("|Inundatie=");
  Serial.println(esteInundatie ? "DA" : "NU");

  
  if (esteInundatie && !stareInundatieAnterioara) {
    salveazaEvenimentInundatie(nivelApa);
    Serial.println("ALERT:InundatieDetectata!");
  }
  stareInundatieAnterioara = esteInundatie;

  
  if (Serial.available() > 0) {
    String comanda = Serial.readStringUntil('\n');
    comanda.trim();

    if (comanda == "A") {
      digitalWrite(pinLED, HIGH);
      Serial.println("STATUS:LED_Aprins");
    } 
    else if (comanda == "S") {
      digitalWrite(pinLED, LOW);
      Serial.println("STATUS:LED_Stins");
    } 
    
    else if (comanda.startsWith("MSG:")) {
      String mesajDeSalvat = comanda.substring(4);
      salveazaMesajEEPROM(mesajDeSalvat);
      Serial.println("STATUS:MesajSalvat");
    }
  }

  delay(2000); 
}


void salveazaMesajEEPROM(String msg) {
  int adresa = ADRESA_START_MESAJE + (indexMesajCurent * 20);
  
  
  if(msg.length() > 19) msg = msg.substring(0, 19);
  
  for (int i = 0; i < msg.length(); i++) {
    EEPROM.write(adresa + i, msg[i]);
  }
  EEPROM.write(adresa + msg.length(), '\0'); 

  indexMesajCurent = (indexMesajCurent + 1) % 10;
  EEPROM.write(500, indexMesajCurent); 
}


void salveazaEvenimentInundatie(int valoare) {
  int adresa = ADRESA_START_INUNDATII + (indexInundatieCurent * 2);
  
  
  EEPROM.write(adresa, highByte(valoare));
  EEPROM.write(adresa + 1, lowByte(valoare));

  indexInundatieCurent = (indexInundatieCurent + 1) % 10;
  EEPROM.write(501, indexInundatieCurent); 
}