from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional, Union, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field
from motor.motor_asyncio import AsyncIOMotorClient
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from google.oauth2 import id_token
from google.auth.transport import requests
import os
import sys
import json
import uuid
import asyncio
import logging
import sqlite3
import csv
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, User, PeerChannel
from telethon.errors import FloodWaitError, RPCError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'telegram_scraper')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# JWT Authentication settings
SECRET_KEY = os.environ.get('SECRET_KEY')
ALGORITHM = os.environ.get('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

# Telegram API credentials
TELEGRAM_API_ID = int(os.environ.get('TELEGRAM_API_ID'))
TELEGRAM_API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Google OAuth settings
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 token bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Email config disabled for testing
email_config = None

# Initialize FastAPI app
app = FastAPI(title="Telegram Scraper API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router with /api prefix
from fastapi import APIRouter
api_router = APIRouter(prefix="/api")

# Data models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleLogin(BaseModel):
    token: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ResetPassword(BaseModel):
    email: EmailStr

class NewPassword(BaseModel):
    token: str
    password: str

class ChannelModel(BaseModel):
    channel_id: str
    last_message_id: int = 0

class TelegramCredentials(BaseModel):
    api_id: int
    api_hash: str
    phone: str

class User(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    hashed_password: str
    telegram_credentials: Optional[TelegramCredentials] = None
    channels: Dict[str, int] = {}
    scrape_media: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
class ScrapeSettings(BaseModel):
    scrape_media: bool

# Authentication Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(email: str):
    user = await db.users.find_one({"email": email})
    if user:
        return User(**user)
    return None

async def authenticate_user(email: str, password: str):
    user = await get_user(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = await get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# API Routes
@api_router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)
    
    user = {
        "id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "hashed_password": hashed_password,
        "telegram_credentials": None,
        "channels": {},
        "scrape_media": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user)
    
    return {
        "id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name
    }

@api_router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/google-login", response_model=Token)
async def google_login(data: GoogleLogin):
    try:
        # Verify the Google token
        idinfo = id_token.verify_oauth2_token(
            data.token, requests.Request(), GOOGLE_CLIENT_ID
        )
        
        # Extract user info
        email = idinfo.get('email')
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Google token"
            )
        
        # Check if user exists, create if not
        user = await db.users.find_one({"email": email})
        if not user:
            user_id = str(uuid.uuid4())
            user = {
                "id": user_id,
                "email": email,
                "full_name": idinfo.get('name'),
                # No password since this is Google auth
                "hashed_password": get_password_hash(str(uuid.uuid4())),
                "telegram_credentials": None,
                "channels": {},
                "scrape_media": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.users.insert_one(user)
        
        # Generate JWT token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    except ValueError:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )

@app.post("/reset-password")
async def reset_password(data: ResetPassword):
    user = await get_user(data.email)
    if not user:
        # Don't reveal that the user doesn't exist
        return {"message": "If your email is registered, a password reset link will be sent"}
    
    # Generate a token
    reset_token = create_access_token(
        data={"sub": user.email, "reset": True}, 
        expires_delta=timedelta(hours=1)
    )
    
    # For testing, just return the token
    return {"message": "Password reset requested", "token": reset_token}

@app.post("/set-new-password")
async def set_new_password(data: NewPassword):
    try:
        # Verify token
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        is_reset = payload.get("reset")
        
        if not email or not is_reset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        
        # Hash new password
        hashed_password = get_password_hash(data.password)
        
        # Update user
        result = await db.users.update_one(
            {"email": email},
            {"$set": {"hashed_password": hashed_password, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "Password updated successfully"}
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

@app.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name
    }

@app.post("/telegram-credentials")
async def set_telegram_credentials(credentials: TelegramCredentials, current_user: User = Depends(get_current_user)):
    result = await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "telegram_credentials": credentials.dict(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update credentials"
        )
    
    return {"message": "Telegram credentials set successfully"}

@app.get("/telegram-credentials")
async def get_telegram_credentials(current_user: User = Depends(get_current_user)):
    if not current_user.telegram_credentials:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram credentials not set"
        )
    
    return current_user.telegram_credentials

@app.get("/channels")
async def get_channels(current_user: User = Depends(get_current_user)):
    return {"channels": current_user.channels}

@app.post("/channels")
async def add_channel(channel: ChannelModel, current_user: User = Depends(get_current_user)):
    channels = current_user.channels.copy()
    channels[channel.channel_id] = channel.last_message_id
    
    result = await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                f"channels.{channel.channel_id}": channel.last_message_id,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add channel"
        )
    
    return {"message": f"Channel {channel.channel_id} added successfully"}

@app.delete("/channels/{channel_id}")
async def remove_channel(channel_id: str, current_user: User = Depends(get_current_user)):
    if channel_id not in current_user.channels:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found"
        )
    
    result = await db.users.update_one(
        {"id": current_user.id},
        {
            "$unset": {f"channels.{channel_id}": ""},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove channel"
        )
    
    return {"message": f"Channel {channel_id} removed successfully"}

@app.get("/scrape-settings")
async def get_scrape_settings(current_user: User = Depends(get_current_user)):
    return {"scrape_media": current_user.scrape_media}

@app.post("/scrape-settings")
async def update_scrape_settings(settings: ScrapeSettings, current_user: User = Depends(get_current_user)):
    result = await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "scrape_media": settings.scrape_media,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update scrape settings"
        )
    
    return {"message": "Scrape settings updated successfully"}

# Helper functions for Telegram scraping
def save_message_to_db(user_id, channel, message, sender):
    user_dir = os.path.join(os.getcwd(), 'data', user_id)
    channel_dir = os.path.join(user_dir, channel)
    os.makedirs(channel_dir, exist_ok=True)

    db_file = os.path.join(channel_dir, f'{channel}.db')
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute(f'''CREATE TABLE IF NOT EXISTS messages
                  (id INTEGER PRIMARY KEY, message_id INTEGER, date TEXT, sender_id INTEGER, first_name TEXT, last_name TEXT, username TEXT, message TEXT, media_type TEXT, media_path TEXT, reply_to INTEGER)''')
    c.execute('''INSERT OR IGNORE INTO messages (message_id, date, sender_id, first_name, last_name, username, message, media_type, media_path, reply_to)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (message.id, 
               message.date.strftime('%Y-%m-%d %H:%M:%S'), 
               message.sender_id,
               getattr(sender, 'first_name', None) if isinstance(sender, User) else None, 
               getattr(sender, 'last_name', None) if isinstance(sender, User) else None,
               getattr(sender, 'username', None) if isinstance(sender, User) else None,
               message.message, 
               message.media.__class__.__name__ if message.media else None, 
               None,
               message.reply_to_msg_id if message.reply_to else None))
    conn.commit()
    conn.close()

async def download_media(user_id, channel, message, scrape_media=True):
    if not message.media or not scrape_media:
        return None

    user_dir = os.path.join(os.getcwd(), 'data', user_id)
    channel_dir = os.path.join(user_dir, channel)
    media_folder = os.path.join(channel_dir, 'media')
    os.makedirs(media_folder, exist_ok=True)    
    media_file_name = None
    
    if isinstance(message.media, MessageMediaPhoto):
        media_file_name = message.file.name or f"{message.id}.jpg"
    elif isinstance(message.media, MessageMediaDocument):
        media_file_name = message.file.name or f"{message.id}.{message.file.ext if message.file.ext else 'bin'}"
    
    if not media_file_name:
        logger.warning(f"Unable to determine file name for message {message.id}. Skipping download.")
        return None
    
    media_path = os.path.join(media_folder, media_file_name)
    
    if os.path.exists(media_path):
        logger.info(f"Media file already exists: {media_path}")
        return media_path

    MAX_RETRIES = 5
    retries = 0
    while retries < MAX_RETRIES:
        try:
            if isinstance(message.media, MessageMediaPhoto):
                media_path = await message.download_media(file=media_folder)
            elif isinstance(message.media, MessageMediaDocument):
                media_path = await message.download_media(file=media_folder)
            if media_path:
                logger.info(f"Successfully downloaded media to: {media_path}")
            break
        except Exception as e:
            retries += 1
            logger.warning(f"Retrying download for message {message.id}. Attempt {retries}... Error: {str(e)}")
            await asyncio.sleep(2 ** retries)
    
    return media_path

async def get_telegram_client(user_id):
    user = await db.users.find_one({"id": user_id})
    if not user or not user.get("telegram_credentials"):
        return None
    
    credentials = user["telegram_credentials"]
    session_path = os.path.join(os.getcwd(), 'sessions', user_id)
    os.makedirs(os.path.dirname(session_path), exist_ok=True)
    
    client = TelegramClient(
        session_path, 
        credentials["api_id"], 
        credentials["api_hash"]
    )
    
    return client

@app.post("/scrape/{channel_id}")
async def scrape_channel(channel_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.telegram_credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram credentials not set"
        )
    
    if channel_id not in current_user.channels:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found"
        )
    
    # Start the scraping process in the background
    # In a real production app, you would use a task queue like Celery
    # For simplicity, we'll create a background task
    
    background_task = asyncio.create_task(
        scrape_channel_task(
            current_user.id, 
            channel_id, 
            current_user.channels[channel_id],
            current_user.scrape_media
        )
    )
    
    return {"message": f"Scraping started for channel {channel_id}"}

async def scrape_channel_task(user_id, channel_id, offset_id, scrape_media):
    client = await get_telegram_client(user_id)
    if not client:
        logger.error(f"Failed to get Telegram client for user {user_id}")
        return
    
    try:
        await client.start()
        
        if channel_id.startswith('-'):
            entity = await client.get_entity(PeerChannel(int(channel_id)))
        else:
            entity = await client.get_entity(channel_id)
        
        total_messages = 0
        async for _ in client.iter_messages(entity, offset_id=offset_id, reverse=True):
            total_messages += 1
        
        if total_messages == 0:
            logger.info(f"No messages found in channel {channel_id}")
            await client.disconnect()
            return
        
        last_message_id = None
        processed_messages = 0
        
        async for message in client.iter_messages(entity, offset_id=offset_id, reverse=True):
            try:
                sender = await message.get_sender()
                save_message_to_db(user_id, channel_id, message, sender)
                
                if scrape_media and message.media:
                    media_path = await download_media(user_id, channel_id, message, scrape_media)
                    if media_path:
                        user_dir = os.path.join(os.getcwd(), 'data', user_id)
                        db_file = os.path.join(user_dir, channel_id, f'{channel_id}.db')
                        conn = sqlite3.connect(db_file)
                        c = conn.cursor()
                        c.execute('''UPDATE messages SET media_path = ? WHERE message_id = ?''', (media_path, message.id))
                        conn.commit()
                        conn.close()
                
                last_message_id = message.id
                processed_messages += 1
                
                progress = (processed_messages / total_messages) * 100
                logger.info(f"Scraping channel: {channel_id} - Progress: {progress:.2f}%")
                
                # Update the last message ID in the database
                await db.users.update_one(
                    {"id": user_id},
                    {"$set": {f"channels.{channel_id}": last_message_id}}
                )
            except Exception as e:
                logger.error(f"Error processing message {message.id}: {str(e)}")
        
        logger.info(f"Scraping completed for channel {channel_id}")
    except Exception as e:
        logger.error(f"Error scraping channel {channel_id}: {str(e)}")
    finally:
        await client.disconnect()

@app.get("/channel-data/{channel_id}")
async def get_channel_data(channel_id: str, current_user: User = Depends(get_current_user)):
    if channel_id not in current_user.channels:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found"
        )
    
    user_dir = os.path.join(os.getcwd(), 'data', current_user.id)
    channel_dir = os.path.join(user_dir, channel_id)
    db_file = os.path.join(channel_dir, f'{channel_id}.db')
    
    if not os.path.exists(db_file):
        return {"messages": []}
    
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM messages ORDER BY date DESC LIMIT 100')
    rows = c.fetchall()
    conn.close()
    
    messages = [dict(row) for row in rows]
    return {"messages": messages}

@app.get("/export-data/{channel_id}/{format}")
async def export_data(
    channel_id: str, 
    format: str,
    current_user: User = Depends(get_current_user)
):
    if channel_id not in current_user.channels:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found"
        )
    
    if format not in ["csv", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'csv' or 'json'"
        )
    
    user_dir = os.path.join(os.getcwd(), 'data', current_user.id)
    channel_dir = os.path.join(user_dir, channel_id)
    db_file = os.path.join(channel_dir, f'{channel_id}.db')
    
    if not os.path.exists(db_file):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data found for this channel"
        )
    
    if format == "csv":
        output_file = os.path.join(channel_dir, f'{channel_id}.csv')
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute('SELECT * FROM messages')
        rows = c.fetchall()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([description[0] for description in c.description])
            writer.writerows(rows)
        
        conn.close()
        return {"message": "CSV export completed", "path": output_file}
    
    elif format == "json":
        output_file = os.path.join(channel_dir, f'{channel_id}.json')
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM messages')
        rows = c.fetchall()
        
        data = [dict(row) for row in rows]
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        conn.close()
        return {"message": "JSON export completed", "path": output_file}

@app.post("/continuous-scrape/start")
async def start_continuous_scrape(current_user: User = Depends(get_current_user)):
    if not current_user.telegram_credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram credentials not set"
        )
    
    if not current_user.channels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No channels to scrape"
        )
    
    # Store a flag in the database to indicate continuous scraping
    result = await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"continuous_scraping": True}}
    )
    
    # Start the continuous scraping process in the background
    background_task = asyncio.create_task(
        continuous_scraping_task(current_user.id)
    )
    
    return {"message": "Continuous scraping started"}

@app.post("/continuous-scrape/stop")
async def stop_continuous_scrape(current_user: User = Depends(get_current_user)):
    # Update the flag in the database
    result = await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"continuous_scraping": False}}
    )
    
    return {"message": "Continuous scraping stopped"}

async def continuous_scraping_task(user_id):
    while True:
        # Check if continuous scraping is still enabled
        user = await db.users.find_one({"id": user_id})
        if not user or not user.get("continuous_scraping", False):
            logger.info(f"Continuous scraping stopped for user {user_id}")
            break
        
        # Scrape all channels
        for channel_id, last_message_id in user.get("channels", {}).items():
            try:
                logger.info(f"Checking for new messages in channel: {channel_id}")
                await scrape_channel_task(user_id, channel_id, last_message_id, user.get("scrape_media", True))
            except Exception as e:
                logger.error(f"Error in continuous scraping for channel {channel_id}: {str(e)}")
        
        # Wait before checking again
        await asyncio.sleep(60)

@app.get("/channels-list")
async def list_channels(current_user: User = Depends(get_current_user)):
    client = await get_telegram_client(current_user.id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to initialize Telegram client"
        )
    
    try:
        await client.start()
        channels = []
        
        async for dialog in client.iter_dialogs():
            if dialog.id != 777000:  # Exclude service notifications
                channels.append({
                    "id": str(dialog.id),
                    "title": dialog.title
                })
        
        return {"channels": channels}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing channels: {str(e)}"
        )
    finally:
        await client.disconnect()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
