from __future__ import annotations

from pathlib import Path

from storage.database import Database


def test_database_initializes_schema_and_records_video(tmp_path: Path) -> None:
    db_path = tmp_path / "bri.sqlite3"
    database = Database(str(db_path))

    database.initialize_schema()
    assert db_path.exists()
    database.initialize_schema()
    video_id = database.add_video("demo.mp4", "/tmp/demo.mp4", 12.5)
    video = database.get_video(video_id)

    assert video is not None
    assert video["filename"] == "demo.mp4"
    assert video["duration"] == 12.5


def test_database_records_processing_status(tmp_path: Path) -> None:
    database = Database(str(tmp_path / "bri.sqlite3"))
    database.initialize_schema()
    video_id = database.add_video("demo.mp4", "/tmp/demo.mp4", 12.5)

    database.update_video_status(video_id, "processing")
    database.update_video_status(video_id, "complete")

    assert database.get_video(video_id)["processing_status"] == "complete"
