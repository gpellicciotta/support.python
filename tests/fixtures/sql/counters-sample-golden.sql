/*!40101 SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
-- Example Counters Realistic Sample Dump
/*!40101 SET NAMES utf8mb4 */;
USE `counters`;

CREATE TABLE IF NOT EXISTS `versions` (
  `version` VARCHAR(50) NOT NULL,
  `major-version` TINYINT(4) NOT NULL,
  `minor-version` TINYINT(4) NOT NULL,
  `patch-version` TINYINT(4) NOT NULL,
  `label` VARCHAR(50),
  `info` longtext,
  `installation-time` TIMESTAMP NULL DEFAULT NULL,
  `deletion-time` TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (`version`)
);

INSERT INTO `versions` VALUES ('0.15.0', 0, 15, 0, '', 'Production baseline schema', '2026-01-01 00:00:00', NULL);

CREATE TABLE IF NOT EXISTS `users` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(250) NOT NULL DEFAULT '0',
  `email` VARCHAR(250) NOT NULL DEFAULT '0',
  `realms` LONGTEXT DEFAULT NULL,
  `settings` LONGTEXT DEFAULT NULL,
  `creation-time` TIMESTAMP NULL DEFAULT current_timestamp(),
  `last-activity-time` TIMESTAMP NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `deletion-time` TIMESTAMP NULL DEFAULT NULL,
  `auth-user-id` BIGINT(20) NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
);

INSERT INTO `users` VALUES
(1, 'Anonymized User 15', 'anon-user-15@anonymized.invalid', '["admin"]', '{"theme": "dark"}', '2026-01-01 10:00:00', '2026-01-02 11:00:00', NULL, 15), (2, 'Anonymized User 22', 'anon-user-22@anonymized.invalid', NULL, '{"timezone": "UTC"}', '2026-01-02 12:00:00', '2026-01-03 13:00:00', NULL, 22), (3, 'Anonymized User 3', 'anon-user-3@anonymized.invalid', NULL, NULL, '2026-01-03 14:00:00', '2026-01-04 15:00:00', NULL, NULL);

CREATE TABLE IF NOT EXISTS `tokens` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `type` VARCHAR(50) NOT NULL DEFAULT 'session',
  `user-id` BIGINT(20) NULL DEFAULT NULL,
  `data` LONGTEXT DEFAULT NULL,
  `creation-time` TIMESTAMP NOT NULL DEFAULT current_timestamp(),
  `last-activity-time` TIMESTAMP NOT NULL DEFAULT current_timestamp(),
  `expiry-time` TIMESTAMP NULL,
  PRIMARY KEY (`id`)
);

INSERT INTO `tokens` VALUES
(101, 'session', 1, 'YW5vbi10b2tlbi0xMDE=', '2026-01-01 10:00:00', '2026-01-01 10:00:00', '2026-01-08 10:00:00'), (102, 'session', 2, 'YW5vbi10b2tlbi0xMDI=', '2026-01-02 12:00:00', '2026-01-02 12:00:00', '2026-01-09 12:00:00');

CREATE TABLE IF NOT EXISTS `counters` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `user-id` BIGINT(20) NOT NULL,
  `description` VARCHAR(1000) DEFAULT NULL,
  `value-type` VARCHAR(20),
  `value-scale` INT(11) NOT NULL DEFAULT 0,
  `reset-value` BIGINT(20) DEFAULT 0,
  `threshold-goal` VARCHAR(20),
  `threshold-value` BIGINT(20),
  `creation-time` TIMESTAMP NOT NULL DEFAULT current_timestamp(),
  `last-update-time` TIMESTAMP NOT NULL DEFAULT current_timestamp(),
  `deletion-time` TIMESTAMP NULL,
  PRIMARY KEY (`id`)
);

INSERT INTO `counters` VALUES
(10, 'Daily Coffee', 1, 'Tracks cups of coffee', 'INTEGER', 0, 0, 'maximum', 3, '2026-01-01 10:05:00', '2026-01-02 10:05:00', NULL), (20, 'Running Distance', 2, 'Kilometers run per week', 'DECIMAL', 2, 0, 'minimum', 2000, '2026-01-02 12:05:00', '2026-01-03 12:05:00', NULL);

CREATE TABLE IF NOT EXISTS `webhooks` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `counter-id` BIGINT(20) NOT NULL,
  `user-id` BIGINT(20) NOT NULL,
  `target-url` VARCHAR(2000) NOT NULL,
  `secret` VARCHAR(100) NOT NULL,
  `active` TINYINT(1) NOT NULL DEFAULT 1,
  `creation-time` TIMESTAMP NOT NULL DEFAULT current_timestamp(),
  `last-update-time` TIMESTAMP NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
);

INSERT INTO `webhooks` VALUES
(5, 10, 1, 'https://example.local/webhook/anon-5', 'anon-secret-5', 1, '2026-01-01 10:10:00', '2026-01-01 10:10:00');
