"""
Quick Fix Script - Run this to diagnose and fix BRI
"""
import os
import sys
import subprocess

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")

def run_command(cmd, description):
    print(f"▶ {description}")
    print(f"  Command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("  ✅ Success")
        return True
    else:
        print(f"  ❌ Failed: {result.stderr}")
        return False

def main():
    print_header("BRI VIDEO AGENT - QUICK FIX")
    
    print("This script will:")
    print("1. Diagnose the system")
    print("2. Show you what's broken")
    print("3. Tell you exactly how to fix it")
    print()
    
    input("Press Enter to start diagnosis...")
    
    # Step 1: Diagnose
    print_header("STEP 1: SYSTEM DIAGNOSIS")
    run_command("python diagnose_system.py", "Running diagnostic")
    
    # Step 2: Instructions
    print_header("STEP 2: FIX INSTRUCTIONS")
    
    print("Based on the diagnosis above, here's what to do:\n")
    
    print("🔧 IF YOU SEE: '❌ CRITICAL: Video not processed'")
    print("   → The video has frames but no captions/transcripts")
    print("   → This is the main issue blocking 90% pass rate")
    print()
    print("   FIX:")
    print("   1. Open a NEW terminal")
    print("   2. Run: python mcp_server/main.py")
    print("   3. Wait for 'Server running' message")
    print("   4. Come back here and press Enter")
    print()
    
    input("Press Enter after starting MCP server...")
    
    print("\n   5. Now processing video...")
    
    # Get video ID from diagnostic
    from storage.database import Database
    db = Database()
    db.connect()
    videos = db.execute_query("SELECT video_id, file_path FROM videos")
    
    # Find first video with file
    video_id = None
    for v in videos:
        if os.path.exists(v['file_path']):
            video_id = v['video_id']
            break
    
    if not video_id:
        print("   ❌ No videos with files found")
        print("   → Upload a video first through the Streamlit UI")
        return
    
    print(f"   Processing video: {video_id}")
    success = run_command(
        f"python process_test_video.py {video_id}",
        "Running video processing"
    )
    
    if not success:
        print("\n   ❌ Processing failed")
        print("   → Check that MCP server is running")
        print("   → Check the error message above")
        return
    
    # Step 3: Verify
    print_header("STEP 3: VERIFICATION")
    run_command("python diagnose_system.py", "Re-running diagnostic")
    
    print("\n🎯 IF YOU NOW SEE: '✅ SUCCESS: Video fully processed'")
    print("   → Great! Data persistence is working")
    print("   → Now run tests:")
    print(f"   → python tests/eval_bri_performance.py {video_id}")
    print()
    
    print("📊 EXPECTED RESULT:")
    print("   → Pass rate should jump from 74% to 90%+")
    print("   → Agent should give intelligent answers")
    print()
    
    # Step 4: Next steps
    print_header("STEP 4: NEXT STEPS")
    
    print("✅ If tests pass at 90%+:")
    print("   → You're done! System is working")
    print("   → Move on to Tasks 41-43 for progressive processing")
    print()
    
    print("❌ If tests still fail:")
    print("   → Check EXECUTION_PLAN.md for detailed debugging")
    print("   → Run: python analyze_failures.py")
    print("   → Review ARCHITECTURE_ANALYSIS.md")
    print()
    
    print_header("COMPLETE")
    print("See EXECUTION_PLAN.md for full details on Tasks 40-43")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("See EXECUTION_PLAN.md for manual steps")
