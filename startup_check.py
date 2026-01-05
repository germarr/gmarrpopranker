#!/usr/bin/env python3
"""
Startup verification script - run this BEFORE starting the server
Checks that everything is configured correctly
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

print("="*70)
print("🔍 MOVIE RANKER 2026 - STARTUP VERIFICATION")
print("="*70)

all_ok = True

# 1. Check .env file location
print("\n1️⃣  Checking .env file location...")
dotenv_path = find_dotenv(filename="app/.env", usecwd=True)
if dotenv_path:
    print(f"   ✅ .env file found at: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print("   ❌ .env file NOT found at app/.env")
    print("      Create app/.env with your configuration")
    all_ok = False

# 2. Check environment variables
print("\n2️⃣  Checking environment variables...")
auth_username = os.getenv("BASIC_AUTH_USERNAME")
auth_password = os.getenv("BASIC_AUTH_PASSWORD")
tmdb_key = os.getenv("TMDB_API_KEY")

if auth_username:
    print(f"   ✅ BASIC_AUTH_USERNAME: '{auth_username}'")
else:
    print("   ❌ BASIC_AUTH_USERNAME not set")
    all_ok = False

if auth_password:
    print(f"   ✅ BASIC_AUTH_PASSWORD: '{auth_password}'")
else:
    print("   ❌ BASIC_AUTH_PASSWORD not set")
    all_ok = False

if tmdb_key:
    print(f"   ✅ TMDB_API_KEY: {len(tmdb_key)} chars")
    is_bearer = tmdb_key.startswith('eyJ')
    print(f"      Type: {'Bearer Token (Read Access)' if is_bearer else 'API Key v3'}")
else:
    print("   ❌ TMDB_API_KEY not set")
    all_ok = False

# 3. Check database directory
print("\n3️⃣  Checking database directory...")
db_dir = Path("app/data")
if db_dir.exists():
    print(f"   ✅ Database directory exists: {db_dir}")
    db_file = db_dir / "app.db"
    if db_file.exists():
        print(f"   ✅ Database file exists: {db_file.stat().st_size} bytes")
    else:
        print(f"   ⚠️  Database file doesn't exist yet (will be created on first run)")
else:
    print(f"   ⚠️  Database directory doesn't exist yet (will be created on first run)")

# 4. Check images directory
print("\n4️⃣  Checking images directory...")
images_dir = Path("app/static/images")
if images_dir.exists():
    print(f"   ✅ Images directory exists: {images_dir}")
else:
    print(f"   ⚠️  Images directory doesn't exist yet")
    try:
        images_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created images directory")
    except Exception as e:
        print(f"   ❌ Failed to create images directory: {e}")
        all_ok = False

# 5. Test TMDB API if key is present
if tmdb_key:
    print("\n5️⃣  Testing TMDB API connection...")
    try:
        import json
        from urllib.request import urlopen, Request
        from urllib.parse import urlencode, quote_plus

        is_bearer = tmdb_key.startswith('eyJ')
        query = urlencode({"query": "Matrix", "include_adult": "false"}, quote_via=quote_plus)
        url = f"https://api.themoviedb.org/3/search/multi?{query}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {tmdb_key}"
        } if is_bearer else {"Accept": "application/json"}

        if not is_bearer:
            url += f"&api_key={tmdb_key}"

        request = Request(url, headers=headers)
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        if "results" in data and len(data["results"]) > 0:
            print(f"   ✅ TMDB API working! Found {len(data['results'])} results")
            first = data['results'][0]
            title = first.get('title') or first.get('name')
            print(f"      Sample result: {title}")
        else:
            print(f"   ⚠️  TMDB API returned unexpected response")
            all_ok = False

    except Exception as e:
        print(f"   ❌ TMDB API test failed: {e}")
        print(f"      Make sure your API key is valid")
        all_ok = False

# 6. Check main.py exists
print("\n6️⃣  Checking main.py...")
if Path("main.py").exists():
    print("   ✅ main.py exists")
else:
    print("   ❌ main.py not found")
    all_ok = False

# Final verdict
print("\n" + "="*70)
if all_ok:
    print("✅ ALL CHECKS PASSED!")
    print("\n🚀 You can now start the server:")
    print("   uvicorn main:app --reload")
    print("\n📝 Then navigate to:")
    print(f"   http://localhost:8000/crm")
    print(f"\n🔐 Login with:")
    print(f"   Username: {auth_username}")
    print(f"   Password: {auth_password}")
else:
    print("❌ SOME CHECKS FAILED!")
    print("\n⚠️  Fix the issues above before starting the server")
    sys.exit(1)

print("="*70)
