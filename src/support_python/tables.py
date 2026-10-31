"""Tabular rendering, output formatting, and JSON serialization utilities.

Provides clean tabular alignment for console displays and automatic output format
switching (table vs. JSON) for CLI tools.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime
import json
from typing import Any, Optional, Sequence, TextIO


def json_serial(obj: Any) -> Any:
    """Serialize objects not handled by default JSON encoders into serializable representations.

    Supports objects implementing ``to_wire()``, dataclass instances, datetime objects,
    sets/frozensets, and objects with a ``.value`` attribute (like enums).

    Args:
        obj: The object instance to serialize.

    Returns:
        JSON-serializable representation (e.g. dict, list, string, or primitive value).

    Raises:
        TypeError: If the object type cannot be serialized.
    """
    if hasattr(obj, "to_wire") and callable(getattr(obj, "to_wire")):
        return obj.to_wire()
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if hasattr(obj, "value"):
        return obj.value
    raise TypeError(f"Type {type(obj)} not serializable")


def format_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """Format tabular data cleanly with aligned columns and separator bars.

    Calculates dynamic column widths based on maximum length among header and cell values.

    Args:
        headers: Column header title strings.
        rows: Sequence of table row records containing cell values.

    Returns:
        Formatted multi-line table string, or ``"(empty)"`` if rows is empty.
    """
    if not rows:
        return "(empty)"
    str_rows = [[str(col) if col is not None else "" for col in row] for row in rows]
    col_widths = [len(str(h)) for h in headers]
    for row in str_rows:
        for i, col in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(col))
            else:
                col_widths.append(len(col))

    header_line = "  ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
    sep_line = "  ".join("-" * col_widths[i] for i in range(len(headers)))
    data_lines = ["  ".join(col.ljust(col_widths[i]) for i, col in enumerate(row)) for row in str_rows]
    return "\n".join([header_line, sep_line] + data_lines)


def render_output(data: Any, output_format: str = "table", file: Optional[TextIO] = None) -> None:
    """Render structured data as JSON or formatted human-readable text/table output.

    Supports rendering lists of dataclasses or dictionaries, single dataclasses, dictionaries,
    or primitive objects.

    Args:
        data: Structured data object to display.
        output_format: Output format identifier, either ``"json"`` or ``"table"``. Defaults to ``"table"``.
        file: Destination text stream to write to. Defaults to standard output if None.

    Returns:
        None.
    """
    if output_format == "json":
        print(json.dumps(data, default=json_serial, indent=2), file=file)
        return

    # Human-readable table / text rendering
    if isinstance(data, (list, tuple)):
        if not data:
            print("(empty)", file=file)
            return
        first = data[0]
        if dataclasses.is_dataclass(first) and not isinstance(first, type):
            fields = [f.name for f in dataclasses.fields(first)]
            rows = [[getattr(item, f) for f in fields] for item in data]
            print(format_table(fields, rows), file=file)
        elif isinstance(first, dict):
            fields = list(first.keys())
            rows = [[item.get(k) for k in fields] for item in data]
            print(format_table([str(k) for k in fields], rows), file=file)
        else:
            for item in data:
                print(item, file=file)
    elif dataclasses.is_dataclass(data) and not isinstance(data, type):
        fields = [f.name for f in dataclasses.fields(data)]
        rows = [[f, getattr(data, f)] for f in fields]
        print(format_table(["Property", "Value"], rows), file=file)
    elif isinstance(data, dict):
        rows = [[k, v] for k, v in data.items()]
        print(format_table(["Key", "Value"], rows), file=file)
    else:
        print(data, file=file)


__all__ = ["format_table", "json_serial", "render_output"]
