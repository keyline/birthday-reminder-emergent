from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, date, timezone, timedelta
import bcrypt
from jose import JWTError, jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
from fastapi import UploadFile, File
import pandas as pd
import io
import asyncio
import re
from datetime import datetime as dt
import shutil
import json
import pytz
import random
import secrets
import string


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# LLM settings
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Admin Captcha Storage (in-memory, for production use Redis)
captcha_store = {}

# Create the main app without a prefix
app = FastAPI(title="Birthday Reminder SaaS")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    phone_number: Optional[str] = None
    subscription_status: str = "trial"
    is_admin: bool = False
    whatsapp_credits: int = 100  # Default credits
    email_credits: int = 100     # Default credits
    unlimited_whatsapp: bool = False
    unlimited_email: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactCreate(BaseModel):
    name: str
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    birthday: Optional[date] = None
    anniversary_date: Optional[date] = None
    message_tone: str = "normal"
    whatsapp_image: Optional[str] = None
    email_image: Optional[str] = None

class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    birthday: Optional[date] = None
    anniversary_date: Optional[date] = None
    message_tone: str = "normal"
    whatsapp_image: Optional[str] = None
    email_image: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TemplateCreate(BaseModel):
    name: str
    type: str  # "email" or "whatsapp"
    subject: Optional[str] = None
    content: str
    is_default: bool = False
    whatsapp_image_url: Optional[str] = None  # Default WhatsApp image
    email_image_url: Optional[str] = None     # Default Email image

class Template(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    type: str
    subject: Optional[str] = None
    content: str
    is_default: bool = False
    whatsapp_image_url: Optional[str] = None  # Default WhatsApp image
    email_image_url: Optional[str] = None     # Default Email image
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GenerateMessageRequest(BaseModel):
    contact_name: str
    occasion: str  # "birthday" or "anniversary"
    relationship: Optional[str] = "friend"
    tone: str = "normal"  # "normal", "business", "formal", "informal", "funny", "casual"

class BulkToneUpdate(BaseModel):
    contact_ids: List[str]
    message_tone: str

class MessagePreview(BaseModel):
    contact_id: str
    occasion: str
    message_type: str  # "whatsapp" or "email"
    generated_message: str
    custom_message: Optional[str] = None
    image_url: Optional[str] = None
    editable: bool = True

class CustomMessageRequest(BaseModel):
    contact_id: str
    occasion: str
    message_type: str
    custom_message: str
    image_url: Optional[str] = None

class MessageResponse(BaseModel):
    message: str

class CustomMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    contact_id: str
    occasion: str  # "birthday" or "anniversary"
    message_type: str  # "whatsapp" or "email"
    custom_message: str
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CustomMessageCreate(BaseModel):
    contact_id: str
    occasion: str
    message_type: str
    custom_message: str
    image_url: Optional[str] = None

class TestMessageRequest(BaseModel):
    contact_id: str
    occasion: str

class ReminderLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str  # YYYY-MM-DD format
    execution_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_users: int = 0
    messages_sent: int = 0
    whatsapp_sent: int = 0
    email_sent: int = 0
    errors: List[str] = []

class DailyReminderStats(BaseModel):
    date: str
    total_executions: int
    total_users_processed: int
    total_messages_sent: int
    whatsapp_messages: int
    email_messages: int
    errors: List[str]

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None

class BulkUploadResponse(BaseModel):
    total_rows: int
    successful_imports: int
    failed_imports: int
    errors: List[str]
    imported_contacts: List[Contact]

class UserSettingsCreate(BaseModel):
    # DigitalSMS API
    digitalsms_api_key: Optional[str] = None
    whatsapp_sender_number: Optional[str] = None  # 10-digit sender phone number
    
    # Email settings
    email_api_key: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    
    # Scheduling settings
    daily_send_time: Optional[str] = "09:00"  # HH:MM format
    timezone: Optional[str] = "UTC"
    execution_report_enabled: bool = True
    execution_report_email: Optional[str] = None

class UserSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # DigitalSMS API
    digitalsms_api_key: Optional[str] = None
    whatsapp_sender_number: Optional[str] = None  # 10-digit sender phone number
    
    # Email settings
    email_api_key: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    
    # Scheduling settings
    daily_send_time: str = "09:00"
    timezone: str = "UTC"
    execution_report_enabled: bool = True
    execution_report_email: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

class UserStats(BaseModel):
    id: str
    email: str
    full_name: str
    subscription_status: str
    subscription_expires: Optional[datetime] = None
    is_admin: bool
    created_at: datetime
    contacts_count: int
    templates_count: int
    last_login: Optional[datetime] = None
    total_usage: int
    whatsapp_credits: int
    email_credits: int
    unlimited_whatsapp: bool
    unlimited_email: bool

class CreditUpdate(BaseModel):
    whatsapp_credits: Optional[int] = None
    email_credits: Optional[int] = None
    unlimited_whatsapp: Optional[bool] = None
    unlimited_email: Optional[bool] = None

class AdminDashboardStats(BaseModel):
    total_users: int
    active_subscriptions: int
    trial_users: int
    expired_users: int
    total_contacts: int
    total_templates: int
    monthly_revenue: float
    recent_signups: int  # Last 30 days
    churn_rate: float

# New Admin System Models
class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CaptchaResponse(BaseModel):
    captcha_id: str
    question: str

class UserWithContactCount(BaseModel):
    id: str
    email: str
    full_name: str
    phone_number: Optional[str]
    subscription_status: str
    whatsapp_credits: int
    email_credits: int
    unlimited_whatsapp: bool
    unlimited_email: bool
    created_at: datetime
    contact_count: int

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    phone_number: Optional[str] = None

class SubscriptionUpdateRequest(BaseModel):
    subscription_status: Optional[str] = None
    whatsapp_credits: Optional[int] = None
    email_credits: Optional[int] = None
    unlimited_whatsapp: Optional[bool] = None
    unlimited_email: Optional[bool] = None

# Helper functions
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin authentication"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: str = payload.get("admin_id")
        if admin_id is None:
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        admin = await db.admins.find_one({"id": admin_id})
        if not admin:
            raise HTTPException(status_code=401, detail="Admin not found")
        
        return AdminUser(**admin)
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate admin credentials")

def generate_math_captcha():
    """Generate a simple math captcha"""
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    captcha_id = str(uuid.uuid4())
    answer = num1 + num2
    
    # Store captcha with 5 minute expiration
    captcha_store[captcha_id] = {
        "answer": answer,
        "created_at": datetime.now(timezone.utc)
    }
    
    # Clean old captchas
    current_time = datetime.now(timezone.utc)
    expired_keys = [
        key for key, value in captcha_store.items()
        if (current_time - value["created_at"]).total_seconds() > 300
    ]
    for key in expired_keys:
        del captcha_store[key]
    
    return {
        "captcha_id": captcha_id,
        "question": f"What is {num1} + {num2}?"
    }

def verify_captcha(captcha_id: str, answer: str) -> bool:
    """Verify captcha answer"""
    if captcha_id not in captcha_store:
        return False
    
    stored_data = captcha_store[captcha_id]
    is_valid = str(stored_data["answer"]) == answer
    
    # Remove captcha after verification attempt
    del captcha_store[captcha_id]
    
    return is_valid

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def prepare_for_mongo(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, date) and not isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, datetime):
                data[key] = value.isoformat() if value.tzinfo else value.replace(tzinfo=timezone.utc).isoformat()
    return data

def parse_from_mongo(item):
    if isinstance(item, dict):
        # Handle MongoDB ObjectId conversion
        if '_id' in item:
            del item['_id']  # Remove MongoDB _id field
        
        for key, value in item.items():
            # Convert ObjectId to string if present
            if hasattr(value, '__class__') and value.__class__.__name__ == 'ObjectId':
                item[key] = str(value)
            elif key in ['birthday', 'anniversary_date'] and isinstance(value, str):
                try:
                    item[key] = datetime.fromisoformat(value).date()
                except:
                    pass
            elif key in ['created_at'] and isinstance(value, str):
                try:
                    item[key] = datetime.fromisoformat(value)
                except:
                    pass
    return item

# Authentication Routes
@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name
    )
    
    user_dict = user.dict()
    user_dict["password_hash"] = hashed_password
    user_dict = prepare_for_mongo(user_dict)
    
    await db.users.insert_one(user_dict)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = parse_from_mongo(user)
    user_obj = User(**user)
    
    access_token = create_access_token(data={"sub": user_obj.id})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_obj
    )

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# User Profile Routes
@api_router.put("/user/profile", response_model=User)
async def update_user_profile(profile_data: UserProfileUpdate, current_user: User = Depends(get_current_user)):
    """Update user profile information"""
    update_fields = {}
    
    # Only update fields that are provided
    if profile_data.full_name is not None:
        update_fields["full_name"] = profile_data.full_name.strip()
    
    if profile_data.email is not None:
        # Check if email is already taken by another user
        existing_user = await db.users.find_one({
            "email": str(profile_data.email).lower(), 
            "id": {"$ne": current_user.id}
        })
        if existing_user:
            raise HTTPException(status_code=400, detail="Email address is already in use")
        update_fields["email"] = str(profile_data.email).lower()
    
    if profile_data.phone_number is not None:
        # Country-specific phone number validation
        phone = profile_data.phone_number.strip()
        if phone:
            # Clean the phone number - remove spaces, dashes, parentheses
            cleaned_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            
            # Remove +91 country code for India if present
            if cleaned_phone.startswith("+91"):
                cleaned_phone = cleaned_phone[3:]
            elif cleaned_phone.startswith("91") and len(cleaned_phone) == 12:
                cleaned_phone = cleaned_phone[2:]
            
            # Validate for Indian phone numbers (10 digits)
            if cleaned_phone:
                if not cleaned_phone.isdigit():
                    raise HTTPException(status_code=400, detail="Phone number must contain only digits")
                
                if len(cleaned_phone) != 10:
                    raise HTTPException(status_code=400, detail="Indian phone numbers must be exactly 10 digits")
                
                # Additional validation for Indian mobile numbers (should start with 6-9)
                if not cleaned_phone[0] in ['6', '7', '8', '9']:
                    raise HTTPException(status_code=400, detail="Indian mobile numbers must start with 6, 7, 8, or 9")
                
                update_fields["phone_number"] = cleaned_phone
            else:
                update_fields["phone_number"] = None
        else:
            update_fields["phone_number"] = None
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    # Update user in database
    result = await db.users.update_one(
        {"id": current_user.id},
        {"$set": update_fields}
    )
    
    # Check if user exists (matched_count > 0 means user was found)
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Fetch and return updated user
    updated_user = await db.users.find_one({"id": current_user.id})
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return User(**parse_from_mongo(updated_user))

@api_router.get("/user/profile", response_model=User)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    user = await db.users.find_one({"id": current_user.id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return User(**parse_from_mongo(user))

# Contact Routes
@api_router.post("/contacts", response_model=Contact)
async def create_contact(contact_data: ContactCreate, current_user: User = Depends(get_current_user)):
    contact = Contact(
        user_id=current_user.id,
        **contact_data.dict()
    )
    
    contact_dict = prepare_for_mongo(contact.dict())
    await db.contacts.insert_one(contact_dict)
    
    return contact

@api_router.get("/contacts", response_model=List[Contact])
async def get_contacts(current_user: User = Depends(get_current_user)):
    contacts = await db.contacts.find({"user_id": current_user.id}).to_list(1000)
    return [Contact(**parse_from_mongo(contact)) for contact in contacts]

@api_router.get("/contacts/{contact_id}", response_model=Contact)
async def get_contact(contact_id: str, current_user: User = Depends(get_current_user)):
    contact = await db.contacts.find_one({"id": contact_id, "user_id": current_user.id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return Contact(**parse_from_mongo(contact))

@api_router.put("/contacts/{contact_id}", response_model=Contact)
async def update_contact(contact_id: str, contact_data: ContactCreate, current_user: User = Depends(get_current_user)):
    contact = await db.contacts.find_one({"id": contact_id, "user_id": current_user.id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    update_data = prepare_for_mongo(contact_data.dict(exclude_unset=True))
    await db.contacts.update_one({"id": contact_id}, {"$set": update_data})
    
    updated_contact = await db.contacts.find_one({"id": contact_id})
    return Contact(**parse_from_mongo(updated_contact))

@api_router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, current_user: User = Depends(get_current_user)):
    result = await db.contacts.delete_one({"id": contact_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}

@api_router.put("/contacts/bulk-tone-update")
async def bulk_update_tone(bulk_update: BulkToneUpdate, current_user: User = Depends(get_current_user)):
    result = await db.contacts.update_many(
        {
            "id": {"$in": bulk_update.contact_ids},
            "user_id": current_user.id
        },
        {"$set": {"message_tone": bulk_update.message_tone}}
    )
    
    return {
        "message": f"Updated tone to '{bulk_update.message_tone}' for {result.modified_count} contacts",
        "updated_count": result.modified_count
    }

# Bulk Upload Contacts from Excel
@api_router.post("/contacts/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_contacts(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    try:
        # Read the uploaded file
        contents = await file.read()
        
        # Parse Excel file
        try:
            # Read Excel with specific dtype for whatsapp column to preserve phone numbers
            df = pd.read_excel(io.BytesIO(contents), dtype={'whatsapp': str})
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading Excel file: {str(e)}")
        
        # Validate required columns
        required_columns = ['name', 'birthday', 'anniversary', 'email', 'whatsapp']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}. Expected columns: name, birthday, anniversary, email, whatsapp"
            )
        
        # Get existing contacts for duplicate checking
        existing_contacts = await db.contacts.find({"user_id": current_user.id}).to_list(1000)
        existing_emails = {contact.get('email', '').lower() for contact in existing_contacts if contact.get('email')}
        existing_whatsapp = {contact.get('whatsapp', '') for contact in existing_contacts if contact.get('whatsapp')}
        
        # Process rows
        successful_imports = []
        failed_imports = []
        errors = []
        
        for index, row in df.iterrows():
            row_number = index + 2  # Excel rows start from 1, plus header
            
            try:
                # Extract and clean data
                name = str(row['name']).strip() if pd.notna(row['name']) else ""
                birthday = row['birthday'] if pd.notna(row['birthday']) else None
                anniversary = row['anniversary'] if pd.notna(row['anniversary']) else None
                email = str(row['email']).strip() if pd.notna(row['email']) and str(row['email']).strip().lower() != 'nan' else ""
                whatsapp = str(row['whatsapp']).strip() if pd.notna(row['whatsapp']) and str(row['whatsapp']).strip().lower() != 'nan' else ""
                
                # Validation: Name is mandatory
                if not name or name.lower() == 'nan':
                    errors.append(f"Row {row_number}: Name is required")
                    failed_imports.append(row_number)
                    continue
                
                # Validation: At least one contact method (email or whatsapp) is required
                if not email and not whatsapp:
                    errors.append(f"Row {row_number}: Either email or WhatsApp number is required")
                    failed_imports.append(row_number)
                    continue
                
                # Validation: Email format (if provided)
                if email:
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, email):
                        errors.append(f"Row {row_number}: Invalid email format")
                        failed_imports.append(row_number)
                        continue
                    
                    # Check for duplicate email within user's contacts
                    if email.lower() in existing_emails:
                        errors.append(f"Row {row_number}: Email '{email}' already exists in your contacts")
                        failed_imports.append(row_number)
                        continue
                
                # Validation: WhatsApp format (if provided)
                if whatsapp:
                    # Basic phone number validation (digits, spaces, +, -, (, ))
                    phone_pattern = r'^[\+]?[1-9][\d\s\-\(\)]{7,20}$'
                    clean_whatsapp = re.sub(r'[\s\-\(\)]', '', whatsapp)
                    if not re.match(phone_pattern, whatsapp) or len(clean_whatsapp) < 7:
                        errors.append(f"Row {row_number}: Invalid WhatsApp number format")
                        failed_imports.append(row_number)
                        continue
                    
                    # Check for duplicate WhatsApp within user's contacts
                    if whatsapp in existing_whatsapp:
                        errors.append(f"Row {row_number}: WhatsApp number '{whatsapp}' already exists in your contacts")
                        failed_imports.append(row_number)
                        continue
                
                # Validation: At least one date (birthday or anniversary) is required
                if not birthday and not anniversary:
                    errors.append(f"Row {row_number}: Either birthday or anniversary is required")
                    failed_imports.append(row_number)
                    continue
                
                # Parse dates with flexible format support
                birthday_date = None
                anniversary_date = None
                
                if birthday:
                    try:
                        if isinstance(birthday, str):
                            birthday = birthday.strip()
                            # Try DD-MM format first (without year)
                            if re.match(r'^\d{1,2}-\d{1,2}$', birthday):
                                day, month = birthday.split('-')
                                # Use current year as default for birthday without year
                                current_year = dt.now().year
                                birthday_date = dt(current_year, int(month), int(day)).date()
                            # Try DD-MM-YYYY format
                            elif re.match(r'^\d{1,2}-\d{1,2}-\d{4}$', birthday):
                                day, month, year = birthday.split('-')
                                birthday_date = dt(int(year), int(month), int(day)).date()
                            else:
                                # Fallback to pandas parsing for other formats
                                birthday_date = pd.to_datetime(birthday).date()
                        else:
                            birthday_date = birthday.date() if hasattr(birthday, 'date') else birthday
                    except Exception as e:
                        errors.append(f"Row {row_number}: Invalid birthday date format. Use DD-MM or DD-MM-YYYY format")
                        failed_imports.append(row_number)
                        continue
                
                if anniversary:
                    try:
                        if isinstance(anniversary, str):
                            anniversary = anniversary.strip()
                            # Try DD-MM format first (without year)
                            if re.match(r'^\d{1,2}-\d{1,2}$', anniversary):
                                day, month = anniversary.split('-')
                                # Use current year as default for anniversary without year
                                current_year = dt.now().year
                                anniversary_date = dt(current_year, int(month), int(day)).date()
                            # Try DD-MM-YYYY format
                            elif re.match(r'^\d{1,2}-\d{1,2}-\d{4}$', anniversary):
                                day, month, year = anniversary.split('-')
                                anniversary_date = dt(int(year), int(month), int(day)).date()
                            else:
                                # Fallback to pandas parsing for other formats
                                anniversary_date = pd.to_datetime(anniversary).date()
                        else:
                            anniversary_date = anniversary.date() if hasattr(anniversary, 'date') else anniversary
                    except Exception as e:
                        errors.append(f"Row {row_number}: Invalid anniversary date format. Use DD-MM or DD-MM-YYYY format")
                        failed_imports.append(row_number)
                        continue
                
                # Create contact
                contact = Contact(
                    user_id=current_user.id,
                    name=name,
                    email=email if email else None,
                    whatsapp=whatsapp if whatsapp else None,
                    birthday=birthday_date,
                    anniversary_date=anniversary_date
                )
                
                # Add to existing contact tracking to prevent duplicates within the same upload
                if email:
                    existing_emails.add(email.lower())
                if whatsapp:
                    existing_whatsapp.add(whatsapp)
                
                # Save to database
                contact_dict = prepare_for_mongo(contact.dict())
                await db.contacts.insert_one(contact_dict)
                
                successful_imports.append(contact)
                
            except Exception as e:
                errors.append(f"Row {row_number}: Unexpected error - {str(e)}")
                failed_imports.append(row_number)
        
        return BulkUploadResponse(
            total_rows=len(df),
            successful_imports=len(successful_imports),
            failed_imports=len(failed_imports),
            errors=errors,
            imported_contacts=successful_imports
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Template Routes
@api_router.post("/templates", response_model=Template)
async def create_template(template_data: TemplateCreate, current_user: User = Depends(get_current_user)):
    template = Template(
        user_id=current_user.id,
        **template_data.dict()
    )
    
    template_dict = prepare_for_mongo(template.dict())
    await db.templates.insert_one(template_dict)
    
    return template

@api_router.get("/templates", response_model=List[Template])
async def get_templates(current_user: User = Depends(get_current_user)):
    templates = await db.templates.find({"user_id": current_user.id}).to_list(1000)
    return [Template(**parse_from_mongo(template)) for template in templates]

@api_router.put("/templates/{template_id}", response_model=Template)
async def update_template(template_id: str, template_data: TemplateCreate, current_user: User = Depends(get_current_user)):
    template = await db.templates.find_one({"id": template_id, "user_id": current_user.id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = prepare_for_mongo(template_data.dict(exclude_unset=True))
    await db.templates.update_one({"id": template_id}, {"$set": update_data})
    
    updated_template = await db.templates.find_one({"id": template_id})
    return Template(**parse_from_mongo(updated_template))

@api_router.delete("/templates/{template_id}")
async def delete_template(template_id: str, current_user: User = Depends(get_current_user)):
    result = await db.templates.delete_one({"id": template_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted successfully"}

# Enhanced AI Message Generation with Tone Variations
@api_router.post("/generate-message", response_model=MessageResponse)
async def generate_message(request: GenerateMessageRequest, current_user: User = Depends(get_current_user)):
    try:
        # Tone-specific system messages and prompts
        tone_configs = {
            "normal": {
                "system": "You are a friendly assistant that generates warm, heartfelt messages for special occasions.",
                "style": "warm and friendly"
            },
            "business": {
                "system": "You are a professional assistant that generates polite, respectful business messages.",
                "style": "professional and courteous"
            },
            "formal": {
                "system": "You are a formal assistant that generates elegant, sophisticated messages.",
                "style": "formal and respectful"
            },
            "informal": {
                "system": "You are a casual assistant that generates relaxed, friendly messages.",
                "style": "casual and relaxed"
            },
            "funny": {
                "system": "You are a humorous assistant that generates light-hearted, amusing messages while staying appropriate.",
                "style": "funny and entertaining"
            },
            "casual": {
                "system": "You are a laid-back assistant that generates easy-going, casual messages.",
                "style": "casual and easy-going"
            }
        }
        
        tone_config = tone_configs.get(request.tone, tone_configs["normal"])
        
        # Initialize LLM chat with tone-specific system message
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"user_{current_user.id}_message_gen_{request.tone}",
            system_message=tone_config["system"]
        ).with_model("openai", "gpt-4o")
        
        # Create tone-specific prompt
        prompt = f"Generate a {tone_config['style']} {request.occasion} message for {request.contact_name}. "
        prompt += f"The relationship is: {request.relationship}. "
        prompt += f"Make it {tone_config['style']} and appropriate for the occasion. "
        
        if request.tone == "funny":
            prompt += "Include some light humor but keep it tasteful and appropriate. "
        elif request.tone == "business":
            prompt += "Keep it professional yet warm, suitable for a business relationship. "
        elif request.tone == "formal":
            prompt += "Use elegant language and formal expressions. "
        elif request.tone == "informal":
            prompt += "Use casual language and be conversational. "
        elif request.tone == "casual":
            prompt += "Keep it simple, laid-back, and easy-going. "
        
        prompt += "Keep it between 30-100 words. Do not include greetings like 'Dear' or signatures."
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        return MessageResponse(message=response)
        
    except Exception as e:
        logging.error(f"Error generating message: {str(e)}")
        # Tone-specific fallback messages
        fallback_messages = {
            "birthday": {
                "normal": f"Happy Birthday, {request.contact_name}! Wishing you a wonderful day filled with joy and happiness!",
                "business": f"Happy Birthday, {request.contact_name}! We hope you have a wonderful celebration and a successful year ahead.",
                "formal": f"Wishing you a very Happy Birthday, {request.contact_name}. May this special day bring you joy and prosperity.",
                "informal": f"Hey {request.contact_name}! Happy Birthday! Hope you have an awesome day!",
                "funny": f"Happy Birthday, {request.contact_name}! Another year older and still fabulous! Time to eat cake and pretend calories don't count!",
                "casual": f"Happy Birthday {request.contact_name}! Have a great one and enjoy your day!"
            },
            "anniversary": {
                "normal": f"Happy Anniversary, {request.contact_name}! Celebrating your special day with you!",
                "business": f"Happy Anniversary, {request.contact_name}! Congratulations on this milestone.",
                "formal": f"Congratulations on your Anniversary, {request.contact_name}. Wishing you continued happiness.",
                "informal": f"Happy Anniversary {request.contact_name}! Hope you two have a blast celebrating!",
                "funny": f"Happy Anniversary {request.contact_name}! Another year of successfully putting up with each other - impressive!",
                "casual": f"Happy Anniversary {request.contact_name}! Enjoy your special day!"
            }
        }
        
        occasion_messages = fallback_messages.get(request.occasion, {})
        fallback_message = occasion_messages.get(request.tone, f"Happy {request.occasion}, {request.contact_name}!")
        
        return MessageResponse(message=fallback_message)

@api_router.post("/generate-message-preview")
async def generate_message_preview(contact_id: str, occasion: str, message_type: str, current_user: User = Depends(get_current_user)):
    # Get contact details
    contact = await db.contacts.find_one({"id": contact_id, "user_id": current_user.id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact = parse_from_mongo(contact)
    
    # Generate message using contact's tone preference
    message_request = GenerateMessageRequest(
        contact_name=contact["name"],
        occasion=occasion,
        relationship="friend",
        tone=contact.get("message_tone", "normal")
    )
    
    message_response = await generate_message(message_request, current_user)
    
    # Get appropriate image
    image_url = None
    if message_type == "whatsapp" and contact.get("whatsapp_image"):
        image_url = contact["whatsapp_image"]
    elif message_type == "email" and contact.get("email_image"):
        image_url = contact["email_image"]
    else:
        # Use default image (we'll implement default image management later)
        image_url = "/default-celebration.jpg"
    
    return MessagePreview(
        contact_id=contact_id,
        occasion=occasion,
        message_type=message_type,
        generated_message=message_response.message,
        image_url=image_url,
        editable=True
    )

# Dashboard/Analytics Routes
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    total_contacts = await db.contacts.count_documents({"user_id": current_user.id})
    total_templates = await db.templates.count_documents({"user_id": current_user.id})
    
    # Get upcoming birthdays and anniversaries (next 30 days)
    today = date.today()
    upcoming_events = []
    
    contacts = await db.contacts.find({"user_id": current_user.id}).to_list(1000)
    for contact in contacts:
        contact = parse_from_mongo(contact)
        if contact.get('birthday'):
            birthday = contact['birthday']
            if isinstance(birthday, str):
                birthday = datetime.fromisoformat(birthday).date()
            # Calculate next birthday occurrence
            this_year_birthday = birthday.replace(year=today.year)
            if this_year_birthday < today:
                this_year_birthday = birthday.replace(year=today.year + 1)
            
            days_until = (this_year_birthday - today).days
            if days_until <= 30:
                upcoming_events.append({
                    "contact_name": contact['name'],
                    "event_type": "birthday",
                    "date": this_year_birthday.isoformat(),
                    "days_until": days_until
                })
        
        if contact.get('anniversary_date'):
            anniversary = contact['anniversary_date']
            if isinstance(anniversary, str):
                anniversary = datetime.fromisoformat(anniversary).date()
            # Calculate next anniversary occurrence
            this_year_anniversary = anniversary.replace(year=today.year)
            if this_year_anniversary < today:
                this_year_anniversary = anniversary.replace(year=today.year + 1)
            
            days_until = (this_year_anniversary - today).days
            if days_until <= 30:
                upcoming_events.append({
                    "contact_name": contact['name'],
                    "event_type": "anniversary",
                    "date": this_year_anniversary.isoformat(),
                    "days_until": days_until
                })
    
    # Sort by days until
    upcoming_events.sort(key=lambda x: x['days_until'])
    
    return {
        "total_contacts": total_contacts,
        "total_templates": total_templates,
        "upcoming_events": upcoming_events[:10]  # Limit to 10 most recent
    }

# Admin Routes
@api_router.get("/admin/dashboard", response_model=AdminDashboardStats)
async def get_admin_dashboard(admin_user: User = Depends(get_admin_user)):
    # Get all users
    users = await db.users.find().to_list(10000)
    
    # Calculate stats
    total_users = len(users)
    active_subscriptions = len([u for u in users if u.get('subscription_status') == 'active'])
    trial_users = len([u for u in users if u.get('subscription_status') == 'trial'])
    expired_users = len([u for u in users if u.get('subscription_status') in ['expired', 'cancelled']])
    
    # Get total contacts and templates
    total_contacts = await db.contacts.count_documents({})
    total_templates = await db.templates.count_documents({})
    
    # Calculate revenue (assuming $9.99 per active subscription)
    monthly_revenue = active_subscriptions * 9.99
    
    # Recent signups (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_signups = len([u for u in users if datetime.fromisoformat(u.get('created_at', '2020-01-01T00:00:00+00:00')) > thirty_days_ago])
    
    # Simple churn rate calculation (expired/cancelled out of total)
    churn_rate = (expired_users / total_users * 100) if total_users > 0 else 0.0
    
    return AdminDashboardStats(
        total_users=total_users,
        active_subscriptions=active_subscriptions,
        trial_users=trial_users,
        expired_users=expired_users,
        total_contacts=total_contacts,
        total_templates=total_templates,
        monthly_revenue=monthly_revenue,
        recent_signups=recent_signups,
        churn_rate=churn_rate
    )

# Duplicate endpoint removed - using enhanced version below

@api_router.put("/admin/users/{user_id}/subscription")
async def update_user_subscription(user_id: str, subscription_status: str, admin_user: User = Depends(get_admin_user)):
    # Calculate expiry date based on subscription status
    subscription_expires = None
    if subscription_status == 'active':
        subscription_expires = datetime.now(timezone.utc) + timedelta(days=30)
    elif subscription_status == 'trial':
        subscription_expires = datetime.now(timezone.utc) + timedelta(days=14)
    
    update_data = {"subscription_status": subscription_status}
    if subscription_expires:
        update_data["subscription_expires"] = subscription_expires.isoformat()
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Subscription updated successfully", "expires": subscription_expires}

@api_router.put("/admin/users/{user_id}/expiry")
async def update_user_expiry(user_id: str, expiry_date: str, admin_user: User = Depends(get_admin_user)):
    try:
        # Parse the expiry date
        expiry_datetime = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
        
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": {"subscription_expires": expiry_datetime.isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "Expiry date updated successfully", "expires": expiry_datetime}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin_user: User = Depends(get_admin_user)):
    # Don't allow deleting admin users
    user_to_delete = await db.users.find_one({"id": user_id})
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_to_delete.get('is_admin', False):
        raise HTTPException(status_code=400, detail="Cannot delete admin users")
    
    # Delete user's data
    await db.contacts.delete_many({"user_id": user_id})
    await db.templates.delete_many({"user_id": user_id})
    
    # Delete user
    result = await db.users.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User and all associated data deleted successfully"}

@api_router.post("/admin/users/{user_id}/extend")
async def extend_user_subscription(user_id: str, days: int, admin_user: User = Depends(get_admin_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get current expiry or use current time
    current_expiry = user.get('subscription_expires')
    if current_expiry:
        if isinstance(current_expiry, str):
            current_expiry = datetime.fromisoformat(current_expiry.replace('Z', '+00:00'))
        new_expiry = current_expiry + timedelta(days=days)
    else:
        new_expiry = datetime.now(timezone.utc) + timedelta(days=days)
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"subscription_expires": new_expiry.isoformat()}}
    )
    
    return {"message": f"Subscription extended by {days} days", "new_expiry": new_expiry}

@api_router.put("/admin/users/{user_id}/credits")
async def update_user_credits(user_id: str, credit_update: CreditUpdate, admin_user: User = Depends(get_admin_user)):
    update_data = {}
    
    if credit_update.whatsapp_credits is not None:
        update_data["whatsapp_credits"] = credit_update.whatsapp_credits
    if credit_update.email_credits is not None:
        update_data["email_credits"] = credit_update.email_credits
    if credit_update.unlimited_whatsapp is not None:
        update_data["unlimited_whatsapp"] = credit_update.unlimited_whatsapp
    if credit_update.unlimited_email is not None:
        update_data["unlimited_email"] = credit_update.unlimited_email
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User credits updated successfully", "updated_fields": update_data}

@api_router.post("/admin/users/{user_id}/add-credits")
async def add_credits_to_user(user_id: str, whatsapp_credits: int = 0, email_credits: int = 0, admin_user: User = Depends(get_admin_user)):
    # Get current user credits
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_whatsapp_credits = user.get("whatsapp_credits", 0) + whatsapp_credits
    new_email_credits = user.get("email_credits", 0) + email_credits
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "whatsapp_credits": new_whatsapp_credits,
            "email_credits": new_email_credits
        }}
    )
    
    return {
        "message": f"Added {whatsapp_credits} WhatsApp and {email_credits} email credits",
        "new_whatsapp_credits": new_whatsapp_credits,
        "new_email_credits": new_email_credits
    }

@api_router.post("/admin/make-admin/{user_email}")
async def make_user_admin(user_email: str):
    """Temporary endpoint to make a user admin - should be removed in production"""
    result = await db.users.update_one(
        {"email": user_email},
        {"$set": {"is_admin": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User {user_email} is now an admin"}

# User Settings Routes
@api_router.get("/settings", response_model=UserSettings)
async def get_user_settings(current_user: User = Depends(get_current_user)):
    settings = await db.user_settings.find_one({"user_id": current_user.id})
    
    if not settings:
        # Create default settings for user
        default_settings = UserSettings(
            user_id=current_user.id,
            execution_report_email=current_user.email
        )
        settings_dict = prepare_for_mongo(default_settings.dict())
        await db.user_settings.insert_one(settings_dict)
        return default_settings
    
    return UserSettings(**parse_from_mongo(settings))

@api_router.put("/settings", response_model=UserSettings)
async def update_user_settings(settings_data: UserSettingsCreate, current_user: User = Depends(get_current_user)):
    # Update timestamp
    update_data = settings_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    # If execution_report_email not provided, use user's email
    if not update_data.get("execution_report_email"):
        update_data["execution_report_email"] = current_user.email
    
    # Prepare for MongoDB
    update_data = prepare_for_mongo(update_data)
    
    # Update or create settings
    result = await db.user_settings.update_one(
        {"user_id": current_user.id},
        {"$set": update_data},
        upsert=True
    )
    
    # Fetch updated settings
    settings = await db.user_settings.find_one({"user_id": current_user.id})
    return UserSettings(**parse_from_mongo(settings))

@api_router.post("/settings/test-whatsapp")
async def test_whatsapp_config(current_user: User = Depends(get_current_user)):
    """Send actual test WhatsApp message to user's phone number"""
    settings = await db.user_settings.find_one({"user_id": current_user.id})
    
    if not settings:
        return {"status": "error", "message": "WhatsApp settings not found"}
    
    # Check if required configuration is present
    api_key = settings.get("digitalsms_api_key")
    sender_number = settings.get("whatsapp_sender_number")
    
    if not api_key:
        return {"status": "error", "message": "DigitalSMS API key not configured"}
    
    if not sender_number:
        return {"status": "error", "message": "WhatsApp sender phone number not configured"}
    
    # Get user's phone number from profile
    user = await db.users.find_one({"id": current_user.id})
    if not user:
        return {"status": "error", "message": "User profile not found"}
    
    user_phone = user.get("phone_number")
    if not user_phone:
        return {"status": "error", "message": "Please add your phone number in Account settings to receive test messages"}
    
    # Validate user's phone number format
    if len(user_phone) != 10 or not user_phone.isdigit() or user_phone[0] not in ['6', '7', '8', '9']:
        return {"status": "error", "message": "Invalid phone number in your profile. Please update it in Account settings"}
    
    try:
        # Send actual test message using our WhatsApp function
        test_message = f"🧪 WhatsApp Test from ReminderAI\n\n✅ Your DigitalSMS API configuration is working perfectly!\n\nAPI Key: {api_key[:8]}...\nSender Number: {sender_number}\nTest sent at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n🎉 You're all set to send birthday and anniversary reminders!"
        
        result = await send_whatsapp_message(
            user_id=current_user.id,
            phone_number=user_phone,
            message=test_message,
            occasion="birthday"  # Default for test messages
        )
        
        if result["status"] == "success":
            return {
                "status": "success", 
                "message": f"Test message sent successfully to {user_phone}! Check your WhatsApp.",
                "provider": "digitalsms",
                "details": {
                    "recipient": user_phone,
                    "sender": sender_number,
                    "api_response": result["message"]
                }
            }
        else:
            return {
                "status": "error", 
                "message": f"Failed to send test message: {result['message']}",
                "provider": "digitalsms"
            }
            
    except Exception as e:
        return {"status": "error", "message": f"WhatsApp test error: {str(e)}"}

@api_router.post("/settings/test-email")
async def test_email_config(current_user: User = Depends(get_current_user)):
    settings = await db.user_settings.find_one({"user_id": current_user.id})
    
    if not settings or not settings.get("email_api_key") or not settings.get("sender_email"):
        raise HTTPException(status_code=400, detail="Email configuration not found")
    
    # Test Brevo API configuration
    try:
        import requests
        
        api_key = settings["email_api_key"]
        sender_email = settings["sender_email"]
        sender_name = settings.get("sender_name", "ReminderAI")
        
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        
        # Test email payload
        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email
            },
            "to": [
                {
                    "email": current_user.email,
                    "name": current_user.full_name
                }
            ],
            "subject": "ReminderAI - Email Configuration Test",
            "htmlContent": "<html><body><h2>Email Configuration Test</h2><p>Your email API configuration is working correctly!</p><p>This is a test email to verify your Brevo API setup.</p></body></html>"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            return {"status": "success", "message": "Email API configuration is valid and test email sent"}
        else:
            return {"status": "error", "message": f"Email API test failed: {response.text}"}
            
    except Exception as e:
        return {"status": "error", "message": f"Email API test error: {str(e)}"}

# Credit Management Routes
@api_router.get("/credits")
async def get_user_credits(current_user: User = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user.id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "whatsapp_credits": user.get("whatsapp_credits", 0),
        "email_credits": user.get("email_credits", 0),
        "unlimited_whatsapp": user.get("unlimited_whatsapp", False),
        "unlimited_email": user.get("unlimited_email", False)
    }

@api_router.post("/credits/deduct")
async def deduct_credits(message_type: str, count: int = 1, current_user: User = Depends(get_current_user)):
    """Deduct credits when messages are sent"""
    if message_type not in ["whatsapp", "email"]:
        raise HTTPException(status_code=400, detail="Invalid message type")
    
    user = await db.users.find_one({"id": current_user.id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has unlimited credits
    unlimited_field = f"unlimited_{message_type}"
    if user.get(unlimited_field, False):
        return {"message": f"Unlimited {message_type} credits", "credits_remaining": "unlimited"}
    
    # Check and deduct credits
    credits_field = f"{message_type}_credits"
    current_credits = user.get(credits_field, 0)
    
    if current_credits < count:
        raise HTTPException(status_code=400, detail=f"Insufficient {message_type} credits")
    
    new_credits = current_credits - count
    
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {credits_field: new_credits}}
    )
    
    return {
        "message": f"Deducted {count} {message_type} credits",
        "credits_remaining": new_credits
    }

# Default celebration images
def get_default_celebration_image(occasion: str = "birthday") -> str:
    """Get default celebration image based on occasion"""
    default_images = {
        "birthday": "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHxiaXJ0aGRheSUyMGNlbGVicmF0aW9ufGVufDB8fHx8MTc1OTQ4ODk0Nnww&ixlib=rb-4.1.0&q=85&w=400&h=400&fit=crop",
        "anniversary": "https://images.unsplash.com/photo-1599073499036-dc27fc297dc9?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHwyfHxhbm5pdmVyc2FyeSUyMGNlbGVicmF0aW9ufGVufDB8fHx8MTc1OTQ4ODk1MXww&ixlib=rb-4.1.0&q=85&w=400&h=400&fit=crop",
    }
    return default_images.get(occasion.lower(), default_images["birthday"])

# WhatsApp Message Sending Functions
async def send_whatsapp_message(user_id: str, phone_number: str, message: str, image_url: Optional[str] = None, occasion: str = "birthday"):
    """Send WhatsApp message using DigitalSMS API according to official documentation"""
    settings = await db.user_settings.find_one({"user_id": user_id})
    
    if not settings:
        return {"status": "error", "message": "No WhatsApp configuration found"}
    
    try:
        import requests
        
        api_key = settings.get("digitalsms_api_key")
        
        if not api_key:
            return {"status": "error", "message": "DigitalSMS API key not configured"}
        
        # DigitalSMS API endpoint as per documentation
        url = "https://demo.digitalsms.biz/api"
        
        # Clean phone number - DigitalSMS expects 10-digit Indian mobile number
        clean_phone = phone_number.replace("+91", "").replace("+", "").replace(" ", "").replace("-", "")
        if len(clean_phone) > 10:
            clean_phone = clean_phone[-10:]  # Take last 10 digits
        
        # Prepare API parameters according to DigitalSMS documentation
        params = {
            "apikey": api_key,
            "mobile": clean_phone,
            "msg": message
        }
        
        # For now, skip images entirely to isolate the 407 error issue
        # We'll add image support back once basic messaging works
        # TODO: Add image support back after resolving 407 error
        
        # Temporarily commenting out image logic:
        # if image_url and image_url.strip():
        #     # Convert relative URL to absolute if needed
        #     if image_url.startswith('/'):
        #         absolute_image_url = f"https://remindhub-5.preview.emergentagent.com{image_url}"
        #     elif image_url.startswith('http'):
        #         absolute_image_url = image_url
        #     else:
        #         # Skip image if not a valid URL format
        #         absolute_image_url = None
        #     
        #     # Only add image if we have a valid URL and it's accessible
        #     if absolute_image_url:
        #         try:
        #             import requests
        #             # Quick HEAD request to check if image is accessible
        #             head_response = requests.head(absolute_image_url, timeout=5)
        #             if head_response.status_code == 200:
        #                 params["img1"] = absolute_image_url
        #             # If image is not accessible, don't include img1 parameter
        #         except:
        #             # If validation fails, don't include img1 parameter
        #             pass
        # If no valid image, don't include img1 parameter (send text-only message)
        
        # Log request details for debugging (remove img1 from logs for brevity)
        debug_params = {k: v for k, v in params.items() if k != "img1"}
        debug_params["has_image"] = "img1" in params
        print(f"DigitalSMS API Request - URL: {url}, Params: {debug_params}")
        
        # Make API request (GET method as per documentation)
        response = requests.get(url, params=params, timeout=30)
        
        # Log response for debugging
        print(f"DigitalSMS API Response - Status: {response.status_code}, Body: {response.text[:200]}...")
        
        if response.status_code == 200:
            try:
                # Try to parse JSON response
                response_data = response.json()
                status = response_data.get("status", 0)
                message_text = response_data.get("message", "")
                statuscode = response_data.get("statuscode", "")
                
                if status == 1:
                    return {"status": "success", "message": f"Message sent successfully. Response: {message_text}"}
                else:
                    # Provide specific error messages for common issues
                    if statuscode == 403:
                        error_msg = "Invalid or expired DigitalSMS API key. Please check your API key in Settings."
                    elif statuscode == 407:
                        error_msg = "Proxy authentication error. Please check your DigitalSMS API configuration."
                    elif statuscode == 400:
                        error_msg = "Invalid request format. Please check phone number and message content."
                    else:
                        error_msg = f"DigitalSMS API error (Code: {statuscode}): {message_text}"
                    
                    return {"status": "error", "message": error_msg}
                    
            except json.JSONDecodeError:
                # Fallback to text response parsing
                response_text = response.text.strip()
                
                # Check for success indicators
                if any(indicator in response_text.lower() for indicator in ["success", "sent", "ok", "delivered", "queued"]):
                    return {"status": "success", "message": f"Message sent via DigitalSMS API. Response: {response_text}"}
                elif any(error in response_text.lower() for error in ["invalid", "error", "fail", "unauthorized", "forbidden", "insufficient"]):
                    return {"status": "error", "message": f"DigitalSMS API error: {response_text} | Debug: {debug_params}"}
                else:
                    # If response is unclear, assume success if HTTP 200
                    return {"status": "success", "message": f"Message sent via DigitalSMS API. Server response: {response_text}"}
        else:
            return {"status": "error", "message": f"DigitalSMS API HTTP error {response.status_code}: {response.text} | Debug: {debug_params}"}
            
    except Exception as e:
        return {"status": "error", "message": f"WhatsApp sending error: {str(e)}"}

@api_router.post("/send-whatsapp-test")
async def send_test_whatsapp_message(phone_number: str, current_user: User = Depends(get_current_user)):
    """Send a test WhatsApp message to a real phone number"""
    # Validate phone number format (basic validation)
    clean_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
    if not clean_phone.isdigit() or len(clean_phone) < 8:
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    result = await send_whatsapp_message(
        user_id=current_user.id,
        phone_number=clean_phone,
        message=f"🎉 Test message from ReminderAI! Your WhatsApp API configuration is working perfectly. This message was sent to {phone_number}.",
        occasion="birthday"  # Default for test messages
    )
    return result

# Custom Messages Routes
@api_router.post("/custom-messages", response_model=CustomMessage)
async def create_custom_message(message_data: CustomMessageCreate, current_user: User = Depends(get_current_user)):
    """Create or update a custom message for a contact"""
    # Verify contact belongs to user
    contact = await db.contacts.find_one({"id": message_data.contact_id, "user_id": current_user.id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Check if custom message already exists
    existing_message = await db.custom_messages.find_one({
        "user_id": current_user.id,
        "contact_id": message_data.contact_id,
        "occasion": message_data.occasion,
        "message_type": message_data.message_type
    })
    
    message_dict = prepare_for_mongo({
        "user_id": current_user.id,
        "contact_id": message_data.contact_id,
        "occasion": message_data.occasion,
        "message_type": message_data.message_type,
        "custom_message": message_data.custom_message,
        "image_url": message_data.image_url,
        "updated_at": datetime.now(timezone.utc)
    })
    
    if existing_message:
        # Update existing message
        await db.custom_messages.update_one(
            {"id": existing_message["id"]},
            {"$set": message_dict}
        )
        custom_message = CustomMessage(id=existing_message["id"], **message_dict)
    else:
        # Create new message
        custom_message = CustomMessage(**message_dict)
        await db.custom_messages.insert_one(prepare_for_mongo(custom_message.dict()))
    
    return custom_message

@api_router.get("/custom-messages/{contact_id}")
async def get_custom_messages(contact_id: str, current_user: User = Depends(get_current_user)):
    """Get all custom messages for a specific contact"""
    # Verify contact belongs to user
    contact = await db.contacts.find_one({"id": contact_id, "user_id": current_user.id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    messages = await db.custom_messages.find({
        "user_id": current_user.id,
        "contact_id": contact_id
    }).to_list(100)
    
    return [CustomMessage(**parse_from_mongo(msg)) for msg in messages]

@api_router.get("/custom-messages/{contact_id}/{occasion}/{message_type}")
async def get_custom_message(
    contact_id: str, 
    occasion: str, 
    message_type: str, 
    current_user: User = Depends(get_current_user)
):
    """Get a specific custom message for a contact, occasion and message type"""
    # Verify contact belongs to user
    contact = await db.contacts.find_one({"id": contact_id, "user_id": current_user.id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    message = await db.custom_messages.find_one({
        "user_id": current_user.id,
        "contact_id": contact_id,
        "occasion": occasion,
        "message_type": message_type
    })
    
    if not message:
        # Generate default message using AI
        message_request = GenerateMessageRequest(
            contact_name=contact["name"],
            occasion=occasion,
            relationship="friend",
            tone=contact.get("message_tone", "normal")
        )
        
        ai_message = await generate_message(message_request, current_user)
        
        return {
            "contact_id": contact_id,
            "occasion": occasion,
            "message_type": message_type,
            "custom_message": ai_message.message,
            "image_url": None,
            "is_default": True
        }
    
    return CustomMessage(**parse_from_mongo(message))

@api_router.delete("/custom-messages/{contact_id}/{occasion}/{message_type}")
async def delete_custom_message(
    contact_id: str, 
    occasion: str, 
    message_type: str, 
    current_user: User = Depends(get_current_user)
):
    """Delete a specific custom message"""
    result = await db.custom_messages.delete_one({
        "user_id": current_user.id,
        "contact_id": contact_id,
        "occasion": occasion,
        "message_type": message_type
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Custom message not found")
    
    return {"message": "Custom message deleted successfully"}

@api_router.post("/send-test-message")
async def send_test_message(request: TestMessageRequest, current_user: User = Depends(get_current_user)):
    """Send test messages to user's own contact information"""
    # Get contact
    contact = await db.contacts.find_one({"id": request.contact_id, "user_id": current_user.id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact = parse_from_mongo(contact)
    results = {"whatsapp": None, "email": None}
    
    # Get user settings for test contact information
    settings = await db.user_settings.find_one({"user_id": current_user.id})
    
    # Get template defaults for fallback images
    whatsapp_template = await db.templates.find_one({
        "user_id": current_user.id,
        "type": "whatsapp",
        "is_default": True
    })
    
    email_template = await db.templates.find_one({
        "user_id": current_user.id,
        "type": "email", 
        "is_default": True
    })

    # Get custom messages or generate defaults
    whatsapp_message_data = await db.custom_messages.find_one({
        "user_id": current_user.id,
        "contact_id": request.contact_id,
        "occasion": request.occasion,
        "message_type": "whatsapp"
    })
    
    email_message_data = await db.custom_messages.find_one({
        "user_id": current_user.id,
        "contact_id": request.contact_id,
        "occasion": request.occasion,
        "message_type": "email"
    })
    
    # Generate default messages if no custom ones exist
    if not whatsapp_message_data:
        message_request = GenerateMessageRequest(
            contact_name=contact["name"],
            occasion=request.occasion,
            relationship="friend",
            tone=contact.get("message_tone", "normal")
        )
        ai_message = await generate_message(message_request, current_user)
        whatsapp_message = ai_message.message
        
        # Image hierarchy: contact image -> template default image
        whatsapp_image = (
            contact.get("whatsapp_image") or 
            (whatsapp_template.get("whatsapp_image_url") if whatsapp_template else None)
        )
    else:
        whatsapp_message = whatsapp_message_data["custom_message"]
        
        # Image hierarchy: custom message image -> contact image -> template default image
        whatsapp_image = (
            whatsapp_message_data.get("image_url") or 
            contact.get("whatsapp_image") or
            (whatsapp_template.get("whatsapp_image_url") if whatsapp_template else None)
        )
    
    if not email_message_data:
        message_request = GenerateMessageRequest(
            contact_name=contact["name"],
            occasion=request.occasion,
            relationship="friend",
            tone=contact.get("message_tone", "normal")
        )
        ai_message = await generate_message(message_request, current_user)
        email_message = ai_message.message
        
        # Image hierarchy: contact image -> template default image
        email_image = (
            contact.get("email_image") or
            (email_template.get("email_image_url") if email_template else None)
        )
    else:
        email_message = email_message_data["custom_message"]
        
        # Image hierarchy: custom message image -> contact image -> template default image
        email_image = (
            email_message_data.get("image_url") or
            contact.get("email_image") or
            (email_template.get("email_image_url") if email_template else None)
        )
    
    # Send test WhatsApp message to user's phone (if they have WhatsApp configured and phone number in their profile)
    if contact.get("whatsapp"):
        test_whatsapp_message = f"🧪 TEST MESSAGE for {contact['name']}'s {request.occasion}:\n\n{whatsapp_message}\n\n📝 This is how your message will appear."
        
        whatsapp_result = await send_whatsapp_message(
            user_id=current_user.id,
            phone_number=contact["whatsapp"],
            message=test_whatsapp_message,
            image_url=whatsapp_image,
            occasion=request.occasion
        )
        results["whatsapp"] = whatsapp_result
    
    # Send test email to user's email
    if settings and settings.get("email_api_key"):
        import requests
        
        try:
            api_key = settings.get("email_api_key")
            sender_email = settings.get("sender_email")
            sender_name = settings.get("sender_name", "ReminderAI")
            
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "api-key": api_key,
                "Content-Type": "application/json"
            }
            
            # Create HTML email content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #e11d48; border-bottom: 2px solid #e11d48; padding-bottom: 10px;">
                        🧪 Test Message Preview
                    </h2>
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #374151;">
                            {contact['name']}'s {request.occasion.title()} Message:
                        </h3>
                        <div style="background-color: white; padding: 15px; border-radius: 6px; border-left: 4px solid #e11d48;">
                            {email_message}
                        </div>
                        {f'<img src="{email_image}" style="max-width: 100%; height: auto; margin-top: 15px; border-radius: 6px;" alt="Celebration Image">' if email_image else ''}
                    </div>
                    <p style="font-size: 14px; color: #6b7280; margin-top: 30px;">
                        📝 This is a preview of how your {request.occasion} message will appear when sent to {contact['name']}.
                    </p>
                </div>
            </body>
            </html>
            """
            
            payload = {
                "sender": {
                    "name": sender_name,
                    "email": sender_email
                },
                "to": [
                    {
                        "email": current_user.email,
                        "name": current_user.full_name
                    }
                ],
                "subject": f"Test: {contact['name']}'s {request.occasion.title()} Message Preview",
                "htmlContent": html_content
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 201:
                results["email"] = {"status": "success", "message": "Test email sent successfully"}
            else:
                results["email"] = {"status": "error", "message": f"Email API error: {response.text}"}
                
        except Exception as e:
            results["email"] = {"status": "error", "message": f"Email test error: {str(e)}"}
    else:
        results["email"] = {"status": "error", "message": "Email API not configured"}
    
    return {
        "contact_name": contact["name"],
        "occasion": request.occasion,
        "results": results
    }

# Image Upload Routes
@api_router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Upload image for contacts"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only image files (JPEG, PNG, GIF, WebP) are allowed")
    
    # Validate file size (5MB limit)
    max_size = 5 * 1024 * 1024  # 5MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/images")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{current_user.id}_{uuid.uuid4().hex}.{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)
    
    # Return full file URL with domain
    file_url = f"https://remindhub-5.preview.emergentagent.com/uploads/images/{unique_filename}"
    return {"image_url": file_url, "filename": unique_filename}

@api_router.put("/contacts/{contact_id}/images")
async def update_contact_images(
    contact_id: str, 
    whatsapp_image: Optional[str] = None,
    email_image: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Update contact images for WhatsApp and Email"""
    contact = await db.contacts.find_one({"id": contact_id, "user_id": current_user.id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    update_data = {}
    if whatsapp_image is not None:
        update_data["whatsapp_image"] = whatsapp_image
    if email_image is not None:
        update_data["email_image"] = email_image
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No image data provided")
    
    await db.contacts.update_one(
        {"id": contact_id, "user_id": current_user.id},
        {"$set": update_data}
    )
    
    return {"message": "Contact images updated successfully"}

# Router will be included after all endpoints are defined

# Create uploads directory
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# Mount static files for image serving
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Daily Reminder System
async def get_contact_message_for_reminder(user_id: str, contact_id: str, occasion: str):
    """Get appropriate message and image for reminder with hierarchy logic"""
    
    # Get template defaults for fallback images
    whatsapp_template = await db.templates.find_one({
        "user_id": user_id,
        "type": "whatsapp",
        "is_default": True
    })
    
    email_template = await db.templates.find_one({
        "user_id": user_id,
        "type": "email", 
        "is_default": True
    })
    
    # Get contact info
    contact = await db.contacts.find_one({"id": contact_id, "user_id": user_id})
    if not contact:
        return None
    
    contact = parse_from_mongo(contact)
    
    # Get custom messages
    whatsapp_message_data = await db.custom_messages.find_one({
        "user_id": user_id,
        "contact_id": contact_id,
        "occasion": occasion,
        "message_type": "whatsapp"
    })
    
    email_message_data = await db.custom_messages.find_one({
        "user_id": user_id,
        "contact_id": contact_id,
        "occasion": occasion,
        "message_type": "email"
    })
    
    # Generate WhatsApp message and image
    if whatsapp_message_data:
        whatsapp_message = whatsapp_message_data["custom_message"]
        whatsapp_image = (
            whatsapp_message_data.get("image_url") or 
            contact.get("whatsapp_image") or
            (whatsapp_template.get("whatsapp_image_url") if whatsapp_template else None)
        )
    else:
        # Generate AI message
        try:
            # Get user for AI generation
            user = await db.users.find_one({"id": user_id})
            if user:
                user = User(**parse_from_mongo(user))
                message_request = GenerateMessageRequest(
                    contact_name=contact["name"],
                    occasion=occasion,
                    relationship="friend",
                    tone=contact.get("message_tone", "normal")
                )
                ai_message = await generate_message(message_request, user)
                whatsapp_message = ai_message.message
            else:
                whatsapp_message = f"Happy {occasion}, {contact['name']}! 🎉"
        except:
            whatsapp_message = f"Happy {occasion}, {contact['name']}! 🎉"
        
        whatsapp_image = (
            contact.get("whatsapp_image") or
            (whatsapp_template.get("whatsapp_image_url") if whatsapp_template else None)
        )
    
    # Generate Email message and image
    if email_message_data:
        email_message = email_message_data["custom_message"]
        email_image = (
            email_message_data.get("image_url") or
            contact.get("email_image") or
            (email_template.get("email_image_url") if email_template else None)
        )
    else:
        # Generate AI message
        try:
            # Get user for AI generation
            user = await db.users.find_one({"id": user_id})
            if user:
                user = User(**parse_from_mongo(user))
                message_request = GenerateMessageRequest(
                    contact_name=contact["name"],
                    occasion=occasion,
                    relationship="friend",
                    tone=contact.get("message_tone", "normal")
                )
                ai_message = await generate_message(message_request, user)
                email_message = ai_message.message
            else:
                email_message = f"Happy {occasion}, {contact['name']}! 🎉"
        except:
            email_message = f"Happy {occasion}, {contact['name']}! 🎉"
        
        email_image = (
            contact.get("email_image") or
            (email_template.get("email_image_url") if email_template else None)
        )
    
    return {
        "whatsapp_message": whatsapp_message,
        "whatsapp_image": whatsapp_image,
        "email_message": email_message,
        "email_image": email_image,
        "contact": contact
    }

async def send_email_reminder(user_id: str, contact: dict, occasion: str, message: str, image_url: Optional[str] = None):
    """Send email reminder using Brevo API"""
    
    settings = await db.user_settings.find_one({"user_id": user_id})
    if not settings:
        return {"status": "error", "message": "Email settings not found"}
    
    api_key = settings.get("email_api_key")
    sender_email = settings.get("sender_email")
    sender_name = settings.get("sender_name", "ReminderAI")
    
    if not api_key or not sender_email:
        return {"status": "error", "message": "Email configuration incomplete"}
    
    try:
        import requests
        
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        
        # Create HTML email content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #e11d48; border-bottom: 2px solid #e11d48; padding-bottom: 10px;">
                    🎉 {occasion.title()} Reminder
                </h2>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <div style="background-color: white; padding: 15px; border-radius: 6px; border-left: 4px solid #e11d48;">
                        {message}
                    </div>
                    {f'<img src="{image_url}" style="max-width: 100%; height: auto; margin-top: 15px; border-radius: 6px;" alt="Celebration Image">' if image_url else ''}
                </div>
                <p style="font-size: 14px; color: #6b7280; margin-top: 30px;">
                    Sent with ❤️ by ReminderAI
                </p>
            </div>
        </body>
        </html>
        """
        
        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email
            },
            "to": [
                {
                    "email": contact["email"],
                    "name": contact["name"]
                }
            ],
            "subject": f"🎉 {contact['name']}'s {occasion.title()} Reminder",
            "htmlContent": html_content
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            return {"status": "success", "message": "Email sent successfully"}
        else:
            return {"status": "error", "message": f"Email API error: {response.text}"}
            
    except Exception as e:
        return {"status": "error", "message": f"Email sending error: {str(e)}"}

async def send_reminder_messages(user: dict, contact: dict, occasion: str, results: dict):
    """Send WhatsApp and Email reminders for a contact"""
    try:
        # Get messages with image hierarchy
        message_data = await get_contact_message_for_reminder(user["id"], contact["id"], occasion)
        if not message_data:
            results["errors"].append(f"Could not generate message for {contact['name']}")
            return
        
        # Send WhatsApp if configured and credits available
        if (contact.get("whatsapp") and 
            user.get("whatsapp_credits", 0) > 0 and
            not user.get("unlimited_whatsapp", False)):
            
            whatsapp_result = await send_whatsapp_message(
                user_id=user["id"],
                phone_number=contact["whatsapp"],
                message=message_data["whatsapp_message"],
                image_url=message_data["whatsapp_image"],
                occasion=occasion
            )
            
            if whatsapp_result["status"] == "success":
                results["whatsapp_sent"] += 1
                results["messages_sent"] += 1
                # Deduct credit if not unlimited
                if not user.get("unlimited_whatsapp", False):
                    await db.users.update_one(
                        {"id": user["id"]},
                        {"$inc": {"whatsapp_credits": -1}}
                    )
            else:
                results["errors"].append(f"WhatsApp failed for {contact['name']}: {whatsapp_result['message']}")
        
        # Send WhatsApp if unlimited credits
        elif (contact.get("whatsapp") and user.get("unlimited_whatsapp", False)):
            whatsapp_result = await send_whatsapp_message(
                user_id=user["id"],
                phone_number=contact["whatsapp"],
                message=message_data["whatsapp_message"],
                image_url=message_data["whatsapp_image"],
                occasion=occasion
            )
            
            if whatsapp_result["status"] == "success":
                results["whatsapp_sent"] += 1
                results["messages_sent"] += 1
            else:
                results["errors"].append(f"WhatsApp failed for {contact['name']}: {whatsapp_result['message']}")
        
        # Send Email if configured and credits available
        if (contact.get("email") and 
            user.get("email_credits", 0) > 0 and
            not user.get("unlimited_email", False)):
            
            email_result = await send_email_reminder(
                user_id=user["id"],
                contact=contact,
                occasion=occasion,
                message=message_data["email_message"],
                image_url=message_data["email_image"]
            )
            
            if email_result["status"] == "success":
                results["email_sent"] += 1  
                results["messages_sent"] += 1
                # Deduct credit if not unlimited
                if not user.get("unlimited_email", False):
                    await db.users.update_one(
                        {"id": user["id"]},
                        {"$inc": {"email_credits": -1}}
                    )
            else:
                results["errors"].append(f"Email failed for {contact['name']}: {email_result['message']}")
        
        # Send Email if unlimited credits
        elif (contact.get("email") and user.get("unlimited_email", False)):
            email_result = await send_email_reminder(
                user_id=user["id"],
                contact=contact,
                occasion=occasion,
                message=message_data["email_message"],
                image_url=message_data["email_image"]
            )
            
            if email_result["status"] == "success":
                results["email_sent"] += 1
                results["messages_sent"] += 1
            else:
                results["errors"].append(f"Email failed for {contact['name']}: {email_result['message']}")
                
    except Exception as e:
        results["errors"].append(f"Error processing {contact['name']}: {str(e)}")

@api_router.post("/system/daily-reminders")
async def process_daily_reminders():
    """Process all daily birthday/anniversary reminders - Internal system endpoint"""
    
    execution_time = datetime.now(timezone.utc)
    today = execution_time.date()
    
    results = {
        "execution_time": execution_time.isoformat(),
        "date": today.isoformat(),
        "total_users": 0,
        "messages_sent": 0,
        "whatsapp_sent": 0,
        "email_sent": 0,
        "errors": []
    }
    
    try:
        # Get all users with active subscriptions
        users = await db.users.find({
            "subscription_status": {"$in": ["active", "trial"]}
        }).to_list(1000)
        
        for user in users:
            user = parse_from_mongo(user)
            user_id = user["id"]
            results["total_users"] += 1
            
            try:
                # Get user settings for send time and timezone
                settings = await db.user_settings.find_one({"user_id": user_id})
                if not settings:
                    continue
                    
                user_timezone = settings.get("timezone", "UTC")
                daily_send_time = settings.get("daily_send_time", "09:00")
                
                # Convert to user's timezone and check if it's time to send
                try:
                    user_tz = pytz.timezone(user_timezone)
                    user_now = execution_time.astimezone(user_tz)
                    
                    send_hour, send_minute = map(int, daily_send_time.split(":"))
                    
                    # Check if current time is within 15-minute window of user's preferred send time
                    current_minutes = user_now.hour * 60 + user_now.minute
                    target_minutes = send_hour * 60 + send_minute
                    
                    # Allow 15-minute window (since cron runs every 15 minutes)
                    if abs(current_minutes - target_minutes) > 15:
                        continue
                        
                except Exception as tz_error:
                    results["errors"].append(f"Timezone error for user {user['email']}: {str(tz_error)}")
                    continue
                
                # Get contacts for this user
                contacts = await db.contacts.find({"user_id": user_id}).to_list(1000)
                
                for contact in contacts:
                    contact = parse_from_mongo(contact)
                    
                    # Check birthday
                    if contact.get("birthday"):
                        try:
                            birthday = datetime.fromisoformat(contact["birthday"]).date()
                            if birthday.month == today.month and birthday.day == today.day:
                                await send_reminder_messages(user, contact, "birthday", results)
                        except Exception as bd_error:
                            results["errors"].append(f"Birthday parsing error for {contact['name']}: {str(bd_error)}")
                    
                    # Check anniversary
                    if contact.get("anniversary_date"):
                        try:
                            anniversary = datetime.fromisoformat(contact["anniversary_date"]).date()
                            if anniversary.month == today.month and anniversary.day == today.day:
                                await send_reminder_messages(user, contact, "anniversary", results)
                        except Exception as ann_error:
                            results["errors"].append(f"Anniversary parsing error for {contact['name']}: {str(ann_error)}")
                            
            except Exception as user_error:
                results["errors"].append(f"Error processing user {user.get('email', user_id)}: {str(user_error)}")
        
        # Log execution results
        log_entry = ReminderLog(
            date=today.isoformat(),
            execution_time=execution_time,
            total_users=results["total_users"],
            messages_sent=results["messages_sent"],
            whatsapp_sent=results["whatsapp_sent"],
            email_sent=results["email_sent"],
            errors=results["errors"]
        )
        
        await db.reminder_logs.insert_one(prepare_for_mongo(log_entry.dict()))
        
        return results
        
    except Exception as e:
        results["errors"].append(f"System error: {str(e)}")
        
        # Still try to log the execution
        try:
            log_entry = ReminderLog(
                date=today.isoformat(),
                execution_time=execution_time,
                total_users=results["total_users"],
                messages_sent=results["messages_sent"],
                whatsapp_sent=results["whatsapp_sent"],
                email_sent=results["email_sent"],
                errors=results["errors"]
            )
            await db.reminder_logs.insert_one(prepare_for_mongo(log_entry.dict()))
        except:
            pass
            
        return results

@api_router.get("/admin/reminder-stats", response_model=DailyReminderStats)
async def get_reminder_stats(
    date: Optional[str] = None, 
    admin_user: User = Depends(get_admin_user)
):
    """Get daily reminder execution statistics for admin dashboard"""
    
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()
    
    # Get execution logs for the specified date
    logs = await db.reminder_logs.find({
        "date": date
    }).to_list(100)
    
    if not logs:
        return DailyReminderStats(
            date=date,
            total_executions=0,
            total_users_processed=0,
            total_messages_sent=0,
            whatsapp_messages=0,
            email_messages=0,
            errors=[]
        )
    
    # Aggregate statistics
    total_users = sum(log.get("total_users", 0) for log in logs)
    total_messages = sum(log.get("messages_sent", 0) for log in logs)
    whatsapp_messages = sum(log.get("whatsapp_sent", 0) for log in logs)
    email_messages = sum(log.get("email_sent", 0) for log in logs)
    all_errors = []
    
    for log in logs:
        if log.get("errors"):
            all_errors.extend(log["errors"])
    
    return DailyReminderStats(
        date=date,
        total_executions=len(logs),
        total_users_processed=total_users,
        total_messages_sent=total_messages,
        whatsapp_messages=whatsapp_messages,
        email_messages=email_messages,
        errors=all_errors
    )

@api_router.get("/admin/reminder-logs")
async def get_reminder_logs(
    days: int = 7,
    admin_user: User = Depends(get_admin_user)
):
    """Get reminder execution logs for the past N days"""
    
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days)
    
    logs = await db.reminder_logs.find({
        "date": {
            "$gte": start_date.isoformat(),
            "$lte": end_date.isoformat()
        }
    }).sort("date", -1).to_list(days * 24)  # Max entries per day
    
    return [ReminderLog(**parse_from_mongo(log)) for log in logs]

# Enhanced Admin User Management
@api_router.get("/admin/users")
async def get_all_users(admin_user: User = Depends(get_admin_user)):
    """Get all users for admin management"""
    
    users = await db.users.find({}).to_list(1000)
    
    user_list = []
    for user in users:
        user = parse_from_mongo(user)
        # Don't include password hash in response
        user.pop("password_hash", None)
        
        # Get user's contact count
        contact_count = await db.contacts.count_documents({"user_id": user["id"]})
        user["contact_count"] = contact_count
        
        # Get user's template count
        template_count = await db.templates.count_documents({"user_id": user["id"]})
        user["template_count"] = template_count
        
        # Get message usage statistics
        user_messages = await db.reminder_logs.aggregate([
            {"$match": {"errors": {"$not": {"$regex": f"user {user['email']}", "$options": "i"}}}},
            {"$group": {
                "_id": None,
                "total_whatsapp": {"$sum": "$whatsapp_sent"},
                "total_email": {"$sum": "$email_sent"}
            }}
        ]).to_list(1)
        
        if user_messages:
            user["total_whatsapp_sent"] = user_messages[0].get("total_whatsapp", 0)
            user["total_email_sent"] = user_messages[0].get("total_email", 0)
        else:
            user["total_whatsapp_sent"] = 0
            user["total_email_sent"] = 0
        
        user_list.append(user)
    
    return user_list

@api_router.put("/admin/users/{user_id}")
async def update_user_by_admin(
    user_id: str, 
    update_data: dict,
    admin_user: User = Depends(get_admin_user)
):
    """Update any user's information as admin"""
    
    # Validate user exists
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update fields
    update_fields = {}
    
    # Allow admin to update basic info
    if "full_name" in update_data:
        update_fields["full_name"] = update_data["full_name"]
    
    if "email" in update_data:
        # Check if email is already taken by another user
        existing_user = await db.users.find_one({
            "email": update_data["email"].lower(),
            "id": {"$ne": user_id}
        })
        if existing_user:
            raise HTTPException(status_code=400, detail="Email address is already in use")
        update_fields["email"] = update_data["email"].lower()
    
    if "phone_number" in update_data:
        update_fields["phone_number"] = update_data["phone_number"]
    
    # Allow admin to update password
    if "password" in update_data:
        hashed_password = hash_password(update_data["password"])
        update_fields["password_hash"] = hashed_password
    
    # Allow admin to update admin status
    if "is_admin" in update_data:
        update_fields["is_admin"] = update_data["is_admin"]
    
    # Allow admin to update subscription
    if "subscription_status" in update_data:
        update_fields["subscription_status"] = update_data["subscription_status"]
    
    # Allow admin to update credits
    if "whatsapp_credits" in update_data:
        update_fields["whatsapp_credits"] = update_data["whatsapp_credits"]
    
    if "email_credits" in update_data:
        update_fields["email_credits"] = update_data["email_credits"]
    
    if "unlimited_whatsapp" in update_data:
        update_fields["unlimited_whatsapp"] = update_data["unlimited_whatsapp"]
    
    if "unlimited_email" in update_data:
        update_fields["unlimited_email"] = update_data["unlimited_email"]
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    # Update user
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get updated user
    updated_user = await db.users.find_one({"id": user_id})
    updated_user = parse_from_mongo(updated_user)
    updated_user.pop("password_hash", None)  # Don't return password hash
    
    return {"message": "User updated successfully", "user": updated_user}

@api_router.delete("/admin/users/{user_id}")
async def delete_user_by_admin(
    user_id: str,
    admin_user: User = Depends(get_admin_user)
):
    """Delete a user and all their data"""
    
    # Prevent admin from deleting themselves
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    
    # Check if user exists
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow deleting admin users (except self-deletion is already prevented above)
    if target_user.get('is_admin', False):
        raise HTTPException(status_code=400, detail="Cannot delete admin users")
    
    # Delete user's data
    await db.contacts.delete_many({"user_id": user_id})
    await db.templates.delete_many({"user_id": user_id})
    await db.custom_messages.delete_many({"user_id": user_id})
    await db.user_settings.delete_many({"user_id": user_id})
    
    # Delete user
    await db.users.delete_one({"id": user_id})
    
    return {"message": f"User {target_user['email']} and all associated data deleted successfully"}

@api_router.get("/admin/platform-stats")
async def get_platform_stats(admin_user: User = Depends(get_admin_user)):
    """Get comprehensive platform statistics for admin dashboard"""
    
    # User statistics
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"subscription_status": "active"})
    trial_users = await db.users.count_documents({"subscription_status": "trial"})
    admin_users = await db.users.count_documents({"is_admin": True})
    
    # Content statistics
    total_contacts = await db.contacts.count_documents({})
    total_templates = await db.templates.count_documents({})
    total_custom_messages = await db.custom_messages.count_documents({})
    
    # Message statistics from logs
    total_logs = await db.reminder_logs.count_documents({})
    
    # Aggregate message statistics
    message_stats = await db.reminder_logs.aggregate([
        {
            "$group": {
                "_id": None,
                "total_whatsapp_sent": {"$sum": "$whatsapp_sent"},
                "total_email_sent": {"$sum": "$email_sent"},
                "total_messages": {"$sum": "$messages_sent"}
            }
        }
    ]).to_list(1)
    
    if message_stats:
        whatsapp_sent = message_stats[0]["total_whatsapp_sent"]
        email_sent = message_stats[0]["total_email_sent"]
        total_messages_sent = message_stats[0]["total_messages"]
    else:
        whatsapp_sent = 0
        email_sent = 0
        total_messages_sent = 0
    
    # Recent activity (last 7 days)
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=7)
    
    recent_messages = await db.reminder_logs.aggregate([
        {
            "$match": {
                "date": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "recent_whatsapp": {"$sum": "$whatsapp_sent"},
                "recent_email": {"$sum": "$email_sent"},
                "recent_executions": {"$sum": 1}
            }
        }
    ]).to_list(1)
    
    if recent_messages:
        recent_whatsapp = recent_messages[0]["recent_whatsapp"]
        recent_email = recent_messages[0]["recent_email"]
        recent_executions = recent_messages[0]["recent_executions"]
    else:
        recent_whatsapp = 0
        recent_email = 0
        recent_executions = 0
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "trial": trial_users,
            "admin": admin_users
        },
        "content": {
            "contacts": total_contacts,
            "templates": total_templates,
            "custom_messages": total_custom_messages
        },
        "messages": {
            "total_sent": total_messages_sent,
            "whatsapp_sent": whatsapp_sent,
            "email_sent": email_sent,
            "recent_whatsapp": recent_whatsapp,
            "recent_email": recent_email,
            "recent_executions": recent_executions
        },
        "system": {
            "total_reminder_logs": total_logs
        }
    }

# Admin Setup Route (for initial setup only)
@api_router.post("/setup-admin")
async def setup_admin_user():
    """Setup john@example.com as super admin - for initial setup only"""
    
    admin_email = "john@example.com"
    admin_password = "admin123"
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"email": admin_email})
    
    if existing_admin:
        # Update existing user to be admin and reset password
        hashed_password = hash_password(admin_password)
        await db.users.update_one(
            {"email": admin_email},
            {
                "$set": {
                    "is_admin": True,
                    "unlimited_whatsapp": True,
                    "unlimited_email": True,
                    "whatsapp_credits": 99999,
                    "email_credits": 99999,
                    "subscription_status": "active",
                    "password_hash": hashed_password
                }
            }
        )
        return {"message": "Existing user updated with super admin privileges", "email": admin_email, "password": admin_password}
    else:
        # Create new admin user
        hashed_password = hash_password(admin_password)
        admin_user = User(
            email=admin_email,
            full_name="Super Admin",
            phone_number=None,
            is_admin=True,
            subscription_status="active",
            whatsapp_credits=99999,
            email_credits=99999,
            unlimited_whatsapp=True,
            unlimited_email=True
        )
        
        admin_dict = admin_user.dict()
        admin_dict["password_hash"] = hashed_password
        admin_dict = prepare_for_mongo(admin_dict)
        
        await db.users.insert_one(admin_dict)
        return {"message": "Super admin user created successfully", "email": admin_email, "password": admin_password}

# ==================== NEW ADMIN SYSTEM ENDPOINTS ====================

@api_router.get("/admin-auth/captcha", response_model=CaptchaResponse)
async def get_captcha():
    """Generate a math captcha for admin login"""
    captcha_data = generate_math_captcha()
    return captcha_data

@api_router.post("/admin-auth/setup-first-admin")
async def setup_first_admin():
    """Create the first admin account - only works if no admins exist"""
    # Check if any admin exists
    existing_admin = await db.admins.find_one({})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists. Cannot create another admin.")
    
    # Generate random credentials
    import secrets
    import string
    username = "admin"
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    
    # Hash password
    hashed_password = hash_password(password)
    
    # Create admin
    admin = AdminUser(username=username)
    admin_dict = admin.dict()
    admin_dict["password_hash"] = hashed_password
    admin_dict = prepare_for_mongo(admin_dict)
    
    await db.admins.insert_one(admin_dict)
    
    return {
        "message": "First admin account created successfully",
        "username": username,
        "password": password,
        "warning": "Please save these credentials securely. This is the only time the password will be displayed."
    }

@api_router.post("/admin-auth/login")
async def admin_login(
    username: str,
    password: str,
    captcha_id: str,
    captcha_answer: str
):
    """Admin login with captcha verification"""
    # Verify captcha first
    if not verify_captcha(captcha_id, captcha_answer):
        raise HTTPException(status_code=400, detail="Invalid or expired captcha")
    
    # Find admin by username
    admin = await db.admins.find_one({"username": username})
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Verify password
    if not verify_password(password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create access token
    access_token = create_access_token({"admin_id": admin["id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": {
            "id": admin["id"],
            "username": admin["username"]
        }
    }

@api_router.get("/admin-auth/me")
async def get_current_admin_info(current_admin: AdminUser = Depends(get_current_admin)):
    """Get current admin info"""
    return current_admin

@api_router.get("/admin/users", response_model=List[UserWithContactCount])
async def get_all_users_with_contacts(current_admin: AdminUser = Depends(get_current_admin)):
    """Get all users with their contact counts"""
    # Get all users
    users = await db.users.find().to_list(length=None)
    
    result = []
    for user in users:
        # Count contacts for each user
        contact_count = await db.contacts.count_documents({"user_id": user["id"]})
        
        user_data = {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "phone_number": user.get("phone_number"),
            "subscription_status": user.get("subscription_status", "trial"),
            "whatsapp_credits": user.get("whatsapp_credits", 0),
            "email_credits": user.get("email_credits", 0),
            "unlimited_whatsapp": user.get("unlimited_whatsapp", False),
            "unlimited_email": user.get("unlimited_email", False),
            "created_at": user.get("created_at", datetime.now(timezone.utc)),
            "contact_count": contact_count
        }
        result.append(user_data)
    
    return result

@api_router.put("/admin/users/{user_id}")
async def update_user_details(
    user_id: str,
    update_data: UserUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Update user details (name, email, company, phone)"""
    # Find user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update data
    update_fields = {}
    if update_data.full_name is not None:
        update_fields["full_name"] = update_data.full_name.strip()
    
    if update_data.email is not None:
        # Check if email already exists for another user
        existing_user = await db.users.find_one({"email": update_data.email, "id": {"$ne": user_id}})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use by another user")
        update_fields["email"] = update_data.email
    
    if update_data.phone_number is not None:
        # Clean and validate phone number (Indian format)
        phone = update_data.phone_number.strip()
        if phone:
            # Remove common formatting
            phone = re.sub(r'[\s\-\(\)\+]', '', phone)
            # Remove +91 or 91 prefix
            if phone.startswith('91') and len(phone) > 10:
                phone = phone[2:]
            # Validate 10 digit Indian mobile number (starts with 6-9)
            if not (len(phone) == 10 and phone.isdigit() and phone[0] in '6789'):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid phone number. Must be 10 digits starting with 6-9"
                )
            update_fields["phone_number"] = phone
        else:
            update_fields["phone_number"] = None
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update user
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0 and result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User updated successfully", "updated_fields": list(update_fields.keys())}

@api_router.put("/admin/users/{user_id}/subscription")
async def update_user_subscription(
    user_id: str,
    subscription_data: SubscriptionUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Update user subscription and credits"""
    # Find user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update data
    update_fields = {}
    if subscription_data.subscription_status is not None:
        update_fields["subscription_status"] = subscription_data.subscription_status
    
    if subscription_data.whatsapp_credits is not None:
        update_fields["whatsapp_credits"] = subscription_data.whatsapp_credits
    
    if subscription_data.email_credits is not None:
        update_fields["email_credits"] = subscription_data.email_credits
    
    if subscription_data.unlimited_whatsapp is not None:
        update_fields["unlimited_whatsapp"] = subscription_data.unlimited_whatsapp
    
    if subscription_data.unlimited_email is not None:
        update_fields["unlimited_email"] = subscription_data.unlimited_email
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update user
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0 and result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Subscription updated successfully", "updated_fields": list(update_fields.keys())}

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include the router in the main app (after all endpoints are defined)
app.include_router(api_router)