INSERT INTO `users` VALUES (1, 'Alice Real Name', 'alice@old-email.com', NULL, NULL, '2026-01-01', '2026-01-01', NULL, 15);
INSERT INTO `users` (`auth_user_id`, `email`, `id`, `name`) VALUES (NULL, 'legacy@old-email.com', 2, 'Legacy Standalone');
INSERT INTO `tokens` VALUES (101, 'session', 15, 'session_token_xyz', '2026-01-02', '2026-01-02', NULL);
INSERT INTO `webhooks` VALUES (5, 10, 15, 'https://my-site.com/hook', 'super_secret', 1, '2026-01-01', '2026-01-01');
INSERT INTO `webhooks` (`id`, `secret`, `target_url`) VALUES (6, 'webhook_sec', 'https://other-site.com/hook');
