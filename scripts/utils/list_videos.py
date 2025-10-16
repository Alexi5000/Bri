from storage.database import Database
import os

db = Database()
db.connect()
videos = db.execute_query('SELECT video_id, filename, file_path FROM videos')

for v in videos:
    exists = "✓" if os.path.exists(v["file_path"]) else "✗"
    print(f'{exists} {v["video_id"]}: {v["filename"]} -> {v["file_path"]}')
