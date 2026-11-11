INSERT INTO `users` VALUES (0, 'Admin User Real', 'admin@real.com', '["admin"]', '2026-01-01', '2026-01-01', NULL);
INSERT INTO `users` (`email`, `id`, `name`) VALUES ('custom@corp.org', 10, 'Custom User');
INSERT INTO `credentials` VALUES (1, 'password', 10, 'secret_pass_hash', '2026-01-02', '2026-01-02', NULL);
REPLACE INTO `credentials` (`data`, `type`, `user_id`) VALUES ('secret_pass_val', 'password', 10);
INSERT INTO `tokens` VALUES (101, 'session', 10, 'session_token_xyz', '2026-01-02', '2026-01-02', NULL);
INSERT INTO `tokens` (`data`, `id`) VALUES ('token_val', 102);
INSERT INTO `applications` VALUES (1, 'counters', 'Counters', 'http://localhost', NULL, NULL, 'app_secret_val', '2026-01-01', '2026-01-01');
INSERT INTO `applications` (`app_secret`, `id`) VALUES ('secret_hash', 2);
