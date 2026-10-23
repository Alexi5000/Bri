import io
import json
import logging
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from mcp_server.cache import CacheManager
from services.processing_queue import ProcessingQueue
from utils.log_safety import safe_log_value
from utils.logging_config import LogContext, StructuredFormatter


@pytest.mark.parametrize(
    "control", ["\r", "\n", "\t", "\x00", "\x1b", "\x7f", "\x85", "\u2028", "\u2029"]
)
def test_untrusted_control_characters_are_visible_text(control):
    encoded = safe_log_value(f"original{control}forged ERROR")
    assert control not in encoded
    assert encoded.startswith("original\\")
    assert encoded.endswith("forged ERROR")


def test_normal_identifiers_and_unicode_remain_readable():
    assert safe_log_value("clip-7 café 🐈") == "clip-7 café 🐈"
    assert safe_log_value(42) == "42"


@pytest.mark.parametrize("cache_hit", [True, False])
def test_cache_lookup_logs_one_record_without_changing_lookup_key(caplog, cache_hit):
    key = "clip\r\nERROR forged\x1b[2J"
    manager = CacheManager.__new__(CacheManager)
    manager.enabled = True
    manager.redis_client = Mock()
    manager.redis_client.get.return_value = '{"ok":true}' if cache_hit else None
    with caplog.at_level(logging.DEBUG, logger="mcp_server.cache"):
        result = manager.get(key)
    manager.redis_client.get.assert_called_once_with(key)
    assert result == ({"ok": True} if cache_hit else None)
    messages = [
        record.getMessage() for record in caplog.records if record.name == "mcp_server.cache"
    ]
    assert messages
    assert all(
        "\n" not in message and "\r" not in message and "\x1b" not in message
        for message in messages
    )
    assert any("clip\\r\\nERROR forged\\x1b[2J" in message for message in messages)


@pytest.mark.asyncio
async def test_queue_logs_are_safe_while_job_identity_is_preserved(caplog):
    video_id = "clip\nINFO forged"
    queue = ProcessingQueue()
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="services.processing_queue"):
        first = await queue.add_job(video_id, "/video.mp4")
        second = await queue.add_job(video_id, "/video.mp4")
    assert first is second
    assert first.video_id == video_id
    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "services.processing_queue"
    ]
    assert len(messages) == 2
    assert all("\n" not in message and "clip\\nINFO forged" in message for message in messages)


def test_plain_formatter_keeps_message_context_and_traceback_on_one_line():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(StructuredFormatter())
    logger = logging.Logger("boundary")
    logger.addHandler(handler)
    with LogContext(video_id="clip\nforged"):
        try:
            raise ValueError("bad\r\nforged exception")
        except ValueError:
            logger.exception("message %s", "input\nforged")
    output = stream.getvalue()
    assert len(output.splitlines()) == 1
    assert "input\\nforged" in output
    assert "clip\\nforged" in output
    assert "bad\\r\\nforged exception" in output
    assert "ValueError" in output


def test_json_formatter_preserves_structured_values():
    record = logging.LogRecord("boundary", logging.INFO, __file__, 1, "input\nvalue", (), None)
    with LogContext(video_id="clip\nvalue"):
        output = StructuredFormatter(json_format=True).format(record)
    assert len(output.splitlines()) == 1
    data = json.loads(output)
    assert data["message"] == "input\nvalue"
    assert data["video_id"] == "clip\nvalue"


def test_direct_server_startup_bootstraps_workspace_before_local_imports(tmp_path):
    root = Path(__file__).resolve().parents[2]
    code = """
import builtins, pathlib, runpy, sys
root = pathlib.Path(sys.argv[1])
original_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name == 'utils.log_safety':
        assert sys.path[0] == str(root), 'Local import occurred before script bootstrap'
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded_import
runpy.run_path(str(root / 'mcp_server/main.py'), run_name='startup_probe')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(root)], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
