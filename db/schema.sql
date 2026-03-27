
CREATE DATABASE IF NOT EXISTS iot_supervise
    -> CHARACTER SET utf8mb4
    -> COLLATE utf8mb4_unicode_ci;
CREATE USER 'iot_sup'@'localhost' IDENTIFIED BY 'iot_sup';
GRANT ALL PRIVILEGES ON iot_supervise.* TO 'iot'@'localhost';
FLUSH PRIVILEGES;





CREATE TABLE telemetry (
    -> id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    -> ts_utc DATETIME(3) NOT NULL,
    -> device VARCHAR(32) NOT NULL,
    -> topic VARCHAR(255) NOT NULL,
    -> value DOUBLE NULL,
    -> unit VARCHAR(16) NULL,
    -> payload TEXT NOT NULL,
    -> PRIMARY KEY (id),
    -> INDEX idx_telemetry_device_ts (device, ts_utc)
    -> );


CREATE TABLE events (
    -> id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    -> ts_utc DATETIME(3) NOT NULL,
    -> device VARCHAR(32) NOT NULL,
    -> topic VARCHAR(255) NOT NULL,
    -> kind VARCHAR(16) NOT NULL, -- cmd/state/status/other
    -> payload TEXT NOT NULL,
    -> PRIMARY KEY (id),
    -> INDEX idx_events_device_ts (device, ts_utc)
    -> );
