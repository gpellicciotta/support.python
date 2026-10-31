"""Unit tests for the SQL snapshot anonymizer and SQL tuple parsing in support_python.sql."""

from __future__ import annotations

import base64
import io
from pathlib import Path
import unittest

from support_python.crypto import get_standard_password_hash
from support_python.sql import (
    anonymize_sql_stream,
    anonymize_sql_string,
    format_sql_row_tuples,
    get_anonymized_user_info,
    parse_sql_row_tuples,
    transform_auth_applications,
    transform_auth_credentials,
    transform_auth_tokens,
    transform_auth_users,
    transform_counters_users,
    transform_counters_webhooks,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
AUTH_FIXTURE = FIXTURES_DIR / "realistic-auth-sample.sql"
COUNTERS_FIXTURE = FIXTURES_DIR / "realistic-counters-sample.sql"


class TestSqlAnonymizer(unittest.TestCase):
    def test_anonymized_user_info_deterministic(self):
        admin_name, admin_email = get_anonymized_user_info(0)
        self.assertEqual(admin_name, "Admin User")
        self.assertEqual(admin_email, "admin@anonymized.invalid")

        u1_name, u1_email = get_anonymized_user_info(42)
        self.assertEqual(u1_name, "Anonymized User 42")
        self.assertEqual(u1_email, "anon-user-42@anonymized.invalid")

        # Must be idempotent and identical on repeat calls
        u2_name, u2_email = get_anonymized_user_info(42)
        self.assertEqual(u1_name, u2_name)
        self.assertEqual(u1_email, u2_email)

    def test_parse_and_format_sql_tuples(self):
        raw = (
            r"(1, 'John Doe', 'john@example.com', '[\'admin\']', NULL), "
            r"(2, 'Jane \'Cool\' Doe', 'jane,cool@test.com', NULL, '2026-01-01 00:00:00')"
        )
        rows = parse_sql_row_tuples(raw)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], "1")
        self.assertEqual(rows[0][1], "'John Doe'")
        self.assertEqual(rows[0][2], "'john@example.com'")
        self.assertEqual(rows[0][4], "NULL")

        self.assertEqual(rows[1][0], "2")
        self.assertEqual(rows[1][2], "'jane,cool@test.com'")

        formatted = format_sql_row_tuples(rows)
        self.assertIn("(1, 'John Doe'", formatted)
        self.assertIn("(2, 'Jane \\'Cool\\' Doe'", formatted)

    def test_transform_auth_users(self):
        rows = [
            ["0", "'Original Admin'", "'admin@company.com'", "'[\\\"admin\\\"]'", "'2026-01-01'", "'2026-01-02'", "NULL"],
            ["15", "'Alice Wonderland'", "'alice@secret.org'", "NULL", "'2026-02-01'", "'2026-02-02'", "NULL"],
        ]
        modified = transform_auth_users(rows)
        self.assertEqual(modified, 2)
        # Admin check
        self.assertEqual(rows[0][1], "'Admin User'")
        self.assertEqual(rows[0][2], "'admin@anonymized.invalid'")
        self.assertEqual(rows[0][3], "'[\\\"admin\\\"]'")
        # User 15 check
        self.assertEqual(rows[1][1], "'Anonymized User 15'")
        self.assertEqual(rows[1][2], "'anon-user-15@anonymized.invalid'")

    def test_transform_auth_credentials(self):
        rows = [
            ["1", "'password'", "15", "'secret_hash_value_12345'", "'2026-01-01'", "'2026-01-01'", "NULL"],
            [
                "2",
                "'federated-id'",
                "15",
                "'google:https://accounts.google.com:real_sub_9999'",
                "'2026-01-01'",
                "'2026-01-01'",
                "NULL",
            ],
        ]
        modified = transform_auth_credentials(rows)
        self.assertEqual(modified, 2)
        # Password check
        self.assertNotEqual(rows[0][3], "'secret_hash_value_12345'")
        std_hash = get_standard_password_hash()
        b64_hash = base64.b64encode(std_hash.encode("ascii")).decode("ascii")
        self.assertEqual(rows[0][3], f"'{b64_hash}'")
        # Federated ID check
        self.assertNotIn("real_sub_9999", rows[1][3])
        expected_fed = base64.b64encode("google:https://accounts.google.com:anon-sub-15".encode("utf-8")).decode("ascii")
        self.assertEqual(rows[1][3], f"'{expected_fed}'")

    def test_transform_auth_tokens(self):
        rows = [
            ["101", "'session'", "15", "'real_session_token_xyz'", "'2026-01-01'", "'2026-01-01'", "NULL"],
        ]
        modified = transform_auth_tokens(rows)
        self.assertEqual(modified, 1)
        expected_token = base64.b64encode("anon-token-101".encode("utf-8")).decode("ascii")
        self.assertEqual(rows[0][3], f"'{expected_token}'")

    def test_transform_auth_applications(self):
        rows = [
            [
                "1",
                "'counters'",
                "'Counters App'",
                "'http://localhost:8010'",
                "'http://localhost:8010/logo.png'",
                "NULL",
                "'real_app_secret_hash'",
                "'2026-01-01'",
                "'2026-01-01'",
            ],
        ]
        modified = transform_auth_applications(rows)
        self.assertEqual(modified, 1)
        self.assertEqual(rows[0][6], "NULL")

    def test_counters_cross_repo_user_parity(self):
        rows = [
            ["1", "'Alice Local Name'", "'alice@old-email.com'", "NULL", "NULL", "'2026-01-01'", "'2026-01-01'", "NULL", "15"],
            ["2", "'Legacy Standalone'", "'legacy@old-email.com'", "NULL", "NULL", "'2026-01-01'", "'2026-01-01'", "NULL", "NULL"],
        ]
        modified = transform_counters_users(rows)
        self.assertEqual(modified, 2)
        auth_name, auth_email = get_anonymized_user_info(15)
        self.assertEqual(rows[0][1], f"'{auth_name}'")
        self.assertEqual(rows[0][2], f"'{auth_email}'")
        self.assertEqual(rows[0][8], "15")

        local_name, local_email = get_anonymized_user_info(2)
        self.assertEqual(rows[1][1], f"'{local_name}'")
        self.assertEqual(rows[1][2], f"'{local_email}'")

    def test_transform_counters_webhooks(self):
        rows = [
            [
                "5",
                "10",
                "15",
                "'https://my-private-site.com/webhook'",
                "'super_secret_key_999'",
                "1",
                "'2026-01-01'",
                "'2026-01-01'",
            ],
        ]
        modified = transform_counters_webhooks(rows)
        self.assertEqual(modified, 1)
        self.assertEqual(rows[0][3], "'https://example.local/webhook/anon-5'")
        self.assertEqual(rows[0][4], "'anon-secret-5'")

    def test_full_sql_dump_anonymization_auth(self):
        sample_sql = """-- Example Auth Sample Dump
CREATE TABLE IF NOT EXISTS `users` (`id` BIGINT NOT NULL, `name` VARCHAR(250), `email` VARCHAR(250));
INSERT INTO `users` VALUES (0, 'Admin User Real', 'admin@real.com', '["admin"]', '2026-01-01', '2026-01-01', NULL),
(1, 'Real Person', 'real@person.com', NULL, '2026-01-02', '2026-01-02', NULL);

INSERT INTO `credentials` VALUES (1, 'password', 1, 'real_pass_hash', '2026-01-02', '2026-01-02', NULL);
"""
        anon_sql, stats = anonymize_sql_string(sample_sql, app="auth")
        self.assertEqual(stats.get("users"), 2)
        self.assertEqual(stats.get("credentials"), 1)
        self.assertNotIn("Admin User Real", anon_sql)
        self.assertNotIn("real@person.com", anon_sql)
        self.assertNotIn("real_pass_hash", anon_sql)
        self.assertIn("Admin User", anon_sql)
        self.assertIn("admin@anonymized.invalid", anon_sql)
        self.assertIn("Anonymized User 1", anon_sql)
        self.assertIn("anon-user-1@anonymized.invalid", anon_sql)

    def test_realistic_auth_fixture_e2e(self):
        self.assertTrue(AUTH_FIXTURE.is_file(), f"Fixture file not found at {AUTH_FIXTURE}")
        with open(AUTH_FIXTURE, "r", encoding="utf-8") as in_f:
            out_buf = io.StringIO()
            stats = anonymize_sql_stream(in_f, out_buf, app="auth")
            anon_sql = out_buf.getvalue()

        # Check expected table transformation counts
        self.assertEqual(stats.get("users"), 3)
        self.assertEqual(stats.get("applications"), 2)
        self.assertEqual(stats.get("credentials"), 2)
        self.assertEqual(stats.get("tokens"), 1)

        # Confirm all sensitive PII and secrets were removed
        self.assertNotIn("Alice Wonderland", anon_sql)
        self.assertNotIn("Bob Builder", anon_sql)
        self.assertNotIn("admin@example.test", anon_sql)
        self.assertNotIn("alice.wonderland@corporate.example", anon_sql)
        self.assertNotIn("bob.builder@personal.example", anon_sql)
        self.assertNotIn("real_pbkdf2_hash_alice_secret", anon_sql)
        self.assertNotIn("10987654321", anon_sql)
        self.assertNotIn("secret_session_token_xyz_123", anon_sql)
        self.assertNotIn("secret_app_hash_9999", anon_sql)

        # Confirm anonymized data exists
        self.assertIn("Admin User", anon_sql)
        self.assertIn("admin@anonymized.invalid", anon_sql)
        self.assertIn("Anonymized User 1", anon_sql)
        self.assertIn("anon-user-1@anonymized.invalid", anon_sql)
        self.assertIn("Anonymized User 2", anon_sql)
        self.assertIn("anon-user-2@anonymized.invalid", anon_sql)

        # Confirm token and federated-id are masked in base64
        expected_token = base64.b64encode(b"anon-token-100").decode("ascii")
        self.assertIn(expected_token, anon_sql)
        expected_sub = base64.b64encode(b"google:https://accounts.google.com:anon-sub-2").decode("ascii")
        self.assertIn(expected_sub, anon_sql)

        # Confirm non-sensitive settings and grants remain intact
        self.assertIn("theme", anon_sql)
        self.assertIn("dark", anon_sql)
        self.assertIn("application-grants", anon_sql)

    def test_realistic_counters_fixture_e2e(self):
        self.assertTrue(COUNTERS_FIXTURE.exists(), f"Missing fixture file: {COUNTERS_FIXTURE}")
        out_buf = io.StringIO()
        with open(COUNTERS_FIXTURE, "r", encoding="utf-8") as f:
            stats = anonymize_sql_stream(f, out_buf, app="counters")
            anon_sql = out_buf.getvalue()

        self.assertEqual(stats.get("users"), 3)
        self.assertEqual(stats.get("tokens"), 2)
        self.assertEqual(stats.get("webhooks"), 1)

        self.assertNotIn("Alice Real Name", anon_sql)
        self.assertNotIn("Bob Real Person", anon_sql)
        self.assertNotIn("alice.real@company.example", anon_sql)
        self.assertNotIn("bob.builder@personal.example", anon_sql)

        self.assertIn("Anonymized User 15", anon_sql)
        self.assertIn("anon-user-15@anonymized.invalid", anon_sql)
        self.assertIn("Anonymized User 22", anon_sql)
        self.assertIn("anon-user-22@anonymized.invalid", anon_sql)

    def test_custom_column_lists_and_syntax_variations(self):
        sql = """
INSERT IGNORE INTO `auth`.`users` (`email`, `id`, `name`) VALUES ('secret@corp.org', 10, 'Top Secret User');
REPLACE INTO `credentials` (`data`, `type`, `user-id`) VALUES ('secret_pass_val', 'password', 10);
"""
        anon_sql, stats = anonymize_sql_string(sql, app="auth")
        self.assertEqual(stats.get("users"), 1)
        self.assertEqual(stats.get("credentials"), 1)
        self.assertNotIn("secret@corp.org", anon_sql)
        self.assertNotIn("Top Secret User", anon_sql)
        self.assertNotIn("secret_pass_val", anon_sql)
        self.assertIn("anon-user-10@anonymized.invalid", anon_sql)
        self.assertIn("Anonymized User 10", anon_sql)

    def test_custom_transformers_callback(self):
        sql = """INSERT INTO `custom_sensitive` VALUES (1, 'super-secret-key-1234');\n"""

        def custom_mask(rows: list[list[str]], col_names: list[str] | None) -> int:
            for row in rows:
                row[1] = "'masked-secret'"
            return len(rows)

        anon_sql, stats = anonymize_sql_string(
            sql,
            custom_transformers={"custom_sensitive": custom_mask},
        )
        self.assertEqual(stats.get("custom_sensitive"), 1)
        self.assertNotIn("super-secret-key-1234", anon_sql)
        self.assertIn("'masked-secret'", anon_sql)

    def test_skips_privileged_statements(self):
        sql = """SET @@SESSION.SQL_LOG_BIN= 0;\nSET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '';\nSELECT 1;\n"""
        anon_sql, stats = anonymize_sql_string(sql, app="auth")
        self.assertNotIn("SQL_LOG_BIN", anon_sql)
        self.assertNotIn("GTID_PURGED", anon_sql)
        self.assertIn("SELECT 1;", anon_sql)


if __name__ == "__main__":
    unittest.main()
