import sys
sys.path.append(r"C:\RoboDK\Python")

from robodk import robolink
from robodk.robolink import ITEM_TYPE_ROBOT, ITEM_TYPE_TARGET
import time

RDK = robolink.Robolink()

ROBOT_NAME = "myRobotUR"

POS_SEGURA = "Incu2"
POS_PRE_INCUBADORA = "PrePlaceIncu"
POS_INCUBADORA = "PlaceIncu"

MECANISMO_INCUBADORA = "Refrigeradora"
DOOR_OPEN = "DoorOpen"
DOOR_CLOSE = "DoorClose"

TOPIC_COMMANDS = "giirob/pr2/station/demo/commands"


def handle_message(mqttc, topic, payload):

    if topic != TOPIC_COMMANDS:
        return

    comando = payload.strip().upper()

    if comando == "SACAR_GRADILLA":
        proceso_sacar_gradilla()

    elif comando == "RESET":
        return
    else:
        return

def get_robot():
    robot = RDK.Item(ROBOT_NAME, ITEM_TYPE_ROBOT)

    if not robot.Valid():
        return None

    return robot


def get_target(nombre_target):
    target = RDK.Item(nombre_target, ITEM_TYPE_TARGET)

    if not target.Valid():
        return None

    return target


def mover_robot(nombre_target):
    robot = get_robot()
    target = get_target(nombre_target)

    if robot is None or target is None:
        return False


    try:
        robot.MoveJ(target)
        robot.WaitMove()
        return True

    except Exception as e:
        return False


def mover_puerta(nombre_target):
    mecanismo = RDK.Item(MECANISMO_INCUBADORA)
    target = get_target(nombre_target)

    if not mecanismo.Valid():
        return False

    if target is None:
        return False


    try:
        mecanismo.MoveJ(target)

        while mecanismo.Busy():
            time.sleep(0.1)

        return True

    except Exception as e:
        return False


def ejecutar_programa(nombre_programa):
  
    programa = RDK.Item(nombre_programa)

    if not programa.Valid():
        return False

    try:
        programa.RunProgram()

        while programa.Busy():
            time.sleep(0.1)

        time.sleep(0.2)

        return True

    except Exception as e:
        return False


def coger_gradilla():
    
    if not ejecutar_programa("CerrarGarra"):
        return False

    if not ejecutar_programa("Adjuntar Soporte"):
        return False

    return True


def ejecutar_lista_programas(programas):
    for nombre_programa in programas:
        ok = ejecutar_programa(nombre_programa)

        if not ok:
            return False

    return True


def proceso_sacar_gradilla():
    

    # 1. Abrir incubadora
    if not mover_puerta(DOOR_OPEN):
        return

    time.sleep(1)

    # 2. Ir a la incubadora
    if not mover_robot(POS_PRE_INCUBADORA):
        return

    if not mover_robot(POS_INCUBADORA):
        return

    # 3. Coger soporte/gradilla
    
    if not coger_gradilla():
        return

    time.sleep(1)

    # 4. Sacar soporte de la incubadora
    if not mover_robot(POS_PRE_INCUBADORA):
        return

    if not mover_robot(POS_SEGURA):
        return

    # 5. Cerrar incubadora
    if not mover_puerta(DOOR_CLOSE):
        return

    
    # 6. Ejecutar proceso posterior
    programas_post_incubadora = [
        "DeIncuACentri",
        "MeterProbetas",
        "SacarProbetas",
        "DeCentriAPinchazo",
        "PrgramaAlchol",
        "DePinchazoACentri",
        "MeterProbetas",
        "SacarProbetas",
        "DeCentriARecogida",
        "HomeRobot",
        "ResetSoporte"
    ]

    ok = ejecutar_lista_programas(programas_post_incubadora)

    if not ok:
        return

    