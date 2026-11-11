"""Unit tests for the SQL snapshot anonymizer and SQL tuple parsing in support_python.sql."""

from __future__ import annotations

import base64
import inspect
import io
import json
from pathlib import Path
from typing import Optional
import unittest

from support_python import sql
from support_python.crypto import DEFAULT_TEST_PASSWORD, get_standard_password_hash
from support_python.sql import (
    KEEP,
    ColumnRule,
    RowView,
    TableTransformer,
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
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SQL_FIXTURES_DIR = FIXTURES_DIR / "sql"
AUTH_FIXTURE = FIXTURES_DIR / "realistic-auth-sample.sql"
COUNTERS_FIXTURE = FIXTURES_DIR / "realistic-counters-sample.sql"


_TEST_SALT = bytes(range(1, 33))


def _auth_transformers(custom_password: Optional[str] = None) -> dict[str, TableTransformer]:
    """Build the rules the removed ``app="auth"`` profile applied, as a local transformers map."""
    std_hash = get_standard_password_hash(custom_password or DEFAULT_TEST_PASSWORD, salt=_TEST_SALT)
    b64_password_hash = base64.b64encode(std_hash.encode("ascii")).decode("ascii")

    def credential_data(row: RowView) -> object:
        cred_type = (row.text("type") or "password").lower()
        user_id = row.int("user-id") or 0
        if cred_type == "password":
            return b64_password_hash
        if cred_type == "federated-id":
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

    return {
        "users": column_rules_transformer(
            {
                "name": lambda r: get_anonymized_user_info(r.int("id") or 0)[0],
                "email": lambda r: get_anonymized_user_info(r.int("id") or 0)[1],
            },
            positions={"id": 0, "name": 1, "email": 2},
        ),
        "credentials": column_rules_transformer({"data": credential_data}, positions={"type": 1, "user-id": 2, "data": 3}),
        "tokens": _tokens_transformer(),
        "applications": column_rules_transformer({"app-secret": lambda r: None}, positions={"app-secret": 6}),
    }


def _tokens_transformer() -> TableTransformer:
    return column_rules_transformer(
        {"data": lambda r: base64.b64encode(f"anon-token-{r.int('id') or 0}".encode("utf-8")).decode("ascii")},
        positions={"id": 0, "data": 3},
    )


def _counters_transformers() -> dict[str, TableTransformer]:
    """Build the rules the removed ``app="counters"`` profile applied, as a local transformers map."""

    def user_info(row: RowView) -> tuple[str, str]:
        auth_id = row.int("auth-user-id")
        if auth_id is None:
            auth_id = row.int("id") or 0
        return get_anonymized_user_info(auth_id)

    return {
        "users": column_rules_transformer(
            {"name": lambda r: user_info(r)[0], "email": lambda r: user_info(r)[1]},
            positions={"id": 0, "name": 1, "email": 2, "auth-user-id": 8},
        ),
        "tokens": _tokens_transformer(),
        "webhooks": column_rules_transformer(
            {
                "target-url": lambda r: f"https://example.local/webhook/anon-{r.int('id') or 0}",
                "secret": lambda r: f"anon-secret-{r.int('id') or 0}",
            },
            positions={"id": 0, "target-url": 3, "secret": 4},
        ),
    }


def _read_fixture(name: str) -> str:
    return (SQL_FIXTURES_DIR / name).read_text(encoding="utf-8")


def _golden_stats(name: str) -> dict[str, int]:
    return json.loads(_read_fixture(f"{name}-golden-stats.json"))


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

    def test_full_sql_dump_anonymization_auth(self):
        sample_sql = """-- Example Auth Sample Dump
CREATE TABLE IF NOT EXISTS `users` (`id` BIGINT NOT NULL, `name` VARCHAR(250), `email` VARCHAR(250));
INSERT INTO `users` VALUES (0, 'Admin User Real', 'admin@real.com', '["admin"]', '2026-01-01', '2026-01-01', NULL),
(1, 'Real Person', 'real@person.com', NULL, '2026-01-02', '2026-01-02', NULL);

INSERT INTO `credentials` VALUES (1, 'password', 1, 'real_pass_hash', '2026-01-02', '2026-01-02', NULL);
"""
        anon_sql, stats = anonymize_sql_string(sample_sql, _auth_transformers())
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
            stats = anonymize_sql_stream(in_f, out_buf, _auth_transformers())
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
            stats = anonymize_sql_stream(f, out_buf, _counters_transformers())
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
        anon_sql, stats = anonymize_sql_string(sql, _auth_transformers())
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

        anon_sql, stats = anonymize_sql_string(sql, {"custom_sensitive": custom_mask})
        self.assertEqual(stats.get("custom_sensitive"), 1)
        self.assertNotIn("super-secret-key-1234", anon_sql)
        self.assertIn("'masked-secret'", anon_sql)

    def test_golden_outputs_match_removed_schema_profiles(self):
        cases = [
            ("auth-sample", _read_fixture("../realistic-auth-sample.sql"), _auth_transformers()),
            ("auth-inline", _read_fixture("auth-inline.sql"), _auth_transformers()),
            ("counters-sample", _read_fixture("../realistic-counters-sample.sql"), _counters_transformers()),
            ("counters-inline", _read_fixture("counters-inline.sql"), _counters_transformers()),
        ]
        for name, source, transformers in cases:
            with self.subTest(name):
                out, stats = anonymize_sql_string(source, transformers)
                self.assertEqual(out, _read_fixture(f"{name}-golden.sql"))
                self.assertEqual(stats, _golden_stats(name))

    def test_custom_password_flows_through_local_credentials_rule(self):
        sql_text = "INSERT INTO `credentials` VALUES (1, 'password', 1, 'old', '2026-01-02', '2026-01-02', NULL);\n"
        out, _ = anonymize_sql_string(sql_text, _auth_transformers("pw-1"))
        b64 = base64.b64encode(get_standard_password_hash("pw-1", salt=_TEST_SALT).encode("ascii")).decode("ascii")
        self.assertIn(b64, out)

    def test_transformers_argument_is_required(self):
        with self.assertRaises(TypeError):
            anonymize_sql_string("SELECT 1;\n")  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            anonymize_sql_stream(io.StringIO(""), io.StringIO())  # type: ignore[call-arg]

    def test_removed_parameters_are_rejected(self):
        for removed in ("app", "custom_password", "custom_transformers"):
            with self.subTest(removed):
                self.assertNotIn(removed, inspect.signature(anonymize_sql_stream).parameters)
                self.assertNotIn(removed, inspect.signature(anonymize_sql_string).parameters)
        with self.assertRaises(TypeError):
            anonymize_sql_string("SELECT 1;\n", {}, app="auth")  # type: ignore[call-arg]

    def test_empty_transformers_leave_tables_untouched(self):
        sql_text = "INSERT INTO `users` VALUES (1, 'Real Person', 'real@person.com');\n"
        out, stats = anonymize_sql_string(sql_text, {})
        self.assertEqual(stats, {})
        self.assertIn("real@person.com", out)

    def test_schema_transformers_are_removed(self):
        removed = [
            "transform_auth_users",
            "transform_auth_credentials",
            "transform_auth_applications",
            "transform_auth_tokens",
            "transform_counters_users",
            "transform_counters_webhooks",
        ]
        for name in removed:
            with self.subTest(name):
                self.assertFalse(hasattr(sql, name))
                self.assertNotIn(name, sql.__all__)

    def test_skips_privileged_statements(self):
        sql = """SET @@SESSION.SQL_LOG_BIN= 0;\nSET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '';\nSELECT 1;\n"""
        anon_sql, stats = anonymize_sql_string(sql, {})
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


if __name__ == "__main__":
    unittest.main()
