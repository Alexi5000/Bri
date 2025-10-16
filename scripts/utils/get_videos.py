from storage.database import get_all_videos

videos = get_all_videos()
print("Available videos:")
for v in videos:
    print(f"  - {v['video_id']}: {v['filename']} ({v['processing_status']})")
