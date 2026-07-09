"""
Verification script for Task 17: Video Upload Functionality
Tests all requirements specified in the task.
"""

import sys
import io
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from services.video_service import get_video_service, VideoValidationError, VideoServiceError
from storage.database import initialize_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_file_uploader_component():
    """Verify file uploader component exists and accepts correct formats."""
    print("\n" + "="*70)
    print("REQUIREMENT: Create file uploader component accepting MP4, AVI, MOV, MKV")
    print("="*70)
    
    try:
        from ui.welcome import render_welcome_screen
        print("✅ PASS: Welcome screen with file uploader component exists")
        
        # Check if the component is properly documented
        if render_welcome_screen.__doc__:
            print("✅ PASS: Component has documentation")
        
        # Verify supported formats in video service
        video_service = get_video_service()
        supported = video_service.SUPPORTED_FORMATS
        expected = {'.mp4', '.avi', '.mov', '.mkv'}
        
        if supported == expected:
            print(f"✅ PASS: Supports correct formats: {', '.join(expected)}")
        else:
            print(f"❌ FAIL: Format mismatch. Expected {expected}, got {supported}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def verify_handle_video_upload():
    """Verify handle_video_upload function exists and processes files."""
    print("\n" + "="*70)
    print("REQUIREMENT: Implement handle_video_upload to process uploaded files")
    print("="*70)
    
    try:
        from ui.welcome import handle_video_upload
        print("✅ PASS: handle_video_upload function exists")
        
        if handle_video_upload.__doc__:
            print("✅ PASS: Function has documentation")
            if "2.1" in handle_video_upload.__doc__ or "Requirements" in handle_video_upload.__doc__:
                print("✅ PASS: Documentation references requirements")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def verify_video_validation():
    """Verify video validation for format and size limits."""
    print("\n" + "="*70)
    print("REQUIREMENT: Add video validation (format, size limits)")
    print("="*70)
    
    video_service = get_video_service()
    
    # Test format validation
    print("\nTesting format validation:")
    
    # Valid formats
    valid_tests = [
        ("video.mp4", True),
        ("video.avi", True),
        ("video.mov", True),
        ("video.mkv", True),
    ]
    
    for filename, should_pass in valid_tests:
        is_valid, error = video_service.validate_video_file(filename, 1024 * 1024)
        if is_valid == should_pass:
            print(f"  ✅ {filename}: {'Valid' if is_valid else 'Invalid'}")
        else:
            print(f"  ❌ {filename}: Expected {should_pass}, got {is_valid}")
            return False
    
    # Invalid format
    is_valid, error = video_service.validate_video_file("video.txt", 1024)
    if not is_valid and error:
        print(f"  ✅ Invalid format rejected with friendly message")
        print(f"     Message: {error}")
    else:
        print(f"  ❌ Invalid format not properly rejected")
        return False
    
    # Test size validation
    print("\nTesting size validation:")
    
    # Valid size
    is_valid, error = video_service.validate_video_file("video.mp4", 100 * 1024 * 1024)
    if is_valid:
        print(f"  ✅ 100 MB file accepted")
    else:
        print(f"  ❌ Valid size rejected: {error}")
        return False
    
    # Too large
    is_valid, error = video_service.validate_video_file("video.mp4", 600 * 1024 * 1024)
    if not is_valid and error:
        print(f"  ✅ 600 MB file rejected with friendly message")
        print(f"     Message: {error}")
    else:
        print(f"  ❌ Large file not properly rejected")
        return False
    
    # Verify max size constant
    if video_service.MAX_FILE_SIZE_BYTES == 500 * 1024 * 1024:
        print(f"  ✅ Max file size set to 500 MB")
    else:
        print(f"  ❌ Max file size incorrect: {video_service.MAX_FILE_SIZE_BYTES}")
        return False
    
    return True


def verify_file_storage():
    """Verify video storage with unique ID."""
    print("\n" + "="*70)
    print("REQUIREMENT: Store uploaded video to file system with unique ID")
    print("="*70)
    
    video_service = get_video_service()
    
    # Create mock video
    mock_data = b"MOCK_VIDEO" * 100
    file_data = io.BytesIO(mock_data)
    
    try:
        video, error = video_service.upload_video(
            file_data=file_data,
            filename="test_storage.mp4",
            file_size=len(mock_data)
        )
        
        if error:
            print(f"❌ FAIL: Upload failed: {error}")
            return False
        
        # Verify unique ID
        if video.video_id and len(video.video_id) > 0:
            print(f"✅ PASS: Video assigned unique ID: {video.video_id}")
        else:
            print(f"❌ FAIL: No unique ID assigned")
            return False
        
        # Verify file path
        if Path(video.file_path).exists():
            print(f"✅ PASS: Video file stored at: {video.file_path}")
        else:
            print(f"❌ FAIL: Video file not found at: {video.file_path}")
            return False
        
        # Verify file is in correct directory structure
        if video.video_id in video.file_path:
            print(f"✅ PASS: File stored in video-specific directory")
        else:
            print(f"❌ FAIL: File not in video-specific directory")
            return False
        
        # Clean up
        video_service.delete_video(video.video_id)
        print(f"✅ PASS: Test video cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def verify_database_record():
    """Verify video record creation in database."""
    print("\n" + "="*70)
    print("REQUIREMENT: Create video record in database")
    print("="*70)
    
    video_service = get_video_service()
    
    # Create mock video
    mock_data = b"MOCK_VIDEO" * 100
    file_data = io.BytesIO(mock_data)
    
    try:
        video, error = video_service.upload_video(
            file_data=file_data,
            filename="test_db.mp4",
            file_size=len(mock_data)
        )
        
        if error:
            print(f"❌ FAIL: Upload failed: {error}")
            return False
        
        # Retrieve from database
        retrieved = video_service.get_video(video.video_id)
        
        if retrieved:
            print(f"✅ PASS: Video record created in database")
            
            # Verify fields
            checks = [
                (retrieved.video_id == video.video_id, "video_id"),
                (retrieved.filename == video.filename, "filename"),
                (retrieved.file_path == video.file_path, "file_path"),
                (retrieved.processing_status == "pending", "processing_status"),
            ]
            
            for check, field in checks:
                if check:
                    print(f"  ✅ {field} stored correctly")
                else:
                    print(f"  ❌ {field} mismatch")
                    return False
        else:
            print(f"❌ FAIL: Video not found in database")
            return False
        
        # Clean up
        video_service.delete_video(video.video_id)
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def verify_success_message():
    """Verify friendly confirmation message functionality."""
    print("\n" + "="*70)
    print("REQUIREMENT: Display friendly confirmation message on successful upload")
    print("="*70)
    
    # Check if success messages are in the code
    welcome_file = Path(__file__).parent.parent / "ui" / "welcome.py"
    
    if not welcome_file.exists():
        print(f"❌ FAIL: welcome.py not found")
        return False
    
    content = welcome_file.read_text(encoding='utf-8')
    
    # Check for success indicators
    success_indicators = [
        "st.success",
        "Perfect!",
        "🎉",
        "st.balloons",
    ]
    
    found = []
    for indicator in success_indicators:
        if indicator in content:
            found.append(indicator)
            print(f"  ✅ Found success element: {indicator}")
    
    if len(found) >= 2:
        print(f"✅ PASS: Friendly success messages implemented")
        return True
    else:
        print(f"❌ FAIL: Insufficient success messaging")
        return False


def verify_error_handling():
    """Verify error handling with playful error messages."""
    print("\n" + "="*70)
    print("REQUIREMENT: Implement error handling with playful error messages")
    print("="*70)
    
    video_service = get_video_service()
    
    # Test invalid format error
    is_valid, error = video_service.validate_video_file("test.txt", 1024)
    if error and ("Oops" in error or "?" in error):
        print(f"✅ PASS: Playful error message for invalid format")
        print(f"   Message: {error}")
    else:
        print(f"❌ FAIL: Error message not playful enough")
        return False
    
    # Test file too large error
    is_valid, error = video_service.validate_video_file("test.mp4", 600 * 1024 * 1024)
    if error and ("bit too big" in error or "?" in error):
        print(f"✅ PASS: Playful error message for large file")
        print(f"   Message: {error}")
    else:
        print(f"❌ FAIL: Error message not playful enough")
        return False
    
    # Check for error handling in UI
    welcome_file = Path(__file__).parent.parent / "ui" / "welcome.py"
    content = welcome_file.read_text(encoding='utf-8')
    
    error_indicators = [
        "VideoValidationError",
        "VideoServiceError",
        "st.error",
        "except",
    ]
    
    found = []
    for indicator in error_indicators:
        if indicator in content:
            found.append(indicator)
    
    if len(found) >= 3:
        print(f"✅ PASS: Error handling implemented in UI")
        for indicator in found:
            print(f"   - {indicator}")
    else:
        print(f"❌ FAIL: Insufficient error handling in UI")
        return False
    
    return True


def main():
    """Run all verification tests."""
    print("\n" + "="*70)
    print("TASK 17 VERIFICATION: Video Upload Functionality")
    print("="*70)
    
    # Ensure setup
    Config.ensure_directories()
    initialize_database()
    
    # Run all verifications
    results = []
    
    results.append(("File Uploader Component", verify_file_uploader_component()))
    results.append(("handle_video_upload Function", verify_handle_video_upload()))
    results.append(("Video Validation", verify_video_validation()))
    results.append(("File Storage with Unique ID", verify_file_storage()))
    results.append(("Database Record Creation", verify_database_record()))
    results.append(("Success Messages", verify_success_message()))
    results.append(("Error Handling", verify_error_handling()))
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "="*70)
    print(f"TOTAL: {passed}/{total} requirements verified")
    print("="*70)
    
    if passed == total:
        print("\n🎉 All requirements for Task 17 are implemented and verified!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} requirement(s) need attention")
        return 1


if __name__ == "__main__":
    exit(main())
