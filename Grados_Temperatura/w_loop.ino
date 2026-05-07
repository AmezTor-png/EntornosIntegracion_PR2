#define TEMP_LIMITE_ON  30.0
#define TEMP_LIMITE_OFF 29.0

long now;
long lastTempMsg = 0;
bool ledAutoEstado = false;

void on_loop() 
{
  now = millis();

  if (now - lastTempMsg > TEMP_REPORT_INTERVAL) 
  {
    lastTempMsg = now;

    float temperatura = leerTemperaturaNTC();

    if (temperatura == -999.0) return;

    // Control local con histéresis
    if (!ledAutoEstado && temperatura >= TEMP_LIMITE_ON) {
      ledAutoEstado = true;
      digitalWrite(LED_PIN, HIGH);
      enviarMensajePorTopic(LED_ACTION_TOPIC, "ON");
    }
    else if (ledAutoEstado && temperatura <= TEMP_LIMITE_OFF) {
      ledAutoEstado = false;
      digitalWrite(LED_PIN, LOW);
      enviarMensajePorTopic(LED_ACTION_TOPIC, "OFF");
    }

    JsonDocument doc;
    doc["temperatura"] = temperatura;
    doc["led"] = ledAutoEstado ? "ON" : "OFF";

    String mensajeJson;
    serializeJson(doc, mensajeJson);

    enviarMensajePorTopic(TEMP_TOPIC, mensajeJson);
  }
}