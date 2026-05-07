import sys
sys.path.append(r"C:\RoboDK\Python")
sys.path.insert(0, r"C:\Users\algar\Desktop\PR2\PR2_RoboDK")

import paho.mqtt.client as mqtt
import importlib.util
import traceback
import threading


def cargar_modulo(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


robot_controller = cargar_modulo(
    "RobotController",
    r"C:\Users\algar\Desktop\PR2\PR2_RoboDK\RobotController.py"
)

scara_controller = cargar_modulo(
    "ScaraController",
    r"C:\Users\algar\Desktop\PR2\PR2_RoboDK\ScaraController.py"
)



broker = "172.20.10.2"
puerto = 1883

station_commands_topic = "giirob/pr2/station/demo/commands"
station_status_topic = "giirob/pr2/station/demo/status"
temp_topic = "giirob/pr2/incubadora/temperatura"
scara_estado_topic = "scara/posiciones/estado"


def on_connect(client, userdata, flags, reason_code, properties=None):
    client.subscribe(station_commands_topic, 0)
    client.subscribe(temp_topic, 0)
    client.subscribe(scara_estado_topic, 0)
    client.publish(station_status_topic, "listo")
    

def ejecutar_scara_en_hilo(mqttc, topic, payload):
    try:
        scara_controller.handle_message(mqttc, topic, payload)
    except Exception:
        pass

def ejecutar_robot_en_hilo(mqttc, topic, payload):
    try:
        robot_controller.handle_message(mqttc, topic, payload)
    except Exception:
        pass


def on_message(mqttc, userdata, msg):
    topic = msg.topic.strip()
    payload = msg.payload.decode("utf-8").strip()

    # MENSAJES DEL ESP32 PARA SCARA

    if topic == scara_estado_topic:
        
        try:
            scara_controller.handle_message(mqttc, topic, payload)
        except Exception:
            pass
        return

    # MENSAJES DE TEMPERATURA PARA ROBOT CONTROLLER
    
    if topic == temp_topic:
        
        try:
            robot_controller.handle_message(mqttc, topic, payload)
        except Exception:
            pass
        return

    
    # COMANDOS GENERALES
    
    if topic == station_commands_topic:
        comando = payload.lower().strip()

        if comando in [
            "start_gradilla",
        ]:
        
            hilo_scara = threading.Thread(
                target=ejecutar_scara_en_hilo,
                args=(mqttc, topic, payload),
                daemon=True
            )

            hilo_scara.start()
            return

        else:
        
            hilo_robot = threading.Thread(
                target=ejecutar_robot_en_hilo,
                args=(mqttc, topic, payload),
                daemon=True
            )

            hilo_robot.start()
            return



mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect(broker, puerto, 60)

mqttc.loop_forever()