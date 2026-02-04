import sqlite3
import os
import requests
import time
import subprocess
import sys

def check_db():
    print("Checking Database...")
    if not os.path.exists("healthcare.db"):
        print("❌ healthcare.db not found!")
        return False
    
    conn = sqlite3.connect("healthcare.db")
    cursor = conn.cursor()
    
    try:
        users = cursor.execute("SELECT * FROM users").fetchall()
        print(f"✅ Users found: {len(users)}")
        patients = cursor.execute("SELECT * FROM patients").fetchall()
        print(f"✅ Patients found: {len(patients)}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ DB Check failed: {e}")
        conn.close()
        return False

def check_frontend_files():
    print("\nChecking Frontend Files...")
    files = [
        "static/index.html",
        "static/css/style.css",
        "static/js/app.js"
    ]
    all_exist = True
    for f in files:
        if os.path.exists(f):
            print(f"✅ Found {f}")
        else:
            print(f"❌ Missing {f}")
            all_exist = False
    return all_exist

if __name__ == "__main__":
    db_ok = check_db()
    fe_ok = check_frontend_files()
    
    if db_ok and fe_ok:
        print("\n🎉 Verification Passed! You can run the app with: uvicorn main:app --reload")
    else:
        print("\n❌ Verification Failed.")
