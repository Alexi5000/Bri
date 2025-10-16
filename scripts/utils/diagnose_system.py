"""
BRI System Diagnostic Tool
Analyzes the complete data pipeline and identifies issues.
"""
import os
from storage.database import Database
from config import Config

def diagnose():
    print("="*80)
    print("BRI VIDEO AGENT - SYSTEM DIAGNOSTIC")
    print("="*80)
    
    db = Database()
    db.connect()
    
    # 1. Check database
    print("\n📊 DATABASE STATUS")
    print("-"*80)
    videos = db.execute_query("SELECT COUNT(*) as count FROM videos")
    print(f"Total videos in database: {videos[0]['count']}")
    
    # 2. Check video files
    print("\n📁 VIDEO FILES")
    print("-"*80)
    videos = db.execute_query("SELECT video_id, filename, file_path FROM videos")
    existing = 0
    missing = 0
    for v in videos:
        if os.path.exists(v['file_path']):
            existing += 1
        else:
            missing += 1
    print(f"Videos with existing files: {existing}")
    print(f"Videos with missing files: {missing}")
    
    # 3. Check processed data
    print("\n🔬 PROCESSED DATA")
    print("-"*80)
    
    # Find videos with files
    videos_with_files = [v for v in videos if os.path.exists(v['file_path'])]
    
    if not videos_with_files:
        print("❌ NO VIDEOS WITH FILES FOUND")
        print("   → Upload a video first")
        return
    
    # Check first video with file
    test_video = videos_with_files[0]
    video_id = test_video['video_id']
    
    print(f"\nAnalyzing video: {test_video['filename']} ({video_id})")
    print("-"*80)
    
    # Check frames
    frames = db.execute_query(
        "SELECT COUNT(*) as count FROM video_context WHERE video_id = ? AND context_type = 'frame'",
        (video_id,)
    )
    frame_count = frames[0]['count']
    print(f"✓ Frames extracted: {frame_count}")
    
    # Check captions
    captions = db.execute_query(
        "SELECT COUNT(*) as count FROM video_context WHERE video_id = ? AND context_type = 'caption'",
        (video_id,)
    )
    caption_count = captions[0]['count']
    status = "✓" if caption_count > 0 else "❌"
    print(f"{status} Captions generated: {caption_count}")
    
    # Check transcripts
    transcripts = db.execute_query(
        "SELECT COUNT(*) as count FROM video_context WHERE video_id = ? AND context_type = 'transcript'",
        (video_id,)
    )
    transcript_count = transcripts[0]['count']
    status = "✓" if transcript_count > 0 else "❌"
    print(f"{status} Transcript segments: {transcript_count}")
    
    # Check objects
    objects = db.execute_query(
        "SELECT COUNT(*) as count FROM video_context WHERE video_id = ? AND context_type = 'object'",
        (video_id,)
    )
    object_count = objects[0]['count']
    status = "✓" if object_count > 0 else "❌"
    print(f"{status} Object detections: {object_count}")
    
    # 4. Calculate completeness
    print("\n📈 DATA COMPLETENESS")
    print("-"*80)
    
    total_data_points = frame_count + caption_count + transcript_count + object_count
    expected_minimum = frame_count * 2  # At least frames + captions
    
    if total_data_points == 0:
        completeness = 0
    else:
        completeness = min(100, (total_data_points / expected_minimum) * 100)
    
    print(f"Completeness: {completeness:.1f}%")
    
    if completeness < 50:
        print("\n❌ CRITICAL: Video not processed")
        print("   → Run: python process_test_video.py", video_id)
    elif completeness < 100:
        print("\n⚠️  WARNING: Partial processing")
        print("   → Some tools didn't complete")
    else:
        print("\n✅ SUCCESS: Video fully processed")
    
    # 5. Check MCP server
    print("\n🔧 MCP SERVER")
    print("-"*80)
    try:
        import httpx
        import asyncio
        
        async def check_server():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{Config.get_mcp_server_url()}/health")
                    if response.status_code == 200:
                        print("✓ MCP Server is running")
                        data = response.json()
                        print(f"  Tools registered: {data.get('tools_registered', 'unknown')}")
                        return True
            except:
                return False
        
        if asyncio.run(check_server()):
            pass
        else:
            print("❌ MCP Server is NOT running")
            print("   → Start with: python mcp_server/main.py")
    except Exception as e:
        print(f"❌ Cannot check MCP server: {e}")
    
    # 6. Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-"*80)
    
    if missing > 0:
        print("1. Clean up database entries for missing video files")
    
    if caption_count == 0 and frame_count > 0:
        print("2. CRITICAL: Frames exist but no captions")
        print("   → MCP server not storing tool results")
        print("   → Restart MCP server and reprocess video")
    
    if transcript_count == 0:
        print("3. Run audio transcription on video")
    
    if object_count == 0:
        print("4. Run object detection on video")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Restart MCP server: python mcp_server/main.py")
    print(f"2. Process video: python process_test_video.py {video_id}")
    print("3. Run tests: python tests/eval_bri_performance.py", video_id)
    print("="*80)

if __name__ == "__main__":
    diagnose()
