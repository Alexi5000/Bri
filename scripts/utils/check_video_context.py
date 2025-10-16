from storage.database import Database
import json

db = Database()
db.connect()

video_id = "75befeed-4502-492c-a62d-d30d1852ef9a"

# Also show sample data
print("\nSample captions:")
sample_captions = db.execute_query(
    """SELECT data FROM video_context 
       WHERE video_id = ? AND context_type = 'caption'
       LIMIT 3""",
    (video_id,)
)
import json
for cap in sample_captions:
    data = json.loads(cap['data'])
    print(f"  [{data.get('timestamp', 0):.1f}s] {data.get('text', 'N/A')[:50]}")

# Check if video has frames
frames = db.execute_query(
    """SELECT COUNT(*) as count FROM video_context 
       WHERE video_id = ? AND context_type = 'frame'""",
    (video_id,)
)

captions = db.execute_query(
    """SELECT COUNT(*) as count FROM video_context 
       WHERE video_id = ? AND context_type = 'caption'""",
    (video_id,)
)

transcripts = db.execute_query(
    """SELECT COUNT(*) as count FROM video_context 
       WHERE video_id = ? AND context_type = 'transcript'""",
    (video_id,)
)

objects = db.execute_query(
    """SELECT COUNT(*) as count FROM video_context 
       WHERE video_id = ? AND context_type = 'object'""",
    (video_id,)
)

print(f"Video: {video_id}")
print(f"Frames: {frames[0]['count']}")
print(f"Captions: {captions[0]['count']}")
print(f"Transcripts: {transcripts[0]['count']}")
print(f"Objects: {objects[0]['count']}")
