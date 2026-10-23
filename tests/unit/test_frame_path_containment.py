"""Regression tests: explicit tool frame paths must stay inside the video's frame directory."""

import asyncio
import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from config import Config
from mcp_server.registry import (
    FramePathError,
    ImageCaptioningTool,
    ObjectDetectionTool,
    resolve_video_frame_paths,
)

VIDEO_ID = "video-abc"


@pytest.fixture
def frame_layout(tmp_path, monkeypatch):
    storage = tmp_path / "frames"
    video_dir = storage / VIDEO_ID
    video_dir.mkdir(parents=True)
    other_dir = storage / "other-video"
    other_dir.mkdir()
    outside = tmp_path / "nonlibrary"
    outside.mkdir()

    frame = video_dir / "frame_0001.jpg"
    frame.write_bytes(b"frame")
    other_frame = other_dir / "frame_0001.jpg"
    other_frame.write_bytes(b"other")
    secret = outside / "secret.png"
    secret.write_bytes(b"secret")

    monkeypatch.setenv("FRAME_STORAGE_PATH", str(storage))
    Config.reset_cache()
    yield {
        "storage": storage,
        "video_dir": video_dir,
        "frame": frame,
        "other_frame": other_frame,
        "secret": secret,
    }
    monkeypatch.delenv("FRAME_STORAGE_PATH")
    Config.reset_cache()


def test_registered_frame_path_is_accepted(frame_layout):
    result = resolve_video_frame_paths(VIDEO_ID, [str(frame_layout["frame"])])
    assert result == [str(frame_layout["frame"].resolve())]


def test_relative_frame_name_resolves_inside_video_dir(frame_layout):
    result = resolve_video_frame_paths(VIDEO_ID, ["frame_0001.jpg"])
    assert result == [str(frame_layout["frame"].resolve())]


def test_outside_absolute_path_is_rejected(frame_layout):
    with pytest.raises(FramePathError):
        resolve_video_frame_paths(VIDEO_ID, [str(frame_layout["secret"])])


def test_traversal_path_is_rejected(frame_layout):
    traversal = str(frame_layout["video_dir"] / ".." / ".." / "nonlibrary" / "secret.png")
    with pytest.raises(FramePathError):
        resolve_video_frame_paths(VIDEO_ID, [traversal])


def test_other_video_frame_is_rejected(frame_layout):
    with pytest.raises(FramePathError):
        resolve_video_frame_paths(VIDEO_ID, [str(frame_layout["other_frame"])])


def test_symlink_escape_is_rejected(frame_layout):
    link = frame_layout["video_dir"] / "frame_9999.jpg"
    try:
        os.symlink(frame_layout["secret"], link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform/user")
    with pytest.raises(FramePathError):
        resolve_video_frame_paths(VIDEO_ID, [str(link)])


def test_one_bad_path_rejects_whole_batch(frame_layout):
    with pytest.raises(FramePathError):
        resolve_video_frame_paths(
            VIDEO_ID, [str(frame_layout["frame"]), str(frame_layout["secret"])]
        )


@pytest.mark.parametrize("bad", ["", None, 123, "frame\x00.jpg"])
def test_non_string_or_empty_paths_rejected(frame_layout, bad):
    with pytest.raises(FramePathError):
        resolve_video_frame_paths(VIDEO_ID, [bad])


@pytest.mark.parametrize("bad_video_id", ["..", ".", "../other-video/.."])
def test_video_id_cannot_escape_storage_root(frame_layout, bad_video_id):
    with pytest.raises(FramePathError):
        resolve_video_frame_paths(bad_video_id, [str(frame_layout["secret"])])


def test_captioning_tool_never_opens_outside_path(frame_layout):
    tool = ImageCaptioningTool()
    captioner = Mock()
    tool.captioner = captioner
    tool._get_captioner = lambda: captioner
    with pytest.raises(FramePathError):
        asyncio.run(
            tool.execute(
                VIDEO_ID,
                {"frame_paths": [str(frame_layout["secret"])], "timestamps": [0.0]},
            )
        )
    captioner.caption_frames_batch.assert_not_called()


def test_captioning_tool_passes_contained_path(frame_layout):
    tool = ImageCaptioningTool()
    captioner = Mock()
    captioner.caption_frames_batch.return_value = []
    tool._get_captioner = lambda: captioner
    result = asyncio.run(
        tool.execute(VIDEO_ID, {"frame_paths": [str(frame_layout["frame"])], "timestamps": [0.0]})
    )
    assert result["count"] == 0
    captioner.caption_frames_batch.assert_called_once_with(
        [str(Path(frame_layout["frame"]).resolve())], [0.0]
    )


def test_detection_tool_never_opens_outside_path(frame_layout):
    tool = ObjectDetectionTool()
    detector = Mock()
    tool._get_detector = lambda: detector
    with pytest.raises(FramePathError):
        asyncio.run(
            tool.execute(
                VIDEO_ID,
                {"frame_paths": [str(frame_layout["secret"])], "timestamps": [0.0]},
            )
        )
    detector.detect_objects_in_frames.assert_not_called()
    detector.search_for_object.assert_not_called()
