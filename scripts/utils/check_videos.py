from storage.database import Database

db = Database()
db.connect()
videos = db.execute_query('SELECT video_id, filename FROM videos LIMIT 5')
for v in videos:
    print(f"{v['video_id']}: {v['filename']}")
