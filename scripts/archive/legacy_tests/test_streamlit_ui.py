"""
Test script to verify Streamlit UI foundation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all UI modules can be imported"""
    print("Testing imports...")
    
    try:
        from ui.styles import get_color, COLORS
        print("✓ ui.styles imported successfully")
        
        # Test color palette
        assert 'blush_pink' in COLORS
        assert 'lavender' in COLORS
        assert 'teal' in COLORS
        assert 'cream' in COLORS
        print("✓ Color palette defined correctly")
        
        # Test get_color function
        color = get_color('blush_pink')
        assert color == '#FFB6C1'
        print("✓ get_color function works")
        
        print("\n✅ All UI foundation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_app_structure():
    """Test that app.py has correct structure"""
    print("\nTesting app.py structure...")
    
    try:
        app_path = project_root / "app.py"
        if not app_path.exists():
            print("❌ app.py not found")
            return False
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key components
        required_elements = [
            'st.set_page_config',
            'initialize_session_state',
            'render_sidebar',
            'render_main_content',
            'apply_custom_styles',
            'current_video_id',
            'conversation_history',
            'uploaded_videos',
            'current_view',
        ]
        
        for element in required_elements:
            if element not in content:
                print(f"❌ Missing required element: {element}")
                return False
            print(f"✓ Found: {element}")
        
        print("\n✅ App structure test passed!")
        return True
        
    except Exception as e:
        print(f"❌ App structure test failed: {e}")
        return False

def test_session_state_variables():
    """Test that session state variables are properly defined"""
    print("\nTesting session state variables...")
    
    expected_vars = [
        'current_video_id',
        'conversation_history',
        'uploaded_videos',
        'current_view',
        'processing_status',
        'user_message'
    ]
    
    app_path = project_root / "app.py"
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for var in expected_vars:
        if f"'{var}'" in content or f'"{var}"' in content:
            print(f"✓ Session state variable defined: {var}")
        else:
            print(f"❌ Missing session state variable: {var}")
            return False
    
    print("\n✅ Session state variables test passed!")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("BRI Streamlit UI Foundation Tests")
    print("=" * 60)
    
    results = []
    
    results.append(test_imports())
    results.append(test_app_structure())
    results.append(test_session_state_variables())
    
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 All tests passed! UI foundation is ready.")
        print("\nTo run the app:")
        print("  streamlit run app.py")
    else:
        print("❌ Some tests failed. Please review the output above.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
