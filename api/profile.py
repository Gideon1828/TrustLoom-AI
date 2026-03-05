"""
profile.py - User Profile Management Module (DB-Backed)

All profile data (name, avatar, company, etc.) is stored in the
`user_profiles` PostgreSQL table.  Supabase SERVICE_ROLE_KEY is used
for every database operation so profile reads/writes never fail due
to expired user tokens.

User identity is verified via JWT - with a fallback that decodes the
JWT offline and confirms the user exists via the Admin API.  This
means profile endpoints stay functional even when the access token is
slightly expired (the frontend interceptor will retry after refresh).

Endpoints:
    GET    /api/profile          - Fetch profile (DB + auth merge)
    PATCH  /api/profile          - Update profile fields
    POST   /api/profile/password - Change / add password
    POST   /api/profile/picture  - Upload picture (Cloudinary -> DB)
    POST   /api/feedback         - Submit feedback
    DELETE /api/profile          - Delete account

@module profile
"""

import os
import logging
import httpx
import jwt as pyjwt
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import cloudinary
import cloudinary.uploader

from api.user_db import (
    get_user_profile,
    upsert_user_profile,
    update_user_profile,
    delete_user_profile,
    build_user_response,
)

# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
    )
    logger.info("Cloudinary configured successfully")
else:
    logger.warning("Cloudinary not configured. Set CLOUDINARY_* variables in .env")


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class UpdateProfileRequest(BaseModel):
    """Profile update request model."""
    full_name: Optional[str] = Field(None, min_length=2)
    organization: Optional[str] = None          # maps to DB `company`
    job_title: Optional[str] = None
    phone: Optional[str] = None
    email_preferences: Optional[Dict[str, Any]] = None  # kept in user_metadata


class UpdatePasswordRequest(BaseModel):
    """Password update request model."""
    current_password: Optional[str] = Field(None, alias="currentPassword")
    new_password: str = Field(..., min_length=8, alias="newPassword")
    is_oauth_user: bool = Field(False, alias="isOAuthUser")

    class Config:
        populate_by_name = True


class FeedbackRequest(BaseModel):
    """Feedback submission request model."""
    type: str = Field(..., description="bug, feature, improvement, question")
    subject: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    priority: Optional[str] = Field("medium", description="low, medium, high")


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(prefix="/api", tags=["profile"])
security = HTTPBearer()


# ============================================================================
# AUTH HELPER - robust JWT verification with admin fallback
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Verify the caller identity.

    Strategy:
      1. Verify the access token with Supabase  (online, preferred).
      2. If that fails (e.g. token just expired), decode the JWT
         offline to extract the user-id, then confirm the user
         still exists via the Admin API (SERVICE_ROLE_KEY).

    Returns the raw Supabase user dict (id, email, user_metadata, ...).
    """
    token = credentials.credentials

    # --- Strategy 1: online verification with user token ---
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {token}",
                },
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Online token verification failed: {e}")

    # --- Strategy 2: offline JWT decode + admin lookup ---
    try:
        decoded = pyjwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no subject")

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
                headers={
                    "apikey": SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                },
            )
            if resp.status_code == 200:
                logger.info(f"Authenticated via admin fallback: {user_id}")
                return resp.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Admin fallback failed: {e}")

    raise HTTPException(status_code=401, detail="Invalid or expired token")


async def _update_user_metadata_admin(
    user_id: str, metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update Supabase user_metadata via Admin API (SERVICE_ROLE_KEY).
    Used only for data that must remain in auth.users (e.g. email_preferences).
    """
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
            },
            json={"user_metadata": metadata},
        )
        if resp.status_code != 200:
            logger.error(f"update_user_metadata_admin: {resp.status_code} - {resp.text}")
            raise HTTPException(status_code=500, detail="Failed to update user metadata")
        return resp.json()


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.patch("/profile/tutorial-seen")
async def mark_tutorial_seen(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Mark the tutorial as seen for the current user.
    Sets tutorial_seen = true in user_profiles.
    """
    user_id = current_user.get("id")
    updated = await update_user_profile(user_id, {"tutorial_seen": True})
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update tutorial status")
    return {"success": True, "message": "Tutorial marked as seen"}


@router.get("/profile")
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Fetch the caller profile.
    Merges DB profile data with Supabase auth metadata.
    """
    user_id = current_user.get("id")
    db_profile = await get_user_profile(user_id)

    # Auto-create profile row if missing (first-time login via older flow)
    if db_profile is None:
        user_metadata = current_user.get("user_metadata", {})
        db_profile = await upsert_user_profile(user_id, {
            "email": current_user.get("email"),
            "full_name": (
                user_metadata.get("full_name")
                or user_metadata.get("name")
                or user_metadata.get("preferred_username")
            ),
            "avatar_url": (
                user_metadata.get("picture_url")
                or user_metadata.get("avatar_url")
                or user_metadata.get("picture")
            ),
            "company": user_metadata.get("organization"),
            "email_verified": current_user.get("email_confirmed_at") is not None,
        })

    return {
        "success": True,
        "message": "Profile fetched",
        "user": build_user_response(current_user, db_profile),
    }


@router.patch("/profile")
async def update_profile_endpoint(
    request: UpdateProfileRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update profile fields.

    Writes to `user_profiles` table (full_name, company, job_title, phone).
    If email_preferences is provided, it is stored in Supabase user_metadata.
    """
    user_id = current_user.get("id")

    # ---- Build DB updates ----
    db_updates: Dict[str, Any] = {}
    if request.full_name is not None:
        db_updates["full_name"] = request.full_name
    if request.organization is not None:
        db_updates["company"] = request.organization
    if request.job_title is not None:
        db_updates["job_title"] = request.job_title
    if request.phone is not None:
        db_updates["phone"] = request.phone

    # Write to DB (upsert so it works even if row does not exist yet)
    if db_updates:
        db_updates["email"] = current_user.get("email")
        db_profile = await upsert_user_profile(user_id, db_updates)
    else:
        db_profile = await get_user_profile(user_id)

    # ---- email_preferences -> user_metadata (Supabase auth) ----
    if request.email_preferences is not None:
        existing_meta = current_user.get("user_metadata", {})
        existing_meta["email_preferences"] = request.email_preferences
        if request.full_name is not None:
            existing_meta["full_name"] = request.full_name
        if request.organization is not None:
            existing_meta["organization"] = request.organization
        await _update_user_metadata_admin(user_id, existing_meta)

    # Also keep user_metadata in sync for full_name/organization
    if db_updates and ("full_name" in db_updates or "company" in db_updates):
        try:
            existing_meta = current_user.get("user_metadata", {})
            if "full_name" in db_updates:
                existing_meta["full_name"] = db_updates["full_name"]
            if "company" in db_updates:
                existing_meta["organization"] = db_updates["company"]
            await _update_user_metadata_admin(user_id, existing_meta)
        except Exception as e:
            logger.warning(f"Metadata sync skipped: {e}")

    return {
        "success": True,
        "message": "Profile updated successfully",
        "user": build_user_response(current_user, db_profile),
    }


@router.post("/profile/password")
async def update_password(
    request: UpdatePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Change or add a password.

    - For regular users: verifies current password first.
    - For OAuth users: sets a password so they can also log in with email.
    """
    user_id = current_user.get("id")
    user_email = current_user.get("email")

    # ---- Verify current password (non-OAuth) ----
    if not request.is_oauth_user and request.current_password:
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "email": user_email,
                    "password": request.current_password,
                },
            )
            if login_resp.status_code != 200:
                raise HTTPException(
                    status_code=400, detail="Current password is incorrect"
                )

    # ---- Set new password via Admin API ----
    update_payload: Dict[str, Any] = {
        "password": request.new_password,
        "email_confirm": True,
    }

    if request.is_oauth_user:
        current_app = current_user.get("app_metadata", {})
        providers = list(current_app.get("providers", []))
        if "email" not in providers:
            providers.append("email")
            update_payload["app_metadata"] = {**current_app, "providers": providers}

    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
            },
            json=update_payload,
        )
        if resp.status_code != 200:
            logger.error(f"Password update failed: {resp.text}")
            raise HTTPException(status_code=500, detail="Failed to update password")

    # ---- For OAuth: create email identity ----
    if request.is_oauth_user:
        try:
            async with httpx.AsyncClient() as client:
                link_resp = await client.post(
                    f"{SUPABASE_URL}/auth/v1/admin/generate_link",
                    headers={
                        "apikey": SUPABASE_SERVICE_ROLE_KEY,
                        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "type": "signup",
                        "email": user_email,
                        "password": request.new_password,
                    },
                )
                if link_resp.status_code == 200:
                    logger.info(f"Email identity created for OAuth user {user_id}")
                else:
                    logger.warning(
                        f"generate_link: {link_resp.status_code} - {link_resp.text}"
                    )
        except Exception as e:
            logger.warning(f"Email identity creation skipped: {e}")

    # ---- Re-authenticate to get fresh session tokens ----
    # The Admin API password change invalidates existing sessions,
    # so we sign the user back in immediately to keep them logged in.
    session_data = None
    try:
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "email": user_email,
                    "password": request.new_password,
                },
            )
            if login_resp.status_code == 200:
                token_data = login_resp.json()
                session_data = {
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_at": token_data.get("expires_at", 0),
                }
                logger.info(f"Re-authenticated user {user_id} after password change")
            else:
                logger.warning(f"Re-auth after password change failed: {login_resp.status_code}")
    except Exception as e:
        logger.warning(f"Re-auth after password change skipped: {e}")

    # Fetch DB profile for the response
    db_profile = await get_user_profile(user_id)
    user_info = build_user_response(current_user, db_profile)

    msg = (
        "Password added successfully! You can now sign in with email and password."
        if request.is_oauth_user
        else "Password updated successfully"
    )

    response_data = {"success": True, "message": msg, "user": user_info}
    if session_data:
        response_data["session"] = session_data
    return response_data


@router.post("/profile/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Upload a profile picture to Cloudinary, then persist the URL
    in both user_profiles.avatar_url (DB) and user_metadata.picture_url
    (Supabase auth) for maximum compatibility.
    """
    # ---- Validate ----
    allowed = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPEG, PNG, and WebP images are allowed.",
        )

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")

    # ---- Upload to Cloudinary ----
    user_id = current_user.get("id")
    upload_result = cloudinary.uploader.upload(
        contents,
        folder="trustloom/profile_pictures",
        public_id=f"user_{user_id}",
        overwrite=True,
        resource_type="image",
        transformation=[
            {"width": 400, "height": 400, "crop": "fill", "gravity": "face"},
            {"quality": "auto"},
            {"fetch_format": "auto"},
        ],
    )
    picture_url = upload_result.get("secure_url")

    # ---- Persist in user_profiles table ----
    db_profile = await upsert_user_profile(user_id, {
        "email": current_user.get("email"),
        "avatar_url": picture_url,
    })

    # ---- Also update user_metadata for Supabase UI compatibility ----
    try:
        meta = current_user.get("user_metadata", {})
        meta["picture_url"] = picture_url
        await _update_user_metadata_admin(user_id, meta)
    except Exception as e:
        logger.warning(f"Metadata picture sync skipped: {e}")

    user_response = build_user_response(current_user, db_profile)
    # Ensure the freshly-uploaded URL is used (override any stale cache)
    user_response["avatar_url"] = picture_url
    user_response["picture_url"] = picture_url

    return {
        "success": True,
        "message": "Profile picture uploaded successfully",
        "user": user_response,
        "picture_url": picture_url,
    }


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Submit user feedback (bug reports, feature requests, etc.)
    Logged server-side.  In production, hook into a ticketing system.
    """
    user_email = current_user.get("email")
    user_name = current_user.get("user_metadata", {}).get("full_name", "Unknown")

    logger.info(
        f"FEEDBACK RECEIVED:\n"
        f"   Type: {request.type}\n"
        f"   Priority: {request.priority}\n"
        f"   From: {user_name} ({user_email})\n"
        f"   Subject: {request.subject}\n"
        f"   Description: {request.description}"
    )

    return {
        "success": True,
        "message": "Thank you for your feedback! We will review it shortly.",
    }


@router.delete("/profile")
async def delete_account(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Permanently delete user account.

    1. Remove profile picture from Cloudinary
    2. Delete row from user_profiles
    3. Delete user from Supabase Auth
    """
    user_id = current_user.get("id")

    # ---- Get avatar from DB to clean up Cloudinary ----
    db_profile = await get_user_profile(user_id)
    avatar_url = (
        (db_profile.get("avatar_url") if db_profile else None)
        or current_user.get("user_metadata", {}).get("picture_url")
    )

    if avatar_url and "cloudinary" in avatar_url:
        try:
            public_id = f"trustloom/profile_pictures/user_{user_id}"
            cloudinary.uploader.destroy(public_id)
            logger.info(f"Deleted Cloudinary picture for {user_id}")
        except Exception as e:
            logger.warning(f"Cloudinary cleanup failed: {e}")

    # ---- Delete from user_profiles ----
    await delete_user_profile(user_id)

    # ---- Delete from Supabase Auth ----
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            },
        )
        if resp.status_code not in (200, 204):
            logger.error(f"Auth user deletion failed: {resp.text}")
            raise HTTPException(status_code=500, detail="Failed to delete account")

    logger.info(f"Account deleted: {user_id}")
    return {"success": True, "message": "Account deleted successfully"}
