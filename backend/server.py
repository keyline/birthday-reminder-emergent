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

class BulkUploadResponse(BaseModel):
    total_rows: int
    successful_imports: int
    failed_imports: int
    errors: List[str]
    imported_contacts: List[Contact]

class UserSettingsCreate(BaseModel):
    # WhatsApp API Provider Selection
    whatsapp_provider: Optional[str] = "facebook"  # "facebook" or "digitalsms"
    
    # Facebook Graph API (existing)
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    
    # DigitalSMS API (new)
    digitalsms_api_key: Optional[str] = None
    
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
    
    # WhatsApp API Provider
    whatsapp_provider: str = "facebook"  # "facebook" or "digitalsms"
    
    # Facebook Graph API
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    
    # DigitalSMS API
    digitalsms_api_key: Optional[str] = None
    
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
            total_usage=total_usage,
            whatsapp_credits=user.get('whatsapp_credits', 0),
            email_credits=user.get('email_credits', 0),
            unlimited_whatsapp=user.get('unlimited_whatsapp', False),
            unlimited_email=user.get('unlimited_email', False)
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
    settings = await db.user_settings.find_one({"user_id": current_user.id})
    
    if not settings:
        raise HTTPException(status_code=400, detail="Settings not found")
    
    whatsapp_provider = settings.get("whatsapp_provider", "facebook")
    
    try:
        import requests
        
        if whatsapp_provider == "facebook":
            # Test Facebook Graph API
            phone_number_id = settings.get("whatsapp_phone_number_id")
            access_token = settings.get("whatsapp_access_token")
            
            if not phone_number_id or not access_token:
                return {"status": "error", "message": "Facebook WhatsApp configuration incomplete"}
            
            url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Test message payload
            payload = {
                "messaging_product": "whatsapp",
                "to": "1234567890",  # Test number (won't actually send)
                "type": "text",
                "text": {
                    "body": "Test configuration - Facebook WhatsApp API"
                }
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code in [200, 400]:  # 400 might be invalid number, but credentials are valid
                return {"status": "success", "message": "Facebook WhatsApp API configuration is valid", "provider": "facebook"}
            else:
                return {"status": "error", "message": f"Facebook WhatsApp API test failed: {response.text}"}
                
        elif whatsapp_provider == "digitalsms":
            # Test DigitalSMS API
            api_key = settings.get("digitalsms_api_key")
            
            if not api_key:
                return {"status": "error", "message": "DigitalSMS API key not configured"}
            
            url = "https://demo.digitalsms.biz/api/"
            params = {
                "apikey": api_key,
                "mobile": "1234567890",  # Test mobile number (won't actually send)
                "msg": "Test configuration from ReminderAI - Your DigitalSMS API is working correctly!"
            }
            
            # Make test request
            response = requests.get(url, params=params)
            
            # DigitalSMS API response handling
            if response.status_code == 200:
                response_text = response.text.strip()
                
                # Check for success indicators
                if any(indicator in response_text.lower() for indicator in ["success", "sent", "ok", "delivered", "queued"]):
                    return {"status": "success", "message": f"DigitalSMS API is valid. Response: {response_text}", "provider": "digitalsms"}
                elif any(error in response_text.lower() for error in ["invalid", "error", "fail", "unauthorized", "forbidden"]):
                    return {"status": "error", "message": f"DigitalSMS API test failed: {response_text}"}
                else:
                    # If we get a response but can't determine success/failure, assume it's working
                    return {"status": "success", "message": f"DigitalSMS API responded: {response_text}", "provider": "digitalsms"}
            else:
                return {"status": "error", "message": f"DigitalSMS API HTTP error {response.status_code}: {response.text}"}
        
        else:
            return {"status": "error", "message": f"Unknown WhatsApp provider: {whatsapp_provider}"}
            
    except Exception as e:
        return {"status": "error", "message": f"WhatsApp API test error: {str(e)}"}

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

# WhatsApp Message Sending Functions
async def send_whatsapp_message(user_id: str, phone_number: str, message: str, image_url: Optional[str] = None):
    """Send WhatsApp message using configured provider"""
    settings = await db.user_settings.find_one({"user_id": user_id})
    
    if not settings:
        return {"status": "error", "message": "No WhatsApp configuration found"}
    
    whatsapp_provider = settings.get("whatsapp_provider", "facebook")
    
    try:
        import requests
        
        if whatsapp_provider == "facebook":
            phone_number_id = settings.get("whatsapp_phone_number_id")
            access_token = settings.get("whatsapp_access_token")
            
            if not phone_number_id or not access_token:
                return {"status": "error", "message": "Facebook WhatsApp configuration incomplete"}
            
            url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Prepare message payload
            if image_url:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": phone_number,
                    "type": "image",
                    "image": {
                        "link": image_url,
                        "caption": message
                    }
                }
            else:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": phone_number,
                    "type": "text",
                    "text": {
                        "body": message
                    }
                }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                return {"status": "success", "message": "Message sent via Facebook WhatsApp API"}
            else:
                return {"status": "error", "message": f"Facebook API error: {response.text}"}
                
        elif whatsapp_provider == "digitalsms":
            api_key = settings.get("digitalsms_api_key")
            
            if not api_key:
                return {"status": "error", "message": "DigitalSMS API key not configured"}
            
            url = "https://demo.digitalsms.biz/api/"
            
            # DigitalSMS API doesn't support images in the provided format
            # So we'll send text message only
            if image_url:
                message = f"{message}\n\nImage: {image_url}"
            
            params = {
                "apikey": api_key,
                "mobile": phone_number,
                "msg": message
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                response_text = response.text.lower()
                if "success" in response_text or "sent" in response_text or "ok" in response_text:
                    return {"status": "success", "message": "Message sent via DigitalSMS API"}
                else:
                    return {"status": "error", "message": f"DigitalSMS API error: {response.text}"}
            else:
                return {"status": "error", "message": f"DigitalSMS API HTTP error: {response.status_code}"}
        
        else:
            return {"status": "error", "message": f"Unknown WhatsApp provider: {whatsapp_provider}"}
            
    except Exception as e:
        return {"status": "error", "message": f"WhatsApp sending error: {str(e)}"}

@api_router.post("/send-whatsapp-test")
async def send_test_whatsapp_message(phone_number: str, current_user: User = Depends(get_current_user)):
    """Send a test WhatsApp message"""
    result = await send_whatsapp_message(
        user_id=current_user.id,
        phone_number=phone_number,
        message="Test message from ReminderAI - Your WhatsApp API is working correctly!"
    )
    return result

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
    
    # Return file URL
    file_url = f"/uploads/images/{unique_filename}"
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

# Include the router in the main app
app.include_router(api_router)

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

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}