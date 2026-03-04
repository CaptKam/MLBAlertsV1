#!/usr/bin/env python3
"""Script to create a default admin user for the MLB Monitor application"""

import sys
import os
from app import app, db
import models

def create_default_admin():
    """Create a default admin user if none exists"""
    with app.app_context():
        # Check if any admin users exist
        admin_user = models.User.query.filter_by(is_admin=True).first()
        
        if admin_user:
            print(f"✓ Admin user already exists: {admin_user.username}")
            print(f"  Email: {admin_user.email}")
            return
        
        # Create default admin user
        print("Creating default admin user...")
        
        admin = models.User()
        admin.username = "admin"
        admin.email = "admin@mlbmonitor.com"
        admin.is_admin = True
        admin.set_password("admin123")  # Default password
        
        try:
            db.session.add(admin)
            db.session.commit()
            
            print("\n✅ Default admin user created successfully!")
            print("\n📋 Login Credentials:")
            print("=" * 40)
            print("Username: admin")
            print("Password: admin123")
            print("=" * 40)
            print("\n⚠️  Please change the password after first login!")
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.session.rollback()
            return False
        
        return True

if __name__ == "__main__":
    create_default_admin()