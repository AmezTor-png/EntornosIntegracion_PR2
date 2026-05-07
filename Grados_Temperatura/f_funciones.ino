#include <math.h>

uint8_t ledStatus = 0;


void setInternalLed(uint8_t status) 
{
  if (ledStatus == status)
    return;
    
  ledStatus = status;

  if (status) {
    infoln("Led interno: ON");
    digitalWrite(LED_BUILTIN, HIGH);
  } else {
    infoln("Led interno: OFF");
    digitalWrite(LED_BUILTIN, LOW);
  }
}


void setExternalLed(uint8_t status)
{
  if (status) {
    infoln("Led externo: ON");
    digitalWrite(LED_PIN, HIGH);
  } else {
    infoln("Led externo: OFF");
    digitalWrite(LED_PIN, LOW);
  }
}

float leerTemperaturaNTC()
{
  int adc = analogRead(TEMP_PIN);
  float Vout = adc * (3.3 / 4095.0);

  float R1 = 10000.0;
  float Beta = 3950.0;
  float To = 298.15;
  float Ro = 10000.0;

  if (Vout <= 0.01 || Vout >= 3.29) {
    return -999.0;
  }

  float Rntc = R1 * (Vout / (3.3 - Vout));
  float tempK = 1.0 / ((1.0 / To) + (1.0 / Beta) * log(Rntc / Ro));
  return tempK - 273.15;
}

  