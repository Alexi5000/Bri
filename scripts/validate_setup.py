"""Validate BRI setup and configuration."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"  ✗ Python 3.9+ required (found {version.major}.{version.minor})")
        return False
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    print("\n📦 Checking dependencies...")
    required_packages = [
        "streamlit",
        "groq",
        "opencv-python",
        "transformers",
        "whisper",
        "ultralytics",
        "fastapi",
        "redis",
        "dotenv",
        "pydantic",
    ]

    missing = []
    for package in required_packages:
        try:
            # Handle package name variations
            import_name = package
            if package == "opencv-python":
                import_name = "cv2"
            elif package == "dotenv":
                import_name = "dotenv"

            __import__(import_name)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)

    if missing:
        print(f"\n  Install missing packages: pip install {' '.join(missing)}")
        return False
    return True


def check_configuration():
    """Check if configuration is valid."""
    print("\n⚙️  Checking configuration...")
    try:
        Config.validate()
        print("  ✓ Configuration is valid")
        return True
    except ValueError as e:
        print("  ✗ Configuration validation failed:")
        print(f"    {e}")
        return False


def check_directories():
    """Check if required directories exist or can be created."""
    print("\n📁 Checking directories...")
    try:
        Config.ensure_directories()

        directories = [
            Config.VIDEO_STORAGE_PATH,
            Config.FRAME_STORAGE_PATH,
            Config.CACHE_STORAGE_PATH,
            Path(Config.DATABASE_PATH).parent,
        ]

        for directory in directories:
            if Path(directory).exists():
                print(f"  ✓ {directory}")
            else:
                print(f"  ✗ {directory} (could not create)")
                return False
        return True
    except Exception as e:
        print(f"  ✗ Error creating directories: {e}")
        return False


def check_redis():
    """Check if Redis is available (optional)."""
    print("\n🔴 Checking Redis (optional)...")
    if not Config.REDIS_ENABLED:
        print("  ⚠️  Redis is disabled in configuration")
        return True

    try:
        import redis

        client = redis.from_url(Config.REDIS_URL, socket_connect_timeout=2)
        client.ping()
        print(f"  ✓ Redis is available at {Config.REDIS_URL}")
        return True
    except Exception as e:
        print(f"  ⚠️  Redis not available: {e}")
        print("     Caching will be disabled. Set REDIS_ENABLED=false to suppress this warning.")
        return True  # Redis is optional


def check_env_file():
    """Check if .env file exists."""
    print("\n📄 Checking .env file...")
    env_path = Path(".env")
    if not env_path.exists():
        print("  ✗ .env file not found")
        print("     Copy .env.example to .env and configure it:")
        print("     cp .env.example .env")
        return False
    print("  ✓ .env file exists")
    return True


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("BRI Setup Validation")
    print("=" * 60)

    checks = [
        ("Python Version", check_python_version),
        ("Environment File", check_env_file),
        ("Dependencies", check_dependencies),
        ("Configuration", check_configuration),
        ("Directories", check_directories),
        ("Redis", check_redis),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ✗ Unexpected error in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All checks passed! You're ready to run BRI.")
        print("\nNext steps:")
        print("  1. Initialize database: python scripts/init_db.py")
        print("  2. Start MCP server: python mcp_server/main.py")
        print("  3. Start Streamlit UI: streamlit run app.py")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
