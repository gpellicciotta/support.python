"""Unit tests for the SQL snapshot anonymizer and SQL tuple parsing in support_python.sql."""

from __future__ import annotations

import base64
import io
from pathlib import Path
import unittest

from support_python.crypto import DEFAULT_TEST_PASSWORD, get_standard_password_hash
from support_python.sql import (
    KEEP,
    ColumnRule,
    RowView,
    anonymize_sql_stream,
    anonymize_sql_string,
    column_index,
    column_rules_transformer,
    format_sql_row_tuples,
    get_anonymized_user_info,
    parse_sql_row_tuples,
    sql_int,
    sql_literal,
    sql_value,
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

    def test_sql_value_and_sql_literal_round_trip(self):
        self.assertEqual(sql_literal(None), "NULL")
        self.assertIsNone(sql_value("NULL"))
        self.assertIsNone(sql_value("null"))
        self.assertIsNone(sql_value("Null"))
        self.assertIsNone(sql_value("  NULL  "))

        self.assertEqual(sql_literal(42), "42")
        self.assertEqual(sql_literal(0), "0")
        self.assertEqual(sql_literal(-15), "-15")
        self.assertEqual(sql_value("42"), "42")

        self.assertEqual(sql_literal("NULL"), "'NULL'")
        self.assertEqual(sql_value("'NULL'"), "NULL")

        self.assertEqual(sql_literal(""), "''")
        self.assertEqual(sql_value("''"), "")

        samples = [
            "simple text",
            "O'Connor",
            r"path\to\file",
            r"quotes 'and' \backslashes\\",
            r"'already quoted'",
            "double \"quotes\" and 'single'",
            "line1\nline2\ttab",
        ]
        for sample in samples:
            lit = sql_literal(sample)
            self.assertEqual(sql_value(lit), sample)

        with self.assertRaises(TypeError):
            sql_literal(True)
        with self.assertRaises(TypeError):
            sql_literal([1, 2, 3])

    def test_sql_int(self):
        self.assertEqual(sql_int("42"), 42)
        self.assertEqual(sql_int("0"), 0)
        self.assertEqual(sql_int("-7"), -7)
        self.assertEqual(sql_int("  42  "), 42)
        self.assertEqual(sql_int("'42'"), 42)
        self.assertIsNone(sql_int("NULL"))
        self.assertIsNone(sql_int("null"))
        self.assertIsNone(sql_int("not_a_number"))
        self.assertIsNone(sql_int("12.34"))
        self.assertIsNone(sql_int(""))

    def test_column_index(self):
        cols = ["id", "auth_user_id", "`target-url`", "'Secret'"]
        self.assertEqual(column_index(cols, "AUTH_USER_ID"), 1)
        self.assertEqual(column_index(cols, "auth-user-id"), 1)
        self.assertEqual(column_index(cols, "`auth_user_id`"), 1)
        self.assertEqual(column_index(cols, "target_url"), 2)
        self.assertEqual(column_index(cols, "target-url"), 2)
        self.assertEqual(column_index(cols, "secret"), 3)
        self.assertEqual(column_index(cols, "SECRET"), 3)

        self.assertIsNone(column_index(cols, "missing"))
        self.assertIsNone(column_index(cols, "missing", position=5))

        self.assertEqual(column_index(None, "anything", position=2), 2)
        self.assertIsNone(column_index(None, "anything", position=None))

    def test_row_view(self):
        row = ["1", r"'Alice \'Cool\' Doe'", "'alice@example.com'", "42", "NULL"]
        cols = ["id", "name", "email", "auth-user-id", "optional_data"]
        view = RowView(row, col_names=cols)
        self.assertTrue(view.has("name"))
        self.assertTrue(view.has("AUTH-USER-ID"))
        self.assertFalse(view.has("missing"))

        self.assertEqual(view.raw("name"), r"'Alice \'Cool\' Doe'")
        self.assertEqual(view.raw("auth_user_id"), "42")
        self.assertEqual(view.raw("optional_data"), "NULL")
        self.assertIsNone(view.raw("missing"))

        self.assertEqual(view.text("name"), "Alice 'Cool' Doe")
        self.assertIsNone(view.text("optional_data"))
        self.assertIsNone(view.text("missing"))

        self.assertEqual(view.int("id"), 1)
        self.assertEqual(view.int("auth_user_id"), 42)
        self.assertIsNone(view.int("name"))
        self.assertIsNone(view.int("optional_data"))
        self.assertIsNone(view.int("missing"))

        view_pos = RowView(row, positions={"id": 0, "name": 1, "auth-user-id": 3})
        self.assertEqual(view_pos.text("name"), "Alice 'Cool' Doe")
        self.assertEqual(view_pos.int("auth_user_id"), 42)
        self.assertIsNone(view_pos.text("missing"))

    def test_column_rules_transformer_unit(self):
        rows = [["1", "'Alice'", "'secret1'"], ["2", "'Bob'", "'secret2'"]]
        transformer = column_rules_transformer(
            {"name": lambda r: KEEP, "secret": lambda r: "masked"},
            positions={"id": 0, "name": 1, "secret": 2},
        )
        count = transformer(rows, None)
        self.assertEqual(count, 2)
        self.assertEqual(rows[0][1], "'Alice'")
        self.assertEqual(rows[0][2], "'masked'")
        self.assertEqual(rows[1][1], "'Bob'")
        self.assertEqual(rows[1][2], "'masked'")

        rows = [["'original'", "'old'"]]
        transformer = column_rules_transformer(
            {
                "col1": lambda r: "rewritten",
                "col2": lambda r: f"saw-{r.text('col1')}",
            },
            positions={"col1": 0, "col2": 1},
        )
        transformer(rows, None)
        self.assertEqual(rows[0][0], "'rewritten'")
        self.assertEqual(rows[0][1], "'saw-original'")

        rows = [["1", "'test'"]]
        transformer = column_rules_transformer({"name": lambda r: KEEP}, positions={"name": 1})
        count = transformer(rows, None)
        self.assertEqual(count, 1)
        self.assertEqual(rows[0][1], "'test'")

        rows = [["1", "'test'"]]
        transformer = column_rules_transformer({"other": lambda r: "new"})
        count = transformer(rows, ["id", "val"])
        self.assertEqual(count, 0)
        self.assertEqual(rows[0], ["1", "'test'"])

        def dummy_rule(r: RowView) -> object:
            return KEEP

        rule_fn: ColumnRule = dummy_rule
        self.assertIs(rule_fn(RowView([])), KEEP)

    def test_declarative_builder_auth_and_counters_equivalence(self):
        auth_users_transformer = column_rules_transformer(
            {
                "name": lambda r: get_anonymized_user_info(r.int("id") or 0)[0],
                "email": lambda r: get_anonymized_user_info(r.int("id") or 0)[1],
            },
            positions={"id": 0, "name": 1, "email": 2},
        )

        def make_credentials_transformer(custom_password=None):
            std_hash = get_standard_password_hash(custom_password or DEFAULT_TEST_PASSWORD)
            b64_password_hash = base64.b64encode(std_hash.encode("ascii")).decode("ascii")

            def transform_data(row: RowView) -> object:
                cred_type = (row.text("type") or "password").lower()
                user_id = row.int("user-id") or 0
                if cred_type == "password":
                    return b64_password_hash
                elif cred_type == "federated-id":
                    orig_data = row.text("data") or ""
                    try:
                        decoded = base64.b64decode(orig_data, validate=True).decode("utf-8", errors="replace")
                        if ":" in decoded:
                            orig_data = decoded
                    except Exception:
                        pass
                    if ":" in orig_data:
                        prefix_part, _ = orig_data.rsplit(":", 1)
                        fed_val = f"{prefix_part}:anon-sub-{user_id}"
                    else:
                        fed_val = f"google:anon-sub-{user_id}"
                    return base64.b64encode(fed_val.encode("utf-8")).decode("ascii")
                return KEEP

            return column_rules_transformer(
                {"data": transform_data},
                positions={"type": 1, "user-id": 2, "data": 3},
            )

        auth_tokens_transformer = column_rules_transformer(
            {
                "data": lambda r: base64.b64encode(f"anon-token-{r.int('id') or 0}".encode("utf-8")).decode("ascii"),
            },
            positions={"id": 0, "data": 3},
        )

        auth_applications_transformer = column_rules_transformer(
            {
                "app-secret": lambda r: None,
            },
            positions={"app-secret": 6},
        )

        auth_custom = {
            "users": auth_users_transformer,
            "credentials": make_credentials_transformer(),
            "tokens": auth_tokens_transformer,
            "applications": auth_applications_transformer,
        }

        # Auth Fixture E2E equivalence test (multi-table with and without column lists)
        with open(AUTH_FIXTURE, "r", encoding="utf-8") as in_f:
            auth_fixture_sql = in_f.read()
        expected_sql, expected_stats = anonymize_sql_string(auth_fixture_sql, app="auth")
        built_sql, built_stats = anonymize_sql_string(auth_fixture_sql, app="", custom_transformers=auth_custom)
        self.assertEqual(built_sql, expected_sql)
        self.assertEqual(built_stats, expected_stats)

        # Inline multi-table dump test with and without column lists for auth
        inline_auth_sql = """
INSERT INTO `users` VALUES (0, 'Admin User Real', 'admin@real.com', '["admin"]', '2026-01-01', '2026-01-01', NULL);
INSERT INTO `users` (`email`, `id`, `name`) VALUES ('custom@corp.org', 10, 'Custom User');
INSERT INTO `credentials` VALUES (1, 'password', 10, 'secret_pass_hash', '2026-01-02', '2026-01-02', NULL);
REPLACE INTO `credentials` (`data`, `type`, `user_id`) VALUES ('secret_pass_val', 'password', 10);
INSERT INTO `tokens` VALUES (101, 'session', 10, 'session_token_xyz', '2026-01-02', '2026-01-02', NULL);
INSERT INTO `tokens` (`data`, `id`) VALUES ('token_val', 102);
INSERT INTO `applications` VALUES (1, 'counters', 'Counters', 'http://localhost', NULL, NULL, 'app_secret_val', '2026-01-01', '2026-01-01');
INSERT INTO `applications` (`app_secret`, `id`) VALUES ('secret_hash', 2);
"""
        exp_inline, exp_inline_stats = anonymize_sql_string(inline_auth_sql, app="auth")
        built_inline, built_inline_stats = anonymize_sql_string(inline_auth_sql, app="", custom_transformers=auth_custom)
        self.assertEqual(built_inline, exp_inline)
        self.assertEqual(built_inline_stats, exp_inline_stats)

        # Counters rules
        def _counters_user_info(row: RowView) -> tuple[str, str]:
            auth_id = row.int("auth-user-id")
            if auth_id is None:
                auth_id = row.int("id") or 0
            return get_anonymized_user_info(auth_id)

        counters_users_transformer = column_rules_transformer(
            {
                "name": lambda r: _counters_user_info(r)[0],
                "email": lambda r: _counters_user_info(r)[1],
            },
            positions={"id": 0, "name": 1, "email": 2, "auth-user-id": 8},
        )

        counters_webhooks_transformer = column_rules_transformer(
            {
                "target-url": lambda r: f"https://example.local/webhook/anon-{r.int('id') or 0}",
                "secret": lambda r: f"anon-secret-{r.int('id') or 0}",
            },
            positions={"id": 0, "target-url": 3, "secret": 4},
        )

        counters_custom = {
            "users": counters_users_transformer,
            "tokens": auth_tokens_transformer,
            "webhooks": counters_webhooks_transformer,
        }

        # Counters Fixture E2E equivalence test
        with open(COUNTERS_FIXTURE, "r", encoding="utf-8") as in_f:
            counters_fixture_sql = in_f.read()
        exp_counters_sql, exp_counters_stats = anonymize_sql_string(counters_fixture_sql, app="counters")
        built_counters_sql, built_counters_stats = anonymize_sql_string(
            counters_fixture_sql, app="", custom_transformers=counters_custom
        )
        self.assertEqual(built_counters_sql, exp_counters_sql)
        self.assertEqual(built_counters_stats, exp_counters_stats)

        # Inline multi-table dump test with and without column lists for counters
        inline_counters_sql = """
INSERT INTO `users` VALUES (1, 'Alice Real Name', 'alice@old-email.com', NULL, NULL, '2026-01-01', '2026-01-01', NULL, 15);
INSERT INTO `users` (`auth_user_id`, `email`, `id`, `name`) VALUES (NULL, 'legacy@old-email.com', 2, 'Legacy Standalone');
INSERT INTO `tokens` VALUES (101, 'session', 15, 'session_token_xyz', '2026-01-02', '2026-01-02', NULL);
INSERT INTO `webhooks` VALUES (5, 10, 15, 'https://my-site.com/hook', 'super_secret', 1, '2026-01-01', '2026-01-01');
INSERT INTO `webhooks` (`id`, `secret`, `target_url`) VALUES (6, 'webhook_sec', 'https://other-site.com/hook');
"""
        exp_inline_c, exp_inline_c_stats = anonymize_sql_string(inline_counters_sql, app="counters")
        built_inline_c, built_inline_c_stats = anonymize_sql_string(
            inline_counters_sql, app="", custom_transformers=counters_custom
        )
        self.assertEqual(built_inline_c, exp_inline_c)
        self.assertEqual(built_inline_c_stats, exp_inline_c_stats)


if __name__ == "__main__":
    unittest.main()
