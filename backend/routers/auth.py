"""
Authentication router - register, login, forgot password, profile management.
"""
import os
import uuid
import secrets
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File

import resend
from database import db
from config import RESEND_API_KEY, SENDER_EMAIL
from models.user import (
    UserRegister,
    UserLogin,
    UserUpdate,
    LocationPermissionUpdate,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from services.auth_service import (
    hash_password,
    verify_password,
    create_token,
    get_current_user,
)

# Initialize resend if configured
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
async def register(data: UserRegister):
    """Register a new user"""
    # Check if email already exists
    existing = await db.auth_users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username exists
    existing_username = await db.auth_users.find_one({"username": data.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": data.email.lower(),
        "username": data.username,
        "password_hash": hash_password(data.password),
        "birth_year": data.birth_year,
        "birth_date": data.birth_date,
        "avatar_url": None,
        "favorite_genres": [],
        "location_permission": None,
        "location": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.auth_users.insert_one(user_doc)
    
    # Create token
    token = create_token(user_id)
    
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": data.email.lower(),
            "username": data.username,
            "birth_year": data.birth_year,
            "birth_date": data.birth_date,
            "avatar_url": None,
            "favorite_genres": [],
            "location_permission": None
        }
    }


@router.post("/login")
async def login(data: UserLogin):
    """Login user"""
    user = await db.auth_users.find_one({"email": data.email.lower()})
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email address")
    
    if not verify_password(data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    # Create token
    token = create_token(user["id"])
    
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "birth_year": user.get("birth_year", 1995),
            "birth_date": user.get("birth_date"),
            "avatar_url": user.get("avatar_url"),
            "favorite_genres": user.get("favorite_genres", []),
            "location_permission": user.get("location_permission"),
            "gender": user.get("gender"),
            "bio": user.get("bio"),
            "favorite_actors": user.get("favorite_actors", []),
            "favorite_movies": user.get("favorite_movies", []),
            "favorite_directors": user.get("favorite_directors", []),
            "letterboxd_connected": user.get("letterboxd_connected", False),
            "letterboxd_count": user.get("letterboxd_count", 0)
        }
    }


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current logged in user"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user


@router.put("/profile")
async def update_profile(data: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Update user profile"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    update_data = {}
    if data.username is not None:
        # Check username not taken
        existing = await db.auth_users.find_one({
            "username": data.username, 
            "id": {"$ne": current_user["id"]}
        })
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        update_data["username"] = data.username
    
    if data.birth_year is not None:
        update_data["birth_year"] = data.birth_year
    
    if data.birth_date is not None:
        update_data["birth_date"] = data.birth_date
    
    if data.avatar_url is not None:
        update_data["avatar_url"] = data.avatar_url
    
    if data.favorite_genres is not None:
        update_data["favorite_genres"] = data.favorite_genres
    
    if data.gender is not None:
        update_data["gender"] = data.gender
    
    if data.bio is not None:
        update_data["bio"] = data.bio[:150]
    
    if data.favorite_actors is not None:
        update_data["favorite_actors"] = data.favorite_actors[:20]
    
    if data.favorite_movies is not None:
        update_data["favorite_movies"] = data.favorite_movies[:5]
    
    if data.streaming_services is not None:
        update_data["streaming_services"] = data.streaming_services
    
    if data.favorite_directors is not None:
        update_data["favorite_directors"] = data.favorite_directors[:20]
    
    if update_data:
        await db.auth_users.update_one(
            {"id": current_user["id"]},
            {"$set": update_data}
        )
    
    # Return updated user
    user = await db.auth_users.find_one({"id": current_user["id"]}, {"_id": 0, "password_hash": 0})
    return user


@router.post("/logout")
async def logout():
    """Logout (client should delete token)"""
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """Send password reset email"""
    email = data.email.lower().strip()
    user = await db.auth_users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email address")
    
    # Generate a secure reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    
    # Store reset token in DB
    await db.password_resets.update_one(
        {"user_id": user["id"]},
        {"$set": {
            "user_id": user["id"],
            "email": email,
            "token": reset_token,
            "expires_at": expires_at,
            "used": False
        }},
        upsert=True
    )
    
    # Build reset URL
    frontend_url = os.environ.get("FRONTEND_URL", "https://diary-watch.preview.emergentagent.com")
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    
    # Send email via Resend
    email_sent = False
    if RESEND_API_KEY:
        try:
            params = {
                "from": SENDER_EMAIL,
                "to": [email],
                "subject": "Chef - Reset Your Password",
                "html": f"""
                <div style="font-family: Georgia, serif; max-width: 480px; margin: 0 auto; padding: 40px 24px; background: #0a0a0a; color: #e5e5e5;">
                    <h1 style="font-size: 24px; color: #f5f0e8; margin-bottom: 16px;">Reset your password</h1>
                    <p style="font-size: 14px; line-height: 1.6; color: #999;">
                        We received a request to reset the password for your Chef account. Click the button below to set a new password.
                    </p>
                    <a href="{reset_url}" style="display: inline-block; margin: 24px 0; padding: 12px 32px; background: #2dd4bf22; border: 1px solid #2dd4bf44; color: #2dd4bf; text-decoration: none; border-radius: 9999px; font-size: 14px;">
                        Reset Password
                    </a>
                    <p style="font-size: 12px; color: #666; margin-top: 24px;">
                        This link expires in 1 hour. If you didn't request this, you can ignore this email.
                    </p>
                </div>
                """
            }
            await asyncio.to_thread(resend.Emails.send, params)
            email_sent = True
            logging.info(f"Password reset email sent to {email}")
        except Exception as e:
            logging.warning(f"Email send failed (will provide direct link): {e}")
    
    if email_sent:
        return {"message": "Password reset link sent to your email"}
    else:
        # Return reset URL directly when email can't be sent
        return {"message": "Reset link generated", "reset_url": reset_url}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Reset password using token from email"""
    record = await db.password_resets.find_one(
        {"token": data.token, "used": False},
        {"_id": 0}
    )
    
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    
    # Check expiry
    try:
        expires_str = record["expires_at"]
        # Handle timezone-aware and naive datetime strings
        expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
        # Make expires timezone-aware if it's naive
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")
    except (ValueError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid reset link")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Update password
    new_hash = hash_password(data.new_password)
    await db.auth_users.update_one(
        {"id": record["user_id"]},
        {"$set": {"password_hash": new_hash}}
    )
    
    # Mark token as used
    await db.password_resets.update_one(
        {"token": data.token},
        {"$set": {"used": True}}
    )
    
    return {"message": "Password reset successfully. You can now log in."}


@router.put("/location-permission")
async def update_location_permission(data: LocationPermissionUpdate, current_user: dict = Depends(get_current_user)):
    """Update user's location permission preference"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    update_data = {"location_permission": data.location_permission}
    if data.latitude is not None and data.longitude is not None:
        update_data["location"] = {
            "latitude": data.latitude,
            "longitude": data.longitude
        }
    
    await db.auth_users.update_one(
        {"id": current_user["id"]},
        {"$set": update_data}
    )
    
    return {"message": "Location permission updated", "location_permission": data.location_permission}


@router.post("/upload-avatar")
async def upload_avatar(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload user avatar photo"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, and GIF images are allowed")
    
    # Read file (max 2MB)
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 2MB")
    
    # Save to uploads directory
    os.makedirs("/app/uploads/avatars", exist_ok=True)
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{current_user['id']}.{ext}"
    filepath = f"/app/uploads/avatars/{filename}"
    
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Store URL path in user record
    avatar_url = f"/api/uploads/avatars/{filename}"
    await db.auth_users.update_one(
        {"id": current_user["id"]},
        {"$set": {"avatar_url": avatar_url}}
    )
    
    return {"avatar_url": avatar_url}
