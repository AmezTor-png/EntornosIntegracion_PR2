bool ledEncendido = false;
bool ordenRobotEnviada = false;

#define TEMP_ON  30.0
#define TEMP_OFF 29.0

void procesarTemperatura(float temperatura)
{
  info("Procesando temperatura: ");
  infoln(temperatura);


  if (!ledEncendido && temperatura >= TEMP_ON)
  {
    ledEncendido = true;

    infoln("Enviando LED ON");
    enviarMensajePorTopic(LED_ACTION_TOPIC, "ON");

    // 👉 NUEVO: ordenar al robot sacar gradilla
    if (!ordenRobotEnviada)
    {
      infoln("Enviando orden al robot: SACAR_GRADILLA");
      enviarMensajePorTopic("giirob/pr2/station/demo/commands", "SACAR_GRADILLA");
      ordenRobotEnviada = true;
    }
  }

  else if (ledEncendido && temperatura <= TEMP_OFF)
  {
    ledEncendido = false;

    infoln("Enviando LED OFF");
    enviarMensajePorTopic(LED_ACTION_TOPIC, "OFF");

    // 👉 reset para siguiente ciclo
    ordenRobotEnviada = false;
  }
}