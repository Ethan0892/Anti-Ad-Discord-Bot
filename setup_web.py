#!/usr/bin/env python
"""
Setup script for Anti-Ad Bot Web Server
Creates initial owner account for user management
"""

import json
from pathlib import Path
from werkzeug.security import generate_password_hash
from datetime import datetime
import sys

WEB_DATA_PATH = Path(__file__).parent / 'web-data'
WEB_DATA_PATH.mkdir(parents=True, exist_ok=True)
USERS_FILE = WEB_DATA_PATH / 'users.json'

def create_owner_account(password=None):
    """Create initial owner account"""
    
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            if 'owner' in users:
                print("❌ Owner account already exists!")
                print(f"   Users file: {USERS_FILE}")
                return False
    else:
        users = {}
    
    if not password:
        print("🔐 Creating Owner Account for Anti-Ad Bot")
        print("=" * 50)
        
        while True:
            password = input("Enter owner password: ").strip()
            if len(password) < 6:
                print("❌ Password must be at least 6 characters")
                continue
            
            confirm = input("Confirm password: ").strip()
            if password != confirm:
                print("❌ Passwords don't match")
                continue
            break
    
    # Create owner account
    users['owner'] = {
        'password_hash': generate_password_hash(password),
        'role': 'owner',
        'created': datetime.now().isoformat()
    }
    
    # Save to file
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)
    
    print(f"\n✅ Owner account created successfully!")
    print(f"   Username: owner")
    print(f"   Role: owner (full access)")
    print(f"   Users file: {USERS_FILE}")
    print("\n💡 Next steps:")
    print("   1. Start web_server.py: python web_server.py")
    print("   2. Go to http://localhost:5000")
    print("   3. Login with username 'owner' and your password")
    print("   4. Create additional users/developers in the Users management page")
    
    return True

def add_developer(username, password=None):
    """Add a developer account"""
    
    if not USERS_FILE.exists():
        print("❌ Owner account doesn't exist yet!")
        print("   Run with --owner flag first")
        return False
    
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    if username in users:
        print(f"❌ User '{username}' already exists!")
        return False
    
    if not password:
        password = input(f"Enter password for {username}: ").strip()
    
    users[username] = {
        'password_hash': generate_password_hash(password),
        'role': 'dev',
        'created': datetime.now().isoformat()
    }
    
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)
    
    print(f"✅ Developer '{username}' added successfully!")
    return True

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Anti-Ad Bot web authentication')
    parser.add_argument('--owner', action='store_true', help='Create owner account')
    parser.add_argument('--add-dev', metavar='USERNAME', help='Add developer account')
    parser.add_argument('--password', metavar='PASSWORD', help='Set password directly (not recommended)')
    parser.add_argument('--list', action='store_true', help='List all users')
    
    args = parser.parse_args()
    
    if args.list:
        if USERS_FILE.exists():
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
            print("📋 Users in Anti-Ad Bot:")
            print("-" * 40)
            for username, data in users.items():
                created = data.get('created', 'Unknown')
                role = data.get('role', 'user')
                print(f"  {username:15} | {role:10} | {created}")
        else:
            print("❌ No users found. Create owner account first: --owner")
    
    elif args.owner:
        create_owner_account(args.password)
    
    elif args.add_dev:
        add_developer(args.add_dev, args.password)
    
    else:
        print("👋 Anti-Ad Bot Web Server Setup")
        print("=" * 50)
        print("\nUsage:")
        print("  python setup_web.py --owner           Create owner account")
        print("  python setup_web.py --add-dev NAME    Add developer account")
        print("  python setup_web.py --list            List all users")
        print("\nExamples:")
        print("  python setup_web.py --owner")
        print("  python setup_web.py --add-dev john")
        print("  python setup_web.py --add-dev jane --password mypass123")
        print("\nAfter setup:")
        print("  1. Run: python web_server.py")
        print("  2. Visit: http://localhost:5000")
        print("  3. Login with 'owner' and your password")
