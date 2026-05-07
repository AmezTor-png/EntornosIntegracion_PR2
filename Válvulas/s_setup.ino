void on_setup() {
  pinMode(SUSTANCIA_A, OUTPUT);
  pinMode(SUSTANCIA_B, OUTPUT);
  pinMode(SUSTANCIA_C, OUTPUT);

  digitalWrite(SUSTANCIA_A, LOW);
  digitalWrite(SUSTANCIA_B, LOW);
  digitalWrite(SUSTANCIA_C, LOW);

  pinMode(SWITCH_POSICION_SCARA, INPUT_PULLUP);

  info("Setup valvulas terminado");
}