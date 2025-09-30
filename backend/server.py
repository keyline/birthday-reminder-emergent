from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
    subscription_status: str = "trial"
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactCreate(BaseModel):
    name: str
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    birthday: Optional[date] = None
    anniversary_date: Optional[date] = None

class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    birthday: Optional[date] = None
    anniversary_date: Optional[date] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TemplateCreate(BaseModel):
    name: str
    type: str  # "email" or "whatsapp"
    subject: Optional[str] = None
    content: str
    is_default: bool = False

class Template(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    type: str
    subject: Optional[str] = None
    content: str
    is_default: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GenerateMessageRequest(BaseModel):
    contact_name: str
    occasion: str  # "birthday" or "anniversary"
    relationship: Optional[str] = "friend"
    tone: Optional[str] = "warm"  # "warm", "professional", "casual", "funny"

class MessageResponse(BaseModel):
    message: str

class BulkUploadResponse(BaseModel):
    total_rows: int
    successful_imports: int
    failed_imports: int
    errors: List[str]
    imported_contacts: List[Contact]

class UserSettingsCreate(BaseModel):
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    email_api_key: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    daily_send_time: Optional[str] = "09:00"  # HH:MM format
    timezone: Optional[str] = "UTC"
    execution_report_enabled: bool = True
    execution_report_email: Optional[str] = None

class UserSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    email_api_key: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
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
        for key, value in item.items():
            if key in ['birthday', 'anniversary_date'] and isinstance(value, str):
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

# AI Message Generation
@api_router.post("/generate-message", response_model=MessageResponse)
async def generate_message(request: GenerateMessageRequest, current_user: User = Depends(get_current_user)):
    try:
        # Initialize LLM chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"user_{current_user.id}_message_gen",
            system_message="You are a helpful assistant that generates personalized birthday and anniversary messages. Create warm, heartfelt messages that are appropriate for the occasion and relationship."
        ).with_model("openai", "gpt-4o")
        
        # Create prompt based on request
        prompt = f"Generate a {request.tone} {request.occasion} message for {request.contact_name}. "
        prompt += f"The relationship is: {request.relationship}. "
        prompt += "Make it personal, heartfelt, and appropriate for the occasion. "
        prompt += "Keep it between 50-150 words. Do not include any greeting like 'Dear' or signature."
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        return MessageResponse(message=response)
        
    except Exception as e:
        logging.error(f"Error generating message: {str(e)}")
        # Fallback message
        fallback_messages = {
            "birthday": f"Happy Birthday, {request.contact_name}! Wishing you a wonderful day filled with joy, laughter, and all your favorite things. May this new year of your life bring you happiness, success, and beautiful memories!",
            "anniversary": f"Happy Anniversary, {request.contact_name}! Celebrating another year of love, laughter, and beautiful memories together. Wishing you both continued happiness and many more wonderful years ahead!"
        }
        
        return MessageResponse(
            message=fallback_messages.get(request.occasion, f"Happy {request.occasion}, {request.contact_name}! Wishing you all the best on this special day!")
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

@api_router.get("/admin/users", response_model=List[UserStats])
async def get_all_users_with_stats(admin_user: User = Depends(get_admin_user)):
    users = await db.users.find().to_list(1000)
    user_stats = []
    
    for user in users:
        user = parse_from_mongo(user)
        user_id = user['id']
        
        # Get user's contact and template counts
        contacts_count = await db.contacts.count_documents({"user_id": user_id})
        templates_count = await db.templates.count_documents({"user_id": user_id})
        
        # Calculate total usage (contacts + templates)
        total_usage = contacts_count + templates_count
        
        user_stats.append(UserStats(
            id=user_id,
            email=user['email'],
            full_name=user['full_name'],
            subscription_status=user.get('subscription_status', 'trial'),
            subscription_expires=user.get('subscription_expires'),
            is_admin=user.get('is_admin', False),
            created_at=user['created_at'],
            contacts_count=contacts_count,
            templates_count=templates_count,
            last_login=user.get('last_login'),
            total_usage=total_usage
        ))
    
    # Sort by total usage descending
    user_stats.sort(key=lambda x: x.total_usage, reverse=True)
    return user_stats

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

# Include the router in the main app
app.include_router(api_router)

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

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}