"""Tests for support_python.tables module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import io
import json
import unittest

from support_python.tables import format_table, json_serial, render_output


@dataclass
class SampleUser:
    id: int
    name: str
    email: str


@dataclass
class SampleWireToken:
    id: int
    code: str

    def to_wire(self):
        return {"id": self.id, "authorization-code": self.code}

    @classmethod
    def from_wire(cls, data):
        return cls(id=data["id"], code=data["authorization-code"])


class SampleEnum(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class TablesTests(unittest.TestCase):
    def test_format_table_empty(self) -> None:
        self.assertEqual(format_table(["ID", "Name"], []), "(empty)")

    def test_format_table_with_rows(self) -> None:
        headers = ["ID", "Name", "Status"]
        rows = [
            [1, "Alice", "Active"],
            [22, "Bob", None],
        ]
        result = format_table(headers, rows)
        lines = result.splitlines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0], "ID  Name   Status")
        self.assertEqual(lines[1], "--  -----  ------")
        self.assertEqual(lines[2], "1   Alice  Active")
        self.assertEqual(lines[3], "22  Bob          ")

    def test_json_serial_supported_types(self) -> None:
        user = SampleUser(1, "Alice", "alice@example.com")
        self.assertEqual(json_serial(user), {"id": 1, "name": "Alice", "email": "alice@example.com"})

        dt = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(json_serial(dt), "2026-09-18T12:00:00+00:00")

        self.assertEqual(json_serial(SampleEnum.ACTIVE), "active")
        self.assertEqual(sorted(json_serial({"a", "b"})), ["a", "b"])

        wire_token = SampleWireToken(10, "code-123")
        self.assertEqual(json_serial(wire_token), {"id": 10, "authorization-code": "code-123"})

        with self.assertRaises(TypeError):
            json_serial(object())

    def test_render_output_json(self) -> None:
        buffer = io.StringIO()
        user = SampleUser(1, "Alice", "alice@example.com")
        render_output(user, output_format="json", file=buffer)
        data = json.loads(buffer.getvalue())
        self.assertEqual(data, {"id": 1, "name": "Alice", "email": "alice@example.com"})

    def test_render_output_table_dataclass_list(self) -> None:
        buffer = io.StringIO()
        users = [
            SampleUser(1, "Alice", "alice@test.com"),
            SampleUser(2, "Bob", "bob@test.com"),
        ]
        render_output(users, output_format="table", file=buffer)
        output = buffer.getvalue()
        self.assertIn("id  name   email", output)
        self.assertIn("1   Alice  alice@test.com", output)

    def test_render_output_table_single_dataclass(self) -> None:
        buffer = io.StringIO()
        user = SampleUser(1, "Alice", "alice@test.com")
        render_output(user, output_format="table", file=buffer)
        output = buffer.getvalue()
        self.assertIn("Property  Value", output)
        self.assertIn("name      Alice", output)

    def test_render_output_table_dict_list(self) -> None:
        buffer = io.StringIO()
        items = [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]
        render_output(items, output_format="table", file=buffer)
        output = buffer.getvalue()
        self.assertIn("id  val", output)
        self.assertIn("1   a", output)

    def test_render_output_table_dict(self) -> None:
        buffer = io.StringIO()
        data = {"key1": "val1", "key2": "val2"}
        render_output(data, output_format="table", file=buffer)
        output = buffer.getvalue()
        self.assertIn("Key   Value", output)
        self.assertIn("key1  val1", output)

    def test_render_output_empty_list(self) -> None:
        buffer = io.StringIO()
        render_output([], output_format="table", file=buffer)
        self.assertEqual(buffer.getvalue().strip(), "(empty)")


if __name__ == "__main__":
    unittest.main()
