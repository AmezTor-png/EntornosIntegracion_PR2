void apagarTodasLasSustancias()
{
  digitalWrite(SUSTANCIA_A, LOW);
  digitalWrite(SUSTANCIA_B, LOW);
  digitalWrite(SUSTANCIA_C, LOW);

  info("Todas las sustancias apagadas");
}

void encenderSustancia(int sustancia)
{
  if (sustancia == 1)
  {
    digitalWrite(SUSTANCIA_A, HIGH);
    info("Sustancia 1 encendida");
  }
  else if (sustancia == 2)
  {
    digitalWrite(SUSTANCIA_B, HIGH);
    info("Sustancia 2 encendida");
  }
  else if (sustancia == 3)
  {
    digitalWrite(SUSTANCIA_C, HIGH);
    info("Sustancia 3 encendida");
  }
  else
  {
    warn("Sustancia no valida: ");
    warnln(sustancia);
  }
}

void publicarAckSustancia(String posicion, int sustancia)
{
  JsonDocument respuesta;
  respuesta["posicion"] = posicion;
  respuesta["sustancia"] = sustancia;
  respuesta["estado"] = "ok";

  String mensaje;
  serializeJson(respuesta, mensaje);

  enviarMensajePorTopic(SCARA_ESTADO_TOPIC, mensaje);

  info("ACK sustancia enviado: ");
  infoln(mensaje);
}

void publicarFinPosicion(String posicion)
{
  JsonDocument respuesta;
  respuesta["posicion"] = posicion;
  respuesta["estado"] = "listo";

  String mensaje;
  serializeJson(respuesta, mensaje);

  enviarMensajePorTopic(SCARA_ESTADO_TOPIC, mensaje);

  info("Fin posicion enviado: ");
  infoln(mensaje);
}

void procesarOrdenScara(String incomingMessage)
{
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, incomingMessage);

  if (err)
  {
    warn(F("deserializeJson() returned "));
    warnln(err.f_str());
    return;
  }

  String posicion = doc["posicion"] | "";
  String estado = doc["estado"] | "";
  int sustancia = doc["sustancia"] | 0;
  int led = doc["led"] | sustancia;

  info("Orden SCARA recibida. Posicion: ");
  infoln(posicion);

  info("Estado: ");
  infoln(estado);

  info("Sustancia/LED: ");
  infoln(led);

  if (estado == "reset")
  {
    apagarTodasLasSustancias();
    return;
  }

  if (estado == "inyectada")
  {
    encenderSustancia(led);
    publicarAckSustancia(posicion, led);
    return;
  }

  if (estado == "fin_posicion")
  {
    publicarFinPosicion(posicion);
    return;
  }

  // Compatibilidad con el sistema antiguo:
  // Si llega {"posicion":"Pin1","estado":"correcta"}, no encendemos los 3.
  // Solo apagamos todo y esperamos órdenes individuales.
  if (estado == "correcta")
  {
    apagarTodasLasSustancias();
    return;
  }

  warn("Estado no reconocido: ");
  warnln(estado);
}

void confirmarPosicionSCARA()
{
  JsonDocument posicionSCARA;
  posicionSCARA["posicion"] = "manual";
  posicionSCARA["estado"] = "correcta";

  String respuesta_posicionSCARA;
  serializeJson(posicionSCARA, respuesta_posicionSCARA);

  enviarMensajePorTopic(SCARA_R_POSICIONES_TOPIC, respuesta_posicionSCARA);
}