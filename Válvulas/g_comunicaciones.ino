void suscribirseATopics()
{  
  mqtt_subscribe(SCARA_R_POSICIONES_TOPIC);

  Serial.println("Suscrito a topics correctamente.");
}

void alRecibirMensajePorTopic(char* topic, String incomingMessage)
{
  info("Topic recibido: ");
  infoln(topic);

  info("Mensaje recibido: ");
  infoln(incomingMessage);

  if (strcmp(topic, SCARA_R_POSICIONES_TOPIC) == 0)
  {
    procesarOrdenScara(incomingMessage);
    return;
  }

  warn("Topic no gestionado: ");
  warnln(topic);
}

void enviarMensajePorTopic(const char* topic, String outgoingMessage)
{
  mqtt_publish(topic, outgoingMessage.c_str());
}