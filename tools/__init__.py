"""Video processing tool exports.

The concrete tool modules depend on optional media and model packages such as
OpenCV, Transformers, Whisper, and Torch. Importing this package should stay
cheap for API workers, documentation checks, and lightweight CI. Tool classes
are therefore resolved lazily when accessed.
"""

from __future__ import annotations

from typing import Any

__all__ = ["FrameExtractor", "ImageCaptioner", "AudioTranscriber"]

_EXPORTS = {
    "FrameExtractor": ("tools.frame_extractor", "FrameExtractor"),
    "ImageCaptioner": ("tools.image_captioner", "ImageCaptioner"),
    "AudioTranscriber": ("tools.audio_transcriber", "AudioTranscriber"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    try:
        module = __import__(module_name, fromlist=[attr_name])
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency-specific help
        raise ModuleNotFoundError(
            f"{name} requires an optional media dependency that is not installed. "
            "Install the full requirements or the appropriate optional extra before using this tool."
        ) from exc
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
