"""
subscriber_logger.py
====================
But :
- S'abonner à MQTT (Mosquitto)
- Recevoir messages
- Enregistrer en MariaDB (essentiel seulement)

Principe simple :
- Si le topic contient "/sensors/" => table telemetry
- Sinon => table events (cmd/state/status/other)
- On stocke toujours payload brut (texte)
- On essaye d'extraire value/unit pour telemetry si JSON valide

Pourquoi c'est utile ?
- On garde un historique réel (debug, rapport, vérification)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

import pymysql
import paho.mqtt.client as mqtt


# -----------------------------
# 1) Paramètres MQTT
# -----------------------------
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_KEEPALIVE = 60

# IMPORTANT : "iot_supervise/pi_iot" pour votre équipe
#MQTT_PREFIX = "ahuntsic/aec-iot/b3/iot_supervise/pi_iot"
MQTT_TOPIC_FILTER = f"ahuntsic/aec-iot/b3/iot_supervise/pi_iot/#"

MQTT_CLIENT_ID = "b3-logger-iot_supervise-pi_iot"


# -----------------------------
# 2) Paramètres MariaDB
# -----------------------------
DB_HOST = "localhost"
DB_USER = "iot_sup"
DB_PASSWORD = "iot_sup"
DB_NAME = "iot_supervise"

def utc_now_naive() -> datetime:
    """
    MariaDB DATETIME ne stocke pas le fuseau horaire.
    Convention : on stocke en UTC.
    (naive datetime = sans tzinfo)
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def db_connect() -> pymysql.connections.Connection:
    """
    Ouvre une connexion vers MariaDB.
    autocommit=True : chaque INSERT est écrit immédiatement.
    (Simple pour le labo)
    """
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True,
        charset="utf8mb4",
    )


# Connexion DB globale (simple)
db = db_connect()

# -----------------------------
# 3) Fonctions utilitaires
# -----------------------------
def extract_device(topic: str) -> str:
    """
    Convention : ahuntsic/aec-iot/b3/<team>/<device>/...
    => <device> est souvent à l'index 4
    """
    parts = topic.split("/")
    return parts[4] if len(parts) >= 5 else "unknown"


def is_telemetry(topic: str) -> bool:
    """
    On considère telemetry si le topic contient '/sensors/'.
    On ignore les topics qui finissent par '/value' (si vous en publiez)
    pour éviter de doubler les données.
    """
    if "/sensors/" not in topic:
        return False
    if topic.endswith("/value"):
        return False
    return True


def classify_kind(topic: str) -> str:
    """
    Classe l'événement selon le topic.
    """
    if "/cmd/" in topic:
        return "cmd"
    if "/state/" in topic:
        return "state"
    if "/status/" in topic:
        return "status"
    return "other"


def try_parse_json(payload_text: str) -> Optional[dict[str, Any]]:
    """
    Tente de parser le payload en JSON.
    Retourne un dict si OK, sinon None.
    """
    try:
        obj = json.loads(payload_text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None
    

# -----------------------------
# 4) INSERT en BD (SQL paramétré)
# -----------------------------
def insert_telemetry(ts_utc: datetime, device: str, topic: str, payload_text: str) -> None:
    """
    Insère une mesure dans telemetry.
    Si JSON contient value/unit, on remplit value/unit. Sinon NULL.
    """
    obj = try_parse_json(payload_text)
    value = None
    unit = None
    
    if obj is not None:
        if "value" in obj:
            try:
                value = float(obj["value"])
            except (TypeError, ValueError):
                value = None
    if "unit" in obj and isinstance(obj["unit"], str):
        unit = obj["unit"][:16]
    
    sql = """
        INSERT INTO telemetry (ts_utc, device, topic, value, unit, payload)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    with db.cursor() as cur:
        cur.execute(sql, (ts_utc, device, topic, value, unit, payload_text))


def insert_event(ts_utc: datetime, device: str, topic: str, kind: str, payload_text: str) -> None:
    """
    Insère un événement dans events.
    """
    sql = """
        INSERT INTO events (ts_utc, device, topic, kind, payload)
        VALUES (%s, %s, %s, %s, %s)
    """
    with db.cursor() as cur:
        cur.execute(sql, (ts_utc, device, topic, kind, payload_text))


# -----------------------------
# 5) Callbacks MQTT
# -----------------------------
def on_connect(client, _userdata, _flags, reason_code, properties=None):
    """
    Appelé quand le broker répond à la connexion.
    reason_code == 0 => OK
    """
    print(f"[CONNECT] reason_code={reason_code}")
    if reason_code == 0:
        client.subscribe(MQTT_TOPIC_FILTER, qos=0)
        print(f"[SUB] {MQTT_TOPIC_FILTER}")
    else:
        print("[ERROR] Connexion MQTT échouée.")


def on_message(_client, _userdata, msg: mqtt.MQTTMessage):
    """
    À chaque message reçu :
    - on décide telemetry vs event
    - on INSERT en BD
    """
    topic = msg.topic
    payload_text = msg.payload.decode("utf-8", errors="replace")
    device = extract_device(topic)
    ts = utc_now_naive()
    
    try:
        if is_telemetry(topic):
            insert_telemetry(ts, device, topic, payload_text)
            print(f"[DB] telemetry <- {topic}")
        else:
            kind = classify_kind(topic)
            insert_event(ts, device, topic, kind, payload_text)
            print(f"[DB] events({kind}) <- {topic}")
    
    except pymysql.MySQLError as e:
        # Si la DB tombe, on log et on tente une reconnexion simple
        print(f"[DB-ERROR] {e} -> reconnexion")
        global db
        try:
            db.close()
        except Exception:
            pass
        db = db_connect()
    
    
def on_disconnect(_client, _userdata, reason_code, properties=None):
    print(f"[DISCONNECT] reason_code={reason_code}")


# -----------------------------
# 6) Démarrage
# -----------------------------
client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=MQTT_KEEPALIVE)

print("[INFO] Logger démarré. CTRL+C pour arrêter.")
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[STOP] arrêt demandé")
finally:
    try:
        db.close()
    except Exception:
        pass
    client.disconnect()