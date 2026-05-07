void on_setup() {

    // initialize digital pin LED_BUILTIN as an output.
    pinMode(LED_BUILTIN, OUTPUT);
    



    String hello_msg = String("Controladora temperatura iniciada: ") + deviceID;

  JsonDocument doc;
  doc["message"] = hello_msg;
  doc["modo"] = "controlador_temperatura";
  doc["topic_entrada"] = TEMP_TOPIC;
  doc["topic_salida"] = LED_ACTION_TOPIC;

  String hello_msg_json;
  serializeJson(doc, hello_msg_json);

  enviarMensajePorTopic(HELLO_TOPIC, hello_msg_json);
}

