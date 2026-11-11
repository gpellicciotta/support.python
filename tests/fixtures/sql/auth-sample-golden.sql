/*!40101 SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
-- Realistic sample dump for example-auth
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;

-- Clean existing data
DELETE FROM `application-grants`;
DELETE FROM `tokens`;
DELETE FROM `credentials`;
DELETE FROM `settings`;
DELETE FROM `users`;
DELETE FROM `applications`;

-- Seed users
INSERT INTO `users` (`id`, `name`, `email`, `realms`, `creation-time`, `last-activity-time`, `expiry-time`) VALUES
(0, 'Admin User', 'admin@anonymized.invalid', '[ "admin" ]', '2026-01-01 00:00:00', '2026-01-01 00:00:00', NULL), (1, 'Anonymized User 1', 'anon-user-1@anonymized.invalid', '[ "owner" ]', '2026-01-02 10:00:00', '2026-01-02 10:00:00', NULL), (2, 'Anonymized User 2', 'anon-user-2@anonymized.invalid', '[ "owner" ]', '2026-01-03 11:00:00', '2026-01-03 11:00:00', NULL);

-- Seed applications
INSERT INTO `applications` (`id`, `name`, `description`, `base-url`, `logo-url`, `redirect-url`, `app-secret`, `creation-time`, `last-update-time`) VALUES
(1, 'auth', 'Example Auth', 'http://localhost:8020', 'http://localhost:8020/img/auth-icon.svg', NULL, NULL, '2026-01-01 00:00:00', '2026-01-01 00:00:00'), (2, 'counters', 'Example Counters', 'http://localhost:8010', 'http://localhost:8010/img/counters-icon.svg', 'http://localhost:8010/dashboard', NULL, '2026-01-01 00:00:00', '2026-01-01 00:00:00');

-- Seed credentials
INSERT INTO `credentials` (`id`, `type`, `user-id`, `data`, `creation-time`, `last-update-time`, `expiry-time`) VALUES
(1, 'password', 1, 'MDEwMjAzMDQwNTA2MDcwODA5MGEwYjBjMGQwZTBmMTAxMTEyMTMxNDE1MTYxNzE4MTkxYTFiMWMxZDFlMWYyMDpkNjUyZWVhMGM0MmIwYTQ3MDU4OGJiYWNjNjk0YWRhZTZmYmI0MDA2N2Y1YTMwMGYxZjNhYTA2MzYzYzY5Yzlm', '2026-01-02 10:00:00', '2026-01-02 10:00:00', NULL), (2, 'federated-id', 2, 'Z29vZ2xlOmh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbTphbm9uLXN1Yi0y', '2026-01-03 11:00:00', '2026-01-03 11:00:00', NULL);

-- Seed tokens
INSERT INTO `tokens` (`id`, `type`, `user-id`, `data`, `creation-time`, `last-update-time`, `expiry-time`) VALUES
(100, 'session', 1, 'YW5vbi10b2tlbi0xMDA=', '2026-01-02 10:00:00', '2026-01-02 10:00:00', '2026-12-31 23:59:59');

-- Seed settings
INSERT INTO `settings` (`id`, `user-id`, `name`, `value`, `creation-time`, `last-update-time`) VALUES
(1, 1, 'theme', 'dark', '2026-01-02 10:00:00', '2026-01-02 10:00:00');

-- Seed application-grants
INSERT INTO `application-grants` (`id`, `user-id`, `application-id`, `granted-by`, `creation-time`) VALUES
(1, 1, 2, 0, '2026-01-02 10:00:00');

/*!40014 SET FOREIGN_KEY_CHECKS=1 */;
