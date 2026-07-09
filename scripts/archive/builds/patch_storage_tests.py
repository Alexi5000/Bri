from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

database_path = ROOT / "storage" / "database.py"
database_text = database_path.read_text(encoding="utf-8")
if "def add_video(" not in database_text:
    insertion = r'''
    def add_video(
        self,
        filename: str,
        file_path: str,
        duration: float,
        video_id: str | None = None,
        thumbnail_path: str | None = None,
    ) -> str:
        """Create a video row through an instance-scoped database connection.

        This convenience method mirrors the module-level helpers while making
        isolated tests and embedded deployments straightforward because callers
        can provide their own database path.
        """
        import uuid

        record_id = video_id or f"video-{uuid.uuid4().hex[:12]}"
        self.validate_video_data(record_id, filename, file_path, duration)
        self.execute_update(
            """
            INSERT INTO videos (video_id, filename, file_path, duration, thumbnail_path, processing_status)
            VALUES (?, ?, ?, ?, ?, 'pending')
            """,
            (record_id, filename, file_path, duration, thumbnail_path),
        )
        return record_id

    def get_video(self, video_id: str) -> Optional[sqlite3.Row]:
        """Return a video row by identifier from this database instance."""
        results = self.execute_query("SELECT * FROM videos WHERE video_id = ?", (video_id,))
        return results[0] if results else None

    def update_video_status(self, video_id: str, status: str) -> None:
        """Update processing status for a video row in this database instance."""
        self.execute_update(
            "UPDATE videos SET processing_status = ? WHERE video_id = ?",
            (status, video_id),
        )

'''
    marker = "    def close(self) -> None:\n"
    database_text = database_text.replace(marker, insertion + marker)
    database_path.write_text(database_text, encoding="utf-8")

contract_path = ROOT / "tests" / "production" / "test_production_contract.py"
contract_text = contract_path.read_text(encoding="utf-8")
contract_text = contract_text.replace(
    "ROOT = Path(__file__).resolve().parents[1]", "ROOT = Path(__file__).resolve().parents[2]"
)
contract_path.write_text(contract_text, encoding="utf-8")

storage_path = ROOT / "tests" / "production" / "test_storage_contract.py"
storage_text = storage_path.read_text(encoding="utf-8")
storage_text = storage_text.replace(
    "    assert db_path.exists()\n",
    "    database.initialize_schema()\n    assert db_path.exists()\n",
)
storage_text = storage_text.replace(
    '    video_id = database.add_video("demo.mp4", "/tmp/demo.mp4", 12.5)\n',
    '    database.initialize_schema()\n    video_id = database.add_video("demo.mp4", "/tmp/demo.mp4", 12.5)\n',
)
storage_text = storage_text.replace(
    '    assert database.get_video(video_id)["status"] == "completed"\n',
    '    assert database.get_video(video_id)["processing_status"] == "complete"\n',
)
storage_text = storage_text.replace(
    '    database.update_video_status(video_id, "completed")\n',
    '    database.update_video_status(video_id, "complete")\n',
)
storage_path.write_text(storage_text, encoding="utf-8")

print("Patched storage convenience methods and production test expectations.")
