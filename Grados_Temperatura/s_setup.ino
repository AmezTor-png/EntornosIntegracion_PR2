void on_setup() 
{
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(TEMP_PIN, INPUT);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  setInternalLed(0);

  String hello_msg = String("Sensor NTC iniciado: ") + deviceID;

  JsonDocument doc;
  doc["message"] = hello_msg;
  doc["sensor"] = "NTC";
  doc["topic_temperatura"] = TEMP_TOPIC;
  doc["topic_led"] = LED_ACTION_TOPIC;
  

  String hello_msg_json;
  serializeJson(doc, hello_msg_json);

  enviarMensajePorTopic(HELLO_TOPIC, hello_msg_json);
}