-- Requête 1 — Dernières mesures température
SELECT ts_utc, value, unit
FROM telemetry
WHERE device='pi01' AND topic LIKE '%/sensors/temperature'
ORDER BY ts_utc DESC
LIMIT 20;


--Requête 2 — Dernières commandes
SELECT ts_utc, payload
FROM events
WHERE device='pi01' AND kind='cmd'
ORDER BY ts_utc DESC
LIMIT 20;

--Requête 3 — Nombre d’événements par type
SELECT kind, COUNT(*) AS n
FROM events
GROUP BY kind
ORDER BY n DESC;

-- 2) 10 derniers événements
SELECT id, ts_utc, device, kind, topic, payload
FROM events
ORDER BY id DESC
LIMIT 10;


-- 3) Compter le volume
SELECT (SELECT COUNT(*) FROM telemetry) AS n_telemetry,
(SELECT COUNT(*) FROM events) AS n_events;