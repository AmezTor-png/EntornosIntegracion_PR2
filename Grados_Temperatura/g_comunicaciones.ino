void suscribirseATopics() 
{
  // Esta ESP32 solo publica temperatura.
  // No necesita suscribirse a LED, motor ni LDR.
  mqtt_subscribe(HELLO_TOPIC);
  mqtt_subscribe(LED_ACTION_TOPIC);
}

void alRecibirMensajePorTopic(char* topic, String incomingMessage) 
{
  info("Mensaje recibido en topic: ");
  infoln(topic);

  info("Mensaje recibido: ");
  infoln(incomingMessage);
  
  if (strcmp(topic, LED_ACTION_TOPIC) == 0)
  {
    if (incomingMessage == "ON")
    {
      digitalWrite(LED_PIN, HIGH);
      infoln("LED externo encendido");
    }
    else if (incomingMessage == "OFF")
    {
      digitalWrite(LED_PIN, LOW);
      infoln("LED externo apagado");
    }
    else
    {
      warnln("Comando LED no reconocido");
    }
  }

  // De momento no hacemos nada al recibir mensajes.
  // Esta placa solo actúa como sensor de temperatura NTC.
}

void enviarMensajePorTopic(const char* topic, String outgoingMessage) 
{
  mqtt_publish(topic, outgoingMessage.c_str());
}