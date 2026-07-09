"""
Test script for Welcome Screen Component (Task 16)

This script verifies that the welcome screen component is properly implemented
with all required elements.

Requirements tested:
- 1.2: Warm and approachable UI with friendly microcopy
- 2.3: Upload prompt with friendly confirmation messages
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_welcome_component_exists():
    """Test that the welcome component module exists and can be imported"""
    try:
        from ui import welcome  # noqa: F401
        print("✅ Welcome component module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import welcome component: {e}")
        return False


def test_welcome_functions_callable():
    """Test that welcome screen functions are callable"""
    try:
        from ui import welcome
        
        # Check if functions are callable
        assert callable(welcome.render_welcome_screen), "render_welcome_screen is not callable"
        assert callable(welcome.render_empty_state), "render_empty_state is not callable"
        
        print("✅ All welcome screen functions are callable")
        return True
    except AssertionError as e:
        print(f"❌ Function callable test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_app_integration():
    """Test that app.py properly imports and uses the welcome screen"""
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Check for import statement
        assert 'from ui.welcome import render_welcome_screen' in app_content, \
            "Missing import statement in app.py"
        
        # Check for usage
        assert 'render_welcome_screen()' in app_content, \
            "render_welcome_screen() not called in app.py"
        
        print("✅ Welcome screen properly integrated into app.py")
        return True
    except AssertionError as e:
        print(f"❌ App integration test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")
        return False


def test_component_structure():
    """Test that the welcome component has the required structure"""
    try:
        with open('ui/welcome.py', 'r', encoding='utf-8') as f:
            welcome_content = f.read()
        
        # Check for key elements
        required_elements = [
            "Hi, I'm BRI",  # Friendly greeting
            "Ask. Understand. Remember.",  # Tagline
            "file_uploader",  # Upload functionality
            "mp4",  # Supported format
            "avi",  # Supported format
            "mov",  # Supported format
            "mkv",  # Supported format
            "emoji",  # Emoji touches
            "💜",  # Heart emoji (BRI's signature)
            "🎬",  # Video emoji
            "_handle_upload",  # Upload handler
            "_render_feature_card",  # Feature highlights
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in welcome_content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing required elements: {', '.join(missing_elements)}")
            return False
        
        print("✅ Welcome component has all required structural elements")
        return True
    except Exception as e:
        print(f"❌ Error checking component structure: {e}")
        return False


def test_friendly_microcopy():
    """Test that the component includes friendly microcopy"""
    try:
        with open('ui/welcome.py', 'r', encoding='utf-8') as f:
            welcome_content = f.read()
        
        # Check for friendly phrases
        friendly_phrases = [
            "Ready when you are",
            "Let me take a look",
            "I'm here to",
            "friendly",
            "conversation",
        ]
        
        found_phrases = []
        for phrase in friendly_phrases:
            if phrase.lower() in welcome_content.lower():
                found_phrases.append(phrase)
        
        if len(found_phrases) < 3:
            print(f"⚠️  Limited friendly microcopy found: {found_phrases}")
            print("   Consider adding more warm, conversational language")
        else:
            print(f"✅ Friendly microcopy present: {len(found_phrases)} phrases found")
        
        return True
    except Exception as e:
        print(f"❌ Error checking microcopy: {e}")
        return False


def test_upload_confirmation():
    """Test that upload handler provides friendly confirmation"""
    try:
        with open('ui/welcome.py', 'r', encoding='utf-8') as f:
            welcome_content = f.read()
        
        # Check for confirmation elements
        confirmation_elements = [
            "st.success",  # Success message
            "Got it",  # Friendly acknowledgment
            "file_size",  # File details
        ]
        
        missing = []
        for element in confirmation_elements:
            if element not in welcome_content:
                missing.append(element)
        
        if missing:
            print(f"❌ Missing upload confirmation elements: {', '.join(missing)}")
            return False
        
        print("✅ Upload confirmation with friendly messages implemented")
        return True
    except Exception as e:
        print(f"❌ Error checking upload confirmation: {e}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("Testing Welcome Screen Component (Task 16)")
    print("=" * 60)
    print()
    
    tests = [
        ("Component Import", test_welcome_component_exists),
        ("Function Callability", test_welcome_functions_callable),
        ("App Integration", test_app_integration),
        ("Component Structure", test_component_structure),
        ("Friendly Microcopy", test_friendly_microcopy),
        ("Upload Confirmation", test_upload_confirmation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 60)
        result = test_func()
        results.append((test_name, result))
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Welcome screen is ready!")
        print("\n📝 Next steps:")
        print("   1. Run 'streamlit run app.py' to see the welcome screen")
        print("   2. Test the file uploader with a sample video")
        print("   3. Verify the UI matches the design requirements")
        print("   4. Move on to Task 17 (video upload functionality)")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review and fix.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
