import json
import time
import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

import paho.mqtt.client as mqtt
import psycopg
from psycopg.rows import dict_row


MQTT_BROKER = "172.20.10.2"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "mqtt_sql_logger_pr2"

MQTT_TOPICS = [
    ("giirob/pr2/#", 0),
    ("scara/#", 0)
]


DB_NAME = "gdi"
DB_USER = "postgres"
DB_PASSWORD = "Gualda2006."
DB_HOST = "localhost"
DB_PORT = "5432"
DB_SCHEMA = "pr2"


BATCH_SIZE = 10
BATCH_TIMEOUT = 2.0
MAX_QUEUE_SIZE = 1000



@dataclass
class ParsedMqttMessage:
    timestamp_iso: datetime
    timestamp_unix: float
    topic: str
    payload_raw: str
    es_json: bool
    payload_json: Optional[dict]
    device: Optional[str]
    posicion: Optional[str]
    estado: Optional[str]
    sustancia: Optional[int]
    temperatura: Optional[float]
    adc: Optional[int]
    vout: Optional[float]
    rntc: Optional[float]




class MessageParser:
    @staticmethod
    def parse(topic: str, payload_raw: str) -> ParsedMqttMessage:
        now = datetime.now()
        timestamp_unix = time.time()

        es_json = False
        payload_json = None

        device = None
        posicion = None
        estado = None
        sustancia = None
        temperatura = None
        adc = None
        vout = None
        rntc = None

        try:
            data = json.loads(payload_raw)

            if isinstance(data, dict):
                es_json = True
                payload_json = data

                device = MessageParser.to_str(data.get("device"))
                posicion = MessageParser.to_str(data.get("posicion"))
                estado = MessageParser.to_str(data.get("estado"))

                sustancia = MessageParser.to_int(data.get("sustancia"))
                temperatura = MessageParser.to_float(data.get("temperatura"))
                adc = MessageParser.to_int(data.get("adc"))
                vout = MessageParser.to_float(data.get("vout"))
                rntc = MessageParser.to_float(data.get("rntc"))

        except Exception:
            es_json = False
            payload_json = None

            # Si no es JSON, puede ser un comando simple como SACAR_GRADILLA.
            estado = payload_raw.strip()

        return ParsedMqttMessage(
            timestamp_iso=now,
            timestamp_unix=timestamp_unix,
            topic=topic,
            payload_raw=payload_raw,
            es_json=es_json,
            payload_json=payload_json,
            device=device,
            posicion=posicion,
            estado=estado,
            sustancia=sustancia,
            temperatura=temperatura,
            adc=adc,
            vout=vout,
            rntc=rntc
        )

    @staticmethod
    def to_str(value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def to_int(value: Any) -> Optional[int]:
        try:
            if value is None:
                return None
            return int(value)
        except Exception:
            return None

    @staticmethod
    def to_float(value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            return float(value)
        except Exception:
            return None




class DatabaseManager:
    def __init__(self):
        self.conn = psycopg.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            row_factory=dict_row
        )

        self.conn.execute(f"SET search_path TO {DB_SCHEMA};")
        self.conn.commit()

    def close(self):
        self.conn.close()

    def get_or_create_topic(self, topic_name: str) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO topics (nombre_topic)
                VALUES (%s)
                ON CONFLICT (nombre_topic) DO UPDATE
                SET nombre_topic = EXCLUDED.nombre_topic
                RETURNING id_topic;
                """,
                (topic_name,)
            )

            row = cur.fetchone()
            self.conn.commit()
            return row["id_topic"]

    def get_or_create_device(self, device_name: Optional[str]) -> Optional[int]:
        if not device_name:
            return None

        device_type = self.detect_device_type(device_name)

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dispositivos (nombre, tipo, descripcion)
                VALUES (%s, %s, %s)
                ON CONFLICT (nombre) DO UPDATE
                SET nombre = EXCLUDED.nombre
                RETURNING id_dispositivo;
                """,
                (
                    device_name,
                    device_type,
                    "Detectado automáticamente desde MQTT"
                )
            )

            row = cur.fetchone()
            self.conn.commit()
            return row["id_dispositivo"]

    @staticmethod
    def detect_device_type(device_name: str) -> str:
        name = device_name.lower()

        if "esp32" in name or "giirobpr2-device" in name:
            return "ESP32"

        if "robot" in name or "ur" in name:
            return "ROBOT"

        if "python" in name or "listener" in name:
            return "PYTHON"

        return "DESCONOCIDO"

    def insert_message(self, msg: ParsedMqttMessage):
        id_topic = self.get_or_create_topic(msg.topic)
        id_dispositivo = self.get_or_create_device(msg.device)

        payload_json_str = None
        if msg.payload_json is not None:
            payload_json_str = json.dumps(msg.payload_json)

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO mensajes_mqtt (
                    timestamp_iso,
                    timestamp_unix,
                    id_topic,
                    id_dispositivo,
                    payload_raw,
                    es_json,
                    payload_json,
                    posicion,
                    estado,
                    sustancia,
                    temperatura,
                    adc,
                    vout,
                    rntc
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s::jsonb,
                    %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id_mensaje;
                """,
                (
                    msg.timestamp_iso,
                    msg.timestamp_unix,
                    id_topic,
                    id_dispositivo,
                    msg.payload_raw,
                    msg.es_json,
                    payload_json_str,
                    msg.posicion,
                    msg.estado,
                    msg.sustancia,
                    msg.temperatura,
                    msg.adc,
                    msg.vout,
                    msg.rntc
                )
            )

            row = cur.fetchone()
            id_mensaje = row["id_mensaje"]

            self.insert_specific_tables(cur, id_mensaje, msg)

        self.conn.commit()

    def insert_specific_tables(self, cur, id_mensaje: int, msg: ParsedMqttMessage):
        if msg.topic == "giirob/pr2/incubadora/temperatura":
            payload = msg.payload_json or {}

            valida = bool(payload.get("valida", msg.temperatura is not None))
            led = payload.get("led")
            temp_activa = payload.get("temp_activa")

            cur.execute(
                """
                INSERT INTO lecturas_temperatura (
                    id_mensaje,
                    temperatura,
                    valida,
                    adc,
                    vout,
                    rntc,
                    led,
                    temp_activa
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    id_mensaje,
                    msg.temperatura,
                    valida,
                    msg.adc,
                    msg.vout,
                    msg.rntc,
                    led,
                    temp_activa
                )
            )

        if msg.topic.startswith("scara/"):
            if msg.posicion is not None or msg.estado is not None:
                cur.execute(
                    """
                    INSERT INTO eventos_scara (
                        id_mensaje,
                        posicion,
                        sustancia,
                        estado
                    )
                    VALUES (%s, %s, %s, %s);
                    """,
                    (
                        id_mensaje,
                        msg.posicion or "desconocida",
                        msg.sustancia,
                        msg.estado or "desconocido"
                    )
                )

        if msg.topic == "giirob/pr2/station/demo/commands":
            comando = msg.payload_raw.strip()

            cur.execute(
                """
                INSERT INTO comandos_robot (
                    id_mensaje,
                    comando,
                    ejecutado
                )
                VALUES (%s, %s, %s);
                """,
                (
                    id_mensaje,
                    comando,
                    False
                )
            )


# ============================================================
# HILO ESCRITOR SQL
# ============================================================

class DatabaseWriterThread(threading.Thread):
    def __init__(self, db: DatabaseManager, message_queue: queue.Queue):
        super().__init__(daemon=True)
        self.db = db
        self.message_queue = message_queue
        self.running = True

    def run(self):
        print("Hilo SQL iniciado.")

        while self.running:
            batch = self.collect_batch()

            for msg in batch:
                try:
                    self.db.insert_message(msg)
                except Exception as e:
                    print("ERROR insertando mensaje en SQL:")
                    print(e)
                    self.db.conn.rollback()

            if batch:
                print(f"Guardados {len(batch)} mensajes en PostgreSQL.")

    def collect_batch(self):
        batch = []
        start = time.time()

        while len(batch) < BATCH_SIZE:
            timeout = max(0.1, BATCH_TIMEOUT - (time.time() - start))

            try:
                msg = self.message_queue.get(timeout=timeout)
                batch.append(msg)
                self.message_queue.task_done()
            except queue.Empty:
                break

        return batch

    def stop(self):
        self.running = False



class MqttSqlLogger:
    def __init__(self):
        self.db = DatabaseManager()
        self.message_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self.writer = DatabaseWriterThread(self.db, self.message_queue)

        self.client = mqtt.Client(
            client_id=MQTT_CLIENT_ID,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def start(self):
        print("Iniciando logger MQTT → SQL")
        print("Broker:", MQTT_BROKER)
        print("Base de datos:", DB_NAME)
        print("Esquema:", DB_SCHEMA)

        self.writer.start()

        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()

        print("Logger activo. Pulsa CTRL+C para salir.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Cerrando logger...")
            self.stop()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

        self.writer.stop()
        self.writer.join(timeout=5)

        self.db.close()

        print("Logger cerrado correctamente.")

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        print("======================================")
        print("MQTT LOGGER CONECTADO")
        print("Reason code:", reason_code)
        print("======================================")

        for topic, qos in MQTT_TOPICS:
            client.subscribe(topic, qos)
            print("Suscrito a:", topic)

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties=None):
        print("MQTT LOGGER DESCONECTADO")
        print("Reason code:", reason_code)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload_raw = msg.payload.decode("utf-8", errors="replace")

        print("--------------------------------------")
        print("Mensaje MQTT recibido")
        print("Topic:", topic)
        print("Payload:", payload_raw)

        parsed = MessageParser.parse(topic, payload_raw)

        try:
            self.message_queue.put_nowait(parsed)
        except queue.Full:
            print("ERROR: cola llena. Mensaje descartado.")




if __name__ == "__main__":
    logger = MqttSqlLogger()
    logger.start()