import sys
import time
import json
import math

# Ruta RoboDK
sys.path.append(r"C:\RoboDK\Python")

from robodk import robolink
from robodk.robomath import transl

import paho.mqtt.client as mqtt


RDK = robolink.Robolink()

NOMBRE_SOPORTE = "Soporte1"

NOMBRE_REFERENCIA_DEJADA = "Dejada"

BROKER = "172.20.10.2"
PUERTO = 1883

TOPIC_COMANDOS = "giirob/pr2/station/demo/commands"

COMANDO_INICIO = "start_gradilla"

CLIENT_ID = "robodk_sensor_presencia_dejada"

LIMITE_X_MM = 80
LIMITE_Y_MM = 80
LIMITE_Z_MM = 80


TIEMPO_ENTRE_LECTURAS = 0.5

comando_enviado = False


def obtener_item(nombre):
    item = RDK.Item(nombre)

    if not item.Valid():
        return None

    return item


def conectar_mqtt():
    client = mqtt.Client(client_id=CLIENT_ID)

    client.connect(BROKER, PUERTO, 60)
    client.loop_start()

    time.sleep(1)

    return client


def publicar_start_gradilla(mqttc):
    mqttc.publish(TOPIC_COMANDOS, COMANDO_INICIO)


def obtener_posicion_relativa(objeto, referencia):
    pose_objeto_abs = objeto.PoseAbs()
    pose_ref_abs = referencia.PoseAbs()

    pose_relativa = pose_ref_abs.inv() * pose_objeto_abs

    x = pose_relativa.Pos()[0]
    y = pose_relativa.Pos()[1]
    z = pose_relativa.Pos()[2]

    return x, y, z


def soporte_esta_en_dejada(soporte, referencia):
    x, y, z = obtener_posicion_relativa(soporte, referencia)

    dentro_x = abs(x) <= LIMITE_X_MM
    dentro_y = abs(y) <= LIMITE_Y_MM
    dentro_z = abs(z) <= LIMITE_Z_MM

    return dentro_x and dentro_y and dentro_z


def main():
    global comando_enviado

    soporte = obtener_item(NOMBRE_SOPORTE)
    referencia_dejada = obtener_item(NOMBRE_REFERENCIA_DEJADA)

    if soporte is None:
        return

    if referencia_dejada is None:
        return

    mqttc = conectar_mqtt()

    
    while True:
        presente = soporte_esta_en_dejada(soporte, referencia_dejada)

        if presente and not comando_enviado:
            publicar_start_gradilla(mqttc)
            comando_enviado = True

        if not presente and comando_enviado:
            comando_enviado = False

        time.sleep(TIEMPO_ENTRE_LECTURAS)


if __name__ == "__main__":
    main()