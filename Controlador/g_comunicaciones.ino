void suscribirseATopics() 
{
  mqtt_subscribe(TEMP_TOPIC);
}

void alRecibirMensajePorTopic(char* topic, String incomingMessage) 
{
  info("Mensaje recibido en topic: ");
  infoln(topic);

  info("Mensaje recibido: ");
  infoln(incomingMessage);

  if (strcmp(topic, TEMP_TOPIC) == 0) 
  {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, incomingMessage);

    if (err) {
      warn(F("Error JSON: "));
      warnln(err.f_str());
      return;
    }

    float temperatura = doc["temperatura"];

    info("Temperatura recibida: ");
    infoln(temperatura);

    procesarTemperatura(temperatura);
  }
}

void enviarMensajePorTopic(const char* topic, String outgoingMessage) 
{
  mqtt_publish(topic, outgoingMessage.c_str());
}