
# iot_supervise

Projet 1 mini-station météo

## 1) Objectif du projet

Le but du projet est de faire un petit système IoT sur Raspberry Pi avec MQTT, MQTT Dash et MariaDB.

Le système doit :
- publier une mesure de température sur MQTT ;
- afficher cette mesure dans MQTT Dash ;
- recevoir une commande ON/OFF pour une DEL ;
- publier l’état réel de la DEL ;
- enregistrer les mesures et les événements dans MariaDB.

---

## 2) Diagramme d’architecture

```text
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

Préfixe utilisé :

ahuntsic/aec-iot/b3/iot_supervise/pi_iot/

Topics utilisés

Rôle	Topic
Télémétrie JSON	ahuntsic/aec-iot/b3/iot_supervise/pi_iot/sensors/temperature
Valeur simple dashboard	ahuntsic/aec-iot/b3/iot_supervise/pi_iot/sensors/temperature/value
Commande DEL	ahuntsic/aec-iot/b3/iot_supervise/pi_iot/actuators/led/cmd
État DEL	ahuntsic/aec-iot/b3/iot_supervise/pi_iot/actuators/led/state
Statut online	ahuntsic/aec-iot/b3/iot_supervise/pi_iot/status/online

Qui publie quoi / qui s’abonne à quoi

src/publisher_sensor.py
Publie :
	•	.../sensors/temperature
	•	.../sensors/temperature/value
	•	.../status/online

Client ID utilisé :
	•	b3-pub-pi_iot

src/subscriber_led.py
S’abonne à :
	•	.../actuators/led/cmd

Publie :
	•	.../actuators/led/state

Client ID utilisé :
	•	b3-sub-pi_iot-led

src/logger_mariadb.py
S’abonne à :
	•	ahuntsic/aec-iot/b3/iot_supervise/pi_iot/#

MQTT Dash
S’abonne à :
	•	.../sensors/temperature/value
	•	.../actuators/led/state
	•	.../status/online

Publie :
	•	.../actuators/led/cmd

Remarque importante

La séparation entre cmd et state est volontaire :
	•	cmd = ce qu’on demande ;
	•	state = l’état réel appliqué par le Raspberry Pi.

⸻

4) Exemples JSON

a) Température publiée

{
  "device": "pi_iot",
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

Dans le code , l’état de la DEL est publié en texte simple :

on

ou

off


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

mosquitto_sub -h localhost -p 1883 -t "ahuntsic/aec-iot/b3/iot_supervise/pi_iot/#" -v

Tester la commande ON de la DEL

mosquitto_pub -h localhost -p 1883 -t "ahuntsic/aec-iot/b3/iot_supervise/pi_iot/actuators/led/cmd" -m '{"state":"on"}' -q 1

Tester la commande OFF de la DEL

mosquitto_pub -h localhost -p 1883 -t "ahuntsic/aec-iot/b3/iot_supervise/pi_iot/actuators/led/cmd" -m '{"state":"off"}' -q 1

Vérifier l’état de la DEL

mosquitto_sub -h localhost -p 1883 -t "ahuntsic/aec-iot/b3/iot_supervise/pi_iot/actuators/led/state" -v

Vérifier la température

mosquitto_sub -h localhost -p 1883 -t "ahuntsic/aec-iot/b3/iot_supervise/pi_iot/sensors/temperature/#" -v


⸻

7) Comment vérifier MariaDB

Ouvrir MariaDB

sudo mariadb -u iot_sup -p

Sélectionner la base

USE iot_supervise;

Vérifier les 20 dernières températures

SELECT ts_utc, value, unit
FROM telemetry
WHERE device='pi_iot' AND topic LIKE '%/sensors/temperature'
ORDER BY ts_utc DESC
LIMIT 20;

Vérifier les 20 dernières humidités

SELECT ts_utc, value, unit
FROM telemetry
WHERE device='pi_iot' AND topic LIKE '%/sensors/humidity'
ORDER BY ts_utc DESC
LIMIT 20;

Vérifier les 10 derniers événements

SELECT ts_utc, kind, topic, payload
FROM events
ORDER BY ts_utc DESC
LIMIT 10;


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
	•	une capture MQTT Dash montrant la jauge ou la valeur numérique et le switch ;
	•	une capture MariaDB avec une requête SELECT montrant des données réelles.

⸻

10) Notes techniques
	•	La télémétrie capteur est publiée régulièrement en JSON.
	•	Le topic /value sert à simplifier l’affichage dans MQTT Dash.
	•	La commande DEL passe par .../cmd.
	•	L’état réel de la DEL est republié sur .../state.
	•	Le logger s’abonne au préfixe complet et enregistre les mesures dans telemetry ainsi que les commandes, états et statuts dans events.

