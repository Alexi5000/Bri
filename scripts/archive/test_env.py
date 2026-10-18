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
    print("✅ GROQ_API_KEY found")
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
    print("✅ Config.GROQ_API_KEY loaded")
else:
    print("❌ Config.GROQ_API_KEY is empty!")

print(f"   Model: {Config.GROQ_MODEL}")
print(f"   Temperature: {Config.GROQ_TEMPERATURE}")
print(f"   Max Tokens: {Config.GROQ_MAX_TOKENS}")

print("-" * 50)
print("\nEnvironment test complete!")
