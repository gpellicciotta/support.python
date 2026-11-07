"""Unit and integration tests for support_python.files."""

from __future__ import annotations

import os
from pathlib import Path
import stat
import sys
import threading
from unittest import mock

import pytest

from support_python import (
    atomic_replace,
    atomic_write_text,
    read_text_retrying,
)
import support_python.files as files


def test_atomic_write_text_creates_and_overwrites_file(tmp_path: Path) -> None:
    target = tmp_path / "sample.txt"
    assert not target.exists()

    atomic_write_text(target, "first version\nsecond line\n")
    assert target.is_file()
    assert target.read_text(encoding="utf-8") == "first version\nsecond line\n"

    atomic_write_text(target, "overwritten content")
    assert target.read_text(encoding="utf-8") == "overwritten content"


def test_atomic_write_text_cleans_up_temp_file_on_write_failure(tmp_path: Path) -> None:
    target = tmp_path / "intact.txt"
    target.write_text("original content", encoding="utf-8")

    with pytest.raises(TypeError):
        atomic_write_text(target, 12345)  # type: ignore[arg-type]

    assert target.read_text(encoding="utf-8") == "original content"
    assert list(tmp_path.iterdir()) == [target]

    with (
        mock.patch.object(files, "atomic_replace", side_effect=RuntimeError("replace failed")),
        pytest.raises(RuntimeError, match="replace failed"),
    ):
        atomic_write_text(target, "new content")

    assert target.read_text(encoding="utf-8") == "original content"
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits only")
def test_atomic_write_text_preserves_permission_bits_posix(tmp_path: Path) -> None:
    target = tmp_path / "script.sh"
    target.write_text("#!/bin/sh\necho old\n", encoding="utf-8")
    os.chmod(target, 0o755)

    atomic_write_text(target, "#!/bin/sh\necho new\n")
    assert stat.S_IMODE(target.stat().st_mode) == 0o755


def test_atomic_write_text_omits_target_name_from_temporary_file(tmp_path: Path) -> None:
    remaining_budget = max(40, 250 - len(str(tmp_path)) - 5)
    long_name = ("long_target_name_" * 10)[:remaining_budget] + ".txt"
    target = tmp_path / long_name
    observed_temp_names: list[str] = []
    real_atomic_replace = files.atomic_replace

    def SpyReplace(src: Path, dst: Path) -> None:
        observed_temp_names.append(Path(src).name)
        real_atomic_replace(src, dst)

    with mock.patch.object(files, "atomic_replace", side_effect=SpyReplace):
        atomic_write_text(target, "payload")

    assert target.read_text(encoding="utf-8") == "payload"
    assert len(observed_temp_names) == 1
    temp_name = observed_temp_names[0]
    assert "long_target_name_" not in temp_name
    assert temp_name.startswith(".")
    assert temp_name.endswith(".tmp")
    assert len(temp_name) < 30


def test_atomic_write_text_newline_argument_controls_translation(tmp_path: Path) -> None:
    lf_target = tmp_path / "lf.txt"
    crlf_target = tmp_path / "crlf.txt"

    atomic_write_text(lf_target, "alpha\nbeta\n", newline="\n")
    atomic_write_text(crlf_target, "alpha\nbeta\n", newline="\r\n")

    assert lf_target.read_bytes() == b"alpha\nbeta\n"
    assert crlf_target.read_bytes() == b"alpha\r\nbeta\r\n"


def test_atomic_replace_retries_on_permission_error_and_winerrors_then_succeeds(tmp_path: Path) -> None:
    src = tmp_path / "source.tmp"
    dst = tmp_path / "dest.txt"
    src.write_text("updated", encoding="utf-8")
    dst.write_text("initial", encoding="utf-8")

    winerror_5 = OSError("Access is denied")
    winerror_5.winerror = 5  # type: ignore[attr-defined]
    winerror_32 = OSError("Sharing violation")
    winerror_32.winerror = 32  # type: ignore[attr-defined]

    real_replace = Path.replace
    attempts = 0

    def FlakyReplace(self_path: Path, target_path: Path) -> Path:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise PermissionError("transient permission error")
        if attempts == 2:
            raise winerror_5
        if attempts == 3:
            raise winerror_32
        return real_replace(self_path, target_path)

    with (
        mock.patch.object(Path, "replace", autospec=True, side_effect=FlakyReplace),
        mock.patch("support_python.files.time.sleep") as mock_sleep,
    ):
        atomic_replace(src, dst, max_retries=5, base_delay=0.01)

    assert attempts == 4
    assert mock_sleep.call_count == 3
    assert not src.exists()
    assert dst.read_text(encoding="utf-8") == "updated"


def test_atomic_replace_raises_after_max_retries_and_removes_source(tmp_path: Path) -> None:
    src = tmp_path / "source.tmp"
    dst = tmp_path / "dest.txt"
    src.write_text("pending", encoding="utf-8")
    dst.write_text("existing", encoding="utf-8")

    with (
        mock.patch.object(Path, "replace", side_effect=PermissionError("permanently locked")),
        mock.patch("support_python.files.time.sleep") as mock_sleep,
        pytest.raises(PermissionError, match="permanently locked"),
    ):
        atomic_replace(src, dst, max_retries=3, base_delay=0.01)

    assert mock_sleep.call_count == 2
    assert not src.exists()
    assert dst.read_text(encoding="utf-8") == "existing"


def test_read_text_retrying_retries_permission_error_and_respects_errors_mode(tmp_path: Path) -> None:
    target = tmp_path / "document.txt"
    target.write_text("hello world", encoding="utf-8")

    real_read_text = Path.read_text
    calls = 0

    def FlakyReadText(self_path: Path, *args: object, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise PermissionError("transient lock")
        return real_read_text(self_path, *args, **kwargs)  # type: ignore[arg-type]

    with (
        mock.patch.object(Path, "read_text", autospec=True, side_effect=FlakyReadText),
        mock.patch("support_python.files.time.sleep") as mock_sleep,
    ):
        result = read_text_retrying(target, max_retries=4, base_delay=0.005)

    assert result == "hello world"
    assert calls == 3
    assert mock_sleep.call_count == 2

    bad_utf8 = tmp_path / "bad.txt"
    bad_utf8.write_bytes(b"prefix-\xff\xfe-suffix")

    replaced = read_text_retrying(bad_utf8, errors="replace")
    assert "prefix-" in replaced
    assert "\ufffd" in replaced

    with pytest.raises(UnicodeDecodeError):
        read_text_retrying(bad_utf8, errors="strict")


def test_concurrent_writer_and_reader_never_observe_partial_content(tmp_path: Path) -> None:
    target = tmp_path / "concurrent.txt"
    content_a = ("A" * 2048 + "\n") * 8
    content_b = ("B" * 2048 + "\n") * 8
    valid_contents = {content_a, content_b}
    atomic_write_text(target, content_a)

    stop_event = threading.Event()
    observed_reads: list[str] = []
    errors: list[BaseException] = []

    def WriterLoop() -> None:
        try:
            for index in range(40):
                payload = content_a if index % 2 == 0 else content_b
                atomic_write_text(target, payload)
        except BaseException as exc:
            errors.append(exc)
        finally:
            stop_event.set()

    def ReaderLoop() -> None:
        try:
            while not stop_event.is_set() or len(observed_reads) < 10:
                text = read_text_retrying(target, max_retries=20, base_delay=0.002, errors="strict")
                observed_reads.append(text)
                if stop_event.is_set():
                    break
        except BaseException as exc:
            errors.append(exc)

    writer = threading.Thread(target=WriterLoop)
    reader = threading.Thread(target=ReaderLoop)
    writer.start()
    reader.start()
    writer.join(timeout=30)
    reader.join(timeout=30)

    assert not errors
    assert observed_reads
    assert all(item in valid_contents for item in observed_reads)
