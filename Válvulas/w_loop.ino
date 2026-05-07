long now, lastMsg = 0;
long sensorsUpdateInterval = 5000;

uint8_t ultimoEstadoBotonSCARA = HIGH;

void on_loop()
{
  uint8_t estadoActualBotonSCARA = digitalRead(SWITCH_POSICION_SCARA);
  
  if (estadoActualBotonSCARA == LOW && ultimoEstadoBotonSCARA == HIGH)
  {
    confirmarPosicionSCARA();
  }
  
  ultimoEstadoBotonSCARA = estadoActualBotonSCARA;

  now = millis();

  if (now - lastMsg > sensorsUpdateInterval)
  {
    lastMsg = now;
  }
}