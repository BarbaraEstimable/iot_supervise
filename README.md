# iot_supervise


# Projet 1 — MQTT, Raspberry Pi, DEL et MariaDB

## 1) Objectif du projet

Ce projet consiste à réaliser un mini système IoT sur Raspberry Pi avec MQTT, MQTT Dash et MariaDB.

Le système doit :
- publier une mesure de température sur MQTT ;
- afficher cette mesure dans MQTT Dash ;
- recevoir une commande ON/OFF pour une DEL ;
- publier l’état réel de la DEL ;
- enregistrer les mesures et événements dans MariaDB.

Le projet suit l’architecture demandée :
capteur / script Python → broker MQTT → dashboard / subscriber → action GPIO → journalisation en base de données.

---

## 2) Diagramme d’architecture

a
                 +----------------------+
                 |   MQTT Dash (mobile) |
                 | - lit la température |
                 | - envoie cmd DEL     |
                 +----------+-----------+
                            |
                            | MQTT
                            v
+-------------------+   +-------------------+   +----------------------+
| Publisher         |   | Mosquitto Broker  |   | Subscriber LED       |
| température       +-->+ localhost:1883    +-->+ - reçoit cmd         |
| Raspberry Pi      |   |                   |   | - commande la DEL    |
| - JSON température|   |                   |   | - publie state       |
| - value dashboard |   +---------+---------+   +----------+-----------+
| - status online   |             |                        |
+-------------------+             |                        |
                                  |                        v
                                  |                     +------+
                                  |                     | DEL  |
                                  |                     +------+
                                  |
                                  v
                         +----------------------+
                         | Logger MariaDB       |
                         | - lit les topics     |
                         | - insert telemetry   |
                         | - insert events      |
                         +----------------------+


⸻

3) Conventions de topics

Préfixe obligatoire d’équipe :

ahuntsic/aec-iot/b3/<TEAM>/<DEVICE>/


Topics utilisés

Rôle	Topic
Télémétrie JSON	ahuntsic/aec-iot/b3/<TEAM>/<DEVICE>/sensors/temperature
Valeur simple dashboard	ahuntsic/aec-iot/b3/<TEAM>/<DEVICE>/sensors/temperature/value
Commande DEL	ahuntsic/aec-iot/b3/<TEAM>/<DEVICE>/actuators/led/cmd
État DEL	ahuntsic/aec-iot/b3/<TEAM>/<DEVICE>/actuators/led/state
Statut online	ahuntsic/aec-iot/b3/<TEAM>/<DEVICE>/status/online

Qui publie quoi / qui s’abonne à quoi

src/publisher_sensor.py
Publie :
	•	.../sensors/temperature
	•	.../sensors/temperature/value
	•	.../status/online

src/subscriber_led.py
S’abonne à :
	•	.../actuators/led/cmd

Publie :
	•	.../actuators/led/state

src/logger_mariadb.py
S’abonne à :
	•	ahuntsic/aec-iot/b3/<TEAM>/<DEVICE>/#

MQTT Dash
S’abonne à :
	•	.../sensors/temperature/value
	•	.../actuators/led/state
	•	.../status/online

Publie :
	•	.../actuators/led/cmd

Remarque importante

La séparation cmd / state est volontaire :
	•	cmd = ce qu’on demande ;
	•	state = l’état réel appliqué par le Raspberry Pi.

⸻

4) Exemples JSON

a) Température publiée

{
  "device": "<DEVICE>",
  "sensor": "temperature",
  "value": 23.42,
  "unit": "C",
  "ts": "2026-03-18T18:30:12.120Z"
}

b) Commande DEL envoyée

{
  "state": "on"
}

ou

{
  "state": "off"
}

c) État DEL publié

{
  "device": "<DEVICE>",
  "actuator": "led",
  "state": "on",
  "ts": "2026-03-18T18:31:05.501Z"
}


⸻

5) Procédure d’installation / exécution

Étape 1 — Installer les dépendances système

sudo apt update
sudo apt install -y mosquitto mosquitto-clients mariadb-server python3-venv

Étape 2 — Créer et activer l’environnement virtuel

python3 -m venv .venv
source .venv/bin/activate

Étape 3 — Installer les bibliothèques Python

pip install -r requirements.txt

Étape 4 — Démarrer les services

sudo systemctl enable --now mosquitto
sudo systemctl enable --now mariadb

Étape 5 — Créer la base de données

sudo mariadb < db/schema.sql

Étape 6 — Lancer les scripts

Dans des terminaux séparés :

python3 src/logger_mariadb.py
python3 src/publisher_sensor.py
python3 src/subscriber_led.py


⸻

6) Comment tester avec mosquitto_pub / mosquitto_sub

Voir tous les topics du projet

mosquitto_sub -h localhost -p 1883 -t "ahuntsic/aec-iot/b3/<TEAM>/<DEVICE>/#" -v

Tester la commande ON de la DEL

mosquitto_pub -h localhost -p 1883 \
-t "ahuntsic/aec-iot/b3/<TEAM>/<DEVICE>/actuators/led/cmd" \
-m '{"state":"on"}' -q 1

Tester la commande OFF de la DEL

mosquitto_pub -h localhost -p 1883 \
-t "ahuntsic/aec-iot/b3/<TEAM>/<DEVICE>/actuators/led/cmd" \
-m '{"state":"off"}' -q 1

Vérifier l’état de la DEL

mosquitto_sub -h localhost -p 1883 \
-t "ahuntsic/aec-iot/b3/<TEAM>/<DEVICE>/actuators/led/state" -v

Vérifier la température

mosquitto_sub -h localhost -p 1883 \
-t "ahuntsic/aec-iot/b3/<TEAM>/<DEVICE>/sensors/temperature/#" -v


⸻

7) Comment vérifier MariaDB

Ouvrir MariaDB

sudo mariadb

Sélectionner la base

USE iot_b3;

Vérifier les 10 dernières mesures

SELECT id, ts_utc, device, topic, value, unit
FROM telemetry
ORDER BY id DESC
LIMIT 10;

Vérifier les 10 derniers événements

SELECT id, ts_utc, device, kind, topic, payload
FROM events
ORDER BY id DESC
LIMIT 10;

Vérifier le volume total

SELECT
  (SELECT COUNT(*) FROM telemetry) AS n_telemetry,
  (SELECT COUNT(*) FROM events) AS n_events;

Requêtes utiles supplémentaires

Dernières mesures de température

SELECT ts_utc, value, unit
FROM telemetry
WHERE device='<DEVICE>' AND topic LIKE '%/sensors/temperature'
ORDER BY ts_utc DESC
LIMIT 20;

Dernières commandes

SELECT ts_utc, payload
FROM events
WHERE device='<DEVICE>' AND kind='cmd'
ORDER BY ts_utc DESC
LIMIT 20;

Nombre d’événements par type

SELECT kind, COUNT(*) AS n
FROM events
GROUP BY kind
ORDER BY n DESC;


⸻

8) Structure du dépôt

src/
  publisher_sensor.py
  subscriber_led.py
  logger_mariadb.py

db/
  schema.sql
  queries.sql

README.md
requirements.txt


⸻

9) Preuves à fournir

Le dépôt contient au minimum :
	•	une capture MQTT Dash montrant la jauge ou valeur numérique et le switch ;
	•	une capture MariaDB avec une requête SELECT montrant des données réelles.

⸻

10) Notes techniques
	•	La télémétrie capteur est publiée régulièrement en JSON.
	•	Le topic /value sert à simplifier l’affichage dans MQTT Dash.
	•	La commande DEL passe par .../cmd.
	•	L’état réel de la DEL est republié sur .../state.
	•	Le logger s’abonne au préfixe complet et enregistre les mesures dans telemetry ainsi que les commandes/états/statuts dans events.


