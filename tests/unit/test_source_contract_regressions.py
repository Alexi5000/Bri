import importlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from mcp_server.circuit_breaker import retry_with_backoff
from mcp_server.validation import (
    ValidatedProcessVideoRequest,
    ValidatedProgressiveProcessRequest,
    ValidatedToolExecutionRequest,
)
from services.data_recovery import AutomaticRetry, RetryPolicy


def test_retry_policy_with_no_attempts_has_explicit_error():
    retry = AutomaticRetry.__new__(AutomaticRetry)
    retry.retry_policy = RetryPolicy(max_retries=0)
    operation = Mock()
    with pytest.raises(ValueError, match="at least one attempt"):
        retry.execute_with_retry(operation, "fixture")
    operation.assert_not_called()


def test_retry_preserves_last_exception_and_success():
    retry = AutomaticRetry.__new__(AutomaticRetry)
    retry.retry_policy = RetryPolicy(max_retries=1)
    error = RuntimeError("original failure")
    with pytest.raises(RuntimeError) as caught:
        retry.execute_with_retry(Mock(side_effect=error), "fixture")
    assert caught.value is error
    assert retry.execute_with_retry(lambda: 42, "fixture") == 42


@pytest.mark.asyncio
async def test_async_retry_rejects_negative_count_and_preserves_zero_retry_attempt():
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        return 42

    with pytest.raises(ValueError, match="non-negative"):
        await retry_with_backoff(operation, max_retries=-1)
    assert calls == 0
    assert await retry_with_backoff(operation, max_retries=0) == 42
    assert calls == 1


def test_classmethod_validators_still_accept_and_reject_requests():
    assert ValidatedToolExecutionRequest(video_id=" clip ").video_id == "clip"
    with pytest.raises(ValueError, match="invalid character"):
        ValidatedToolExecutionRequest(video_id="../clip")
    assert ValidatedProcessVideoRequest(tools=["extract_frames"]).tools == ["extract_frames"]
    with pytest.raises(ValueError, match="Duplicate"):
        ValidatedProcessVideoRequest(tools=["extract_frames", "extract_frames"])
    assert (
        ValidatedProgressiveProcessRequest(video_path="data/clip.mp4").video_path == "data/clip.mp4"
    )
    with pytest.raises(ValueError, match="path traversal"):
        ValidatedProgressiveProcessRequest(video_path="../clip.mp4")
    with pytest.raises(ValueError, match="nesting"):
        ValidatedToolExecutionRequest(video_id="clip", parameters={"a": [[[[[[[1]]]]]]]})


def test_tool_exports_remain_lazy_and_resolve_the_declared_classes(monkeypatch):
    import tools

    for name, (module_name, attribute) in tools._EXPORTS.items():
        sentinel = type(name, (), {})
        module = type(sys)(module_name)
        setattr(module, attribute, sentinel)
        monkeypatch.setitem(sys.modules, module_name, module)
        monkeypatch.delitem(tools.__dict__, name, raising=False)
        assert getattr(tools, name) is sentinel
        monkeypatch.delitem(tools.__dict__, name)
    with pytest.raises(AttributeError):
        getattr(tools, "not_a_tool")


def test_importing_config_and_tools_does_not_load_optional_media_modules():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import config, tools, sys, json; print(json.dumps([name for name in ('torch', 'transformers', 'whisper') if name in sys.modules]))",
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
        check=True,
    )
    assert json.loads(result.stdout) == []


def test_config_logger_preserves_standard_logger_identity():
    import logging

    config = importlib.import_module("config")
    assert config._get_logger() is logging.getLogger("config")


@pytest.mark.parametrize("kind", ["lineage", "mutation", "dead_letter"])
def test_malformed_stored_json_is_retained_and_reported(kind, caplog):
    from services.data_lineage_tracker import DataLineageTracker
    from services.data_observability import DataMutationLogger
    from services.data_recovery import DeadLetterQueue

    if kind == "lineage":
        service = DataLineageTracker.__new__(DataLineageTracker)
        key = "parameters"
        call = lambda: service.get_lineage_history("clip")
    elif kind == "mutation":
        service = DataMutationLogger.__new__(DataMutationLogger)
        key = "data"
        call = service.get_mutation_history
    else:
        service = DeadLetterQueue.__new__(DeadLetterQueue)
        key = "data"
        call = service.get_queue_items
    service.db = Mock()
    service.db.execute_query.return_value = [{key: "{invalid"}]
    assert call() == [{key: "{invalid"}]
    assert "invalid JSON" in caplog.text


def test_optional_model_resources_can_be_closed_without_running_finalizers():
    code = """
import importlib, sys, types
from unittest.mock import Mock
for name in ('torch', 'transformers', 'whisper'):
    sys.modules[name] = types.ModuleType(name)
sys.modules['torch'].cuda = Mock()
sys.modules['torch'].cuda.is_available.return_value = False
sys.modules['transformers'].BlipForConditionalGeneration = object
sys.modules['transformers'].BlipProcessor = object
for module_name, class_name, fields in [
    ('tools.image_captioner', 'ImageCaptioner', ('model', 'processor')),
    ('tools.audio_transcriber', 'AudioTranscriber', ('model',)),
]:
    cls = getattr(importlib.import_module(module_name), class_name)
    instance = cls.__new__(cls)
    for field in fields:
        setattr(instance, field, object())
    instance.close()
    instance.close()
    assert all(not hasattr(instance, field) for field in fields)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_archived_context_check_closes_database_when_schema_setup_fails(monkeypatch):
    import importlib.util

    path = (
        Path(__file__).resolve().parents[2] / "scripts/archive/legacy_tests/test_context_builder.py"
    )
    spec = importlib.util.spec_from_file_location("context_check_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    database = Mock()
    database.initialize_schema.side_effect = RuntimeError("schema fixture failure")

    class ManagedDatabase:
        def __init__(self, path):
            self.path = path

        def connect(self):
            return database.connect()

        def initialize_schema(self):
            return database.initialize_schema()

        def close(self):
            return database.close()

        def __enter__(self):
            self.connect()
            return self

        def __exit__(self, *args):
            self.close()

    monkeypatch.setattr(module, "Database", ManagedDatabase)
    with pytest.raises(RuntimeError, match="schema fixture failure"):
        module.main()
    database.close.assert_called_once()
