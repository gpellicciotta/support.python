/*!40101 SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
INSERT INTO `users` VALUES (0, 'Admin User', 'admin@anonymized.invalid', '["admin"]', '2026-01-01', '2026-01-01', NULL);
INSERT INTO `users` (`email`, `id`, `name`) VALUES ('anon-user-10@anonymized.invalid', 10, 'Anonymized User 10');
INSERT INTO `credentials` VALUES (1, 'password', 10, 'MDEwMjAzMDQwNTA2MDcwODA5MGEwYjBjMGQwZTBmMTAxMTEyMTMxNDE1MTYxNzE4MTkxYTFiMWMxZDFlMWYyMDpkNjUyZWVhMGM0MmIwYTQ3MDU4OGJiYWNjNjk0YWRhZTZmYmI0MDA2N2Y1YTMwMGYxZjNhYTA2MzYzYzY5Yzlm', '2026-01-02', '2026-01-02', NULL);
REPLACE INTO `credentials` (`data`, `type`, `user_id`) VALUES ('MDEwMjAzMDQwNTA2MDcwODA5MGEwYjBjMGQwZTBmMTAxMTEyMTMxNDE1MTYxNzE4MTkxYTFiMWMxZDFlMWYyMDpkNjUyZWVhMGM0MmIwYTQ3MDU4OGJiYWNjNjk0YWRhZTZmYmI0MDA2N2Y1YTMwMGYxZjNhYTA2MzYzYzY5Yzlm', 'password', 10);
INSERT INTO `tokens` VALUES (101, 'session', 10, 'YW5vbi10b2tlbi0xMDE=', '2026-01-02', '2026-01-02', NULL);
INSERT INTO `tokens` (`data`, `id`) VALUES ('YW5vbi10b2tlbi0xMDI=', 102);
INSERT INTO `applications` VALUES (1, 'counters', 'Counters', 'http://localhost', NULL, NULL, NULL, '2026-01-01', '2026-01-01');
INSERT INTO `applications` (`app_secret`, `id`) VALUES (NULL, 2);
