import json
import time
from robodk import robolink

RDK = robolink.Robolink()

ROBOT_COLABORATIVO = "myRobotUR"
ROBOT_SCARA = "myScara"

PROGRAMA_INICIAL = "DeDejadaAPinchazo"

PROGRAMA_SCARA_1 = "PincharSustancia1"
PROGRAMA_SCARA_2 = "PincharSustancia2"
PROGRAMA_SCARA_3 = "PincharSustancia3"

PROGRAMA_INCU = "DePinchazoAIncu"

MECANISMO_INCUBADORA = "Refrigeradora"

DOOR_OPEN = "DoorOpen"
DOOR_CLOSE = "DoorClose"

TOPIC_COMANDOS = "giirob/pr2/station/demo/commands"
TOPIC_ORDEN_ESP32 = "scara/posiciones/respuestas"
TOPIC_ESTADO_ESP32 = "scara/posiciones/estado"
TOPIC_CONTROL_INCUBADORA = "giirob/pr2/incubadora/control"

posiciones = [
    "Pin1", "Pin2", "Pin3",
    "Pin4", "Pin5", "Pin6",
    "Pin7", "Pin8", "Pin9"
]

proceso_en_marcha = False
indice_actual = 0
mqttc_global = None


def obtener_item(nombre):
    item = RDK.Item(nombre)

    if not item.Valid():
        return None

    return item


def detener_por_error():
    global proceso_en_marcha

    proceso_en_marcha = False

    

def ejecutar_programa(nombre_programa, esperar=True):
    
    programa = obtener_item(nombre_programa)

    if programa is None:
        detener_por_error()
        return False

    programa.RunProgram()

    if esperar:
        programa.WaitFinished()

    return True

def publicar_esp32(mensaje):
    global mqttc_global

    if mqttc_global is None:
        detener_por_error()
        return False

    payload = json.dumps(mensaje)

    

    try:
        info = mqttc_global.publish(TOPIC_ORDEN_ESP32, payload, qos=0)

        info.wait_for_publish(timeout=2)

        return True

    except Exception as e:
        return False


def reset_leds_posicion(posicion):
    mensaje = {
        "posicion": posicion,
        "estado": "reset"
    }

    return publicar_esp32(mensaje)


def encender_led_sustancia(posicion, sustancia):
    mensaje = {
        "posicion": posicion,
        "estado": "inyectada",
        "sustancia": sustancia,
        "led": sustancia
    }

    return publicar_esp32(mensaje)

def ejecutar_scara_sincronizado(posicion):

    pasos = [
        (1, PROGRAMA_SCARA_1),
        (2, PROGRAMA_SCARA_2),
        (3, PROGRAMA_SCARA_3)
    ]

    for sustancia, programa in pasos:
        
        # 1) Primero encendemos el LED de esa sustancia
        
        ok = encender_led_sustancia(posicion, sustancia)

        if not ok:
            return False

        time.sleep(1.0)

        # 2) Ahora ejecutamos la inyección correspondiente

        ok = ejecutar_programa(programa, esperar=True)

        if not ok:
            return False

        time.sleep(0.4)


    publicar_esp32({
        "posicion": posicion,
        "estado": "fin_posicion"
    })

    return True


def iniciar_proceso(mqttc):
    global proceso_en_marcha, indice_actual, mqttc_global

    if proceso_en_marcha:
        return

    mqttc_global = mqttc
    proceso_en_marcha = True
    indice_actual = 0

    

    ok = ejecutar_programa(PROGRAMA_INICIAL, esperar=True)

    if not ok:
        detener_por_error()
        return

    mover_a_siguiente_posicion()


def mover_a_siguiente_posicion():
    global indice_actual, proceso_en_marcha

    if indice_actual >= len(posiciones):
        
        ok = finalizar_gradilla_en_incubadora()

        if not ok:
            detener_por_error()
            return

        proceso_en_marcha = False

       
        return

    posicion = posiciones[indice_actual]

   

    robot_ur = obtener_item(ROBOT_COLABORATIVO)
    target = obtener_item(posicion)

    if robot_ur is None or target is None:
        detener_por_error()
        return

    robot_ur.MoveL(target)
    robot_ur.WaitMove()


    # Apaga los 3 LEDs al comenzar cada pin.
    reset_leds_posicion(posicion)
    time.sleep(0.3)

    # Aquí se hace la nueva sincronización:
    # inyectar sustancia 1 -> LED 1
    # inyectar sustancia 2 -> LED 2
    # inyectar sustancia 3 -> LED 3
    ok = ejecutar_scara_sincronizado(posicion)

    if not ok:
        detener_por_error()
        return

    indice_actual += 1

    time.sleep(0.5)

    mover_a_siguiente_posicion()


def mover_puerta_incubadora(nombre_target):
    
    mecanismo = RDK.Item(MECANISMO_INCUBADORA)
    target = RDK.Item(nombre_target)

    if not mecanismo.Valid():
        return False

    if not target.Valid():
        return False

    try:
        mecanismo.MoveJ(target)

        while mecanismo.Busy():
            time.sleep(0.1)

        return True

    except Exception as e:
        return False

def iniciar_lectura_temperatura_incubadora():
    global mqttc_global

    if mqttc_global is None:
        return False

    mensaje = {
        "estado": "start_temp",
        "motivo": "soporte_dentro_puerta_cerrada"
    }

    payload = json.dumps(mensaje)

    mqttc_global.publish(TOPIC_CONTROL_INCUBADORA, payload)
    return True

def finalizar_gradilla_en_incubadora():
   
    ok = mover_puerta_incubadora(DOOR_OPEN)

    if not ok:
        return False

    time.sleep(0.5)

    ok = ejecutar_programa(PROGRAMA_INCU, esperar=True)

    if not ok:
        return False

    time.sleep(0.5)

    ok = mover_puerta_incubadora(DOOR_CLOSE)

    if not ok:
        return False

    time.sleep(0.5)

    # Activamos la lectura de temperatura en la ESP32.
    iniciar_lectura_temperatura_incubadora()

    return True

def procesar_estado_esp32(payload):
    try:
        data = json.loads(payload)
    except Exception as e:
        return


    posicion = str(data.get("posicion", "")).strip()
    estado = str(data.get("estado", "")).strip().lower()
    sustancia = data.get("sustancia", None)



def handle_message(mqttc, topic, payload):
    if isinstance(topic, bytes):
        topic = topic.decode("utf-8")

    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")

    topic = topic.strip()
    payload = payload.strip()


    if topic == TOPIC_COMANDOS:
        comando = payload.lower().strip()

        if comando in [
            "start_gradilla",
            "start_scara",
            "star_gradiilla",
            "start_gradiilla"
        ]:
            iniciar_proceso(mqttc)

        else:
            print("Comando no reconocido para ScaraController:", comando)

        return

    if topic == TOPIC_ESTADO_ESP32:
        procesar_estado_esp32(payload)
        return

