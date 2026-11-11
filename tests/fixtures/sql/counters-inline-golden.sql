/*!40101 SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
INSERT INTO `users` VALUES (1, 'Anonymized User 15', 'anon-user-15@anonymized.invalid', NULL, NULL, '2026-01-01', '2026-01-01', NULL, 15);
INSERT INTO `users` (`auth_user_id`, `email`, `id`, `name`) VALUES (NULL, 'anon-user-2@anonymized.invalid', 2, 'Anonymized User 2');
INSERT INTO `tokens` VALUES (101, 'session', 15, 'YW5vbi10b2tlbi0xMDE=', '2026-01-02', '2026-01-02', NULL);
INSERT INTO `webhooks` VALUES (5, 10, 15, 'https://example.local/webhook/anon-5', 'anon-secret-5', 1, '2026-01-01', '2026-01-01');
INSERT INTO `webhooks` (`id`, `secret`, `target_url`) VALUES (6, 'anon-secret-6', 'https://example.local/webhook/anon-6');
