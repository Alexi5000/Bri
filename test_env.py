"""Test environment variable loading."""

import os
from dotenv import load_dotenv

print("Testing environment variable loading...")
print("-" * 50)

# Load .env file
load_dotenv()

# Check if GROQ_API_KEY is loaded
groq_key = os.getenv("GROQ_API_KEY", "")

if groq_key:
    # Mask the key for security
    masked_key = groq_key[:10] + "..." + groq_key[-4:] if len(groq_key) > 14 else "***"
    print(f"✅ GROQ_API_KEY found: {masked_key}")
    print(f"   Length: {len(groq_key)} characters")
else:
    print("❌ GROQ_API_KEY not found!")
    print("\nPlease check:")
    print("1. .env file exists in the current directory")
    print("2. .env file contains: GROQ_API_KEY=your_key_here")
    print("3. No extra spaces or quotes around the key")

print("-" * 50)

# Test Config class
print("\nTesting Config class...")
from config import Config

if Config.GROQ_API_KEY:
    masked_key = Config.GROQ_API_KEY[:10] + "..." + Config.GROQ_API_KEY[-4:] if len(Config.GROQ_API_KEY) > 14 else "***"
    print(f"✅ Config.GROQ_API_KEY loaded: {masked_key}")
else:
    print("❌ Config.GROQ_API_KEY is empty!")

print(f"   Model: {Config.GROQ_MODEL}")
print(f"   Temperature: {Config.GROQ_TEMPERATURE}")
print(f"   Max Tokens: {Config.GROQ_MAX_TOKENS}")

print("-" * 50)
print("\nEnvironment test complete!")
