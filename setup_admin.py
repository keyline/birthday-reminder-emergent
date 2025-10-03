#!/usr/bin/env python3

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import uuid
from datetime import datetime, timezone

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def setup_admin_user():
    """Setup john@example.com as super admin"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.birthday_reminder
    
    admin_email = "john@example.com"
    admin_password = "admin123"  # Change this to a secure password
    
    print(f"Setting up super admin: {admin_email}")
    
    # Check if admin user already exists
    existing_user = await db.users.find_one({"email": admin_email})
    
    if existing_user:
        print("Admin user already exists. Updating admin privileges...")
        # Update existing user to be admin
        await db.users.update_one(
            {"email": admin_email},
            {
                "$set": {
                    "is_admin": True,
                    "unlimited_whatsapp": True,
                    "unlimited_email": True,
                    "whatsapp_credits": 99999,
                    "email_credits": 99999,
                    "subscription_status": "active"
                }
            }
        )
        print("✅ Existing user updated with super admin privileges")
    else:
        print("Creating new super admin user...")
        # Create new admin user
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "full_name": "Super Admin",
            "phone_number": None,
            "password_hash": hash_password(admin_password),
            "is_admin": True,
            "subscription_status": "active",
            "whatsapp_credits": 99999,
            "email_credits": 99999,
            "unlimited_whatsapp": True,
            "unlimited_email": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.insert_one(admin_user)
        print("✅ Super admin user created successfully")
    
    # Verify admin user
    admin = await db.users.find_one({"email": admin_email})
    print(f"\n📋 Admin User Details:")
    print(f"   Email: {admin['email']}")
    print(f"   Name: {admin['full_name']}")
    print(f"   Is Admin: {admin['is_admin']}")
    print(f"   WhatsApp Credits: {admin['whatsapp_credits']}")
    print(f"   Email Credits: {admin['email_credits']}")
    print(f"   Unlimited WhatsApp: {admin['unlimited_whatsapp']}")
    print(f"   Unlimited Email: {admin['unlimited_email']}")
    
    # Get total users count
    total_users = await db.users.count_documents({})
    print(f"\n📊 Database Stats:")
    print(f"   Total Users: {total_users}")
    
    # Get total contacts count
    total_contacts = await db.contacts.count_documents({})
    print(f"   Total Contacts: {total_contacts}")
    
    # Get total templates count
    total_templates = await db.templates.count_documents({})
    print(f"   Total Templates: {total_templates}")
    
    client.close()
    print(f"\n🎉 Super admin setup complete!")
    print(f"Login credentials: {admin_email} / {admin_password}")

if __name__ == "__main__":
    asyncio.run(setup_admin_user())