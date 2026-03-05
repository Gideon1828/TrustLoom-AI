"""
user_db.py - User Profile Database Operations

Centralized database operations for the `user_profiles` table.
Uses SERVICE_ROLE_KEY to bypass Row Level Security (RLS),
ensuring profile reads/writes never fail due to expired user tokens.

Table Schema (user_profiles):
    id              UUID PRIMARY KEY (references auth.users)
    email           TEXT
    full_name       TEXT
    avatar_url      TEXT
    role            TEXT DEFAULT 'user'
    company         TEXT
    job_title       TEXT
    phone           TEXT
    is_active       BOOLEAN DEFAULT true
    email_verified  BOOLEAN DEFAULT false
    last_login_at   TIMESTAMPTZ
    created_at      TIMESTAMPTZ DEFAULT now()
    updated_at      TIMESTAMPTZ DEFAULT now()

@module user_db
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def _service_headers(*, prefer: str = "") -> Dict[str, str]:
    """Standard headers for service-role DB requests."""
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


# ============================================================================
# CRUD OPERATIONS
# ============================================================================

async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a user profile from the user_profiles table.
    
    Returns:
        Profile dict if found, None otherwise.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/user_profiles",
                params={"id": f"eq.{user_id}", "select": "*"},
                headers=_service_headers(),
            )
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            logger.warning(f"get_user_profile: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"get_user_profile error: {e}")
    return None


async def upsert_user_profile(
    user_id: str, profile_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Insert or update a user profile (ON CONFLICT DO UPDATE).

    None values are stripped so existing data is never overwritten
    with NULL accidentally.

    Returns:
        The upserted profile row, or None on failure.
    """
    try:
        payload = {
            "id": user_id,
            **profile_data,
            "updated_at": datetime.utcnow().isoformat(),
        }
        # Strip None values to avoid overwriting existing data
        payload = {k: v for k, v in payload.items() if v is not None}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/user_profiles",
                headers=_service_headers(
                    prefer="resolution=merge-duplicates,return=representation"
                ),
                json=payload,
            )
            if response.status_code in (200, 201):
                data = response.json()
                return data[0] if data else None
            logger.error(
                f"upsert_user_profile: {response.status_code} - {response.text}"
            )
    except Exception as e:
        logger.error(f"upsert_user_profile error: {e}")
    return None


async def update_user_profile(
    user_id: str, updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Update specific fields in an existing user profile.

    Returns:
        The updated profile row, or None on failure.
    """
    try:
        updates["updated_at"] = datetime.utcnow().isoformat()

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{SUPABASE_URL}/rest/v1/user_profiles",
                params={"id": f"eq.{user_id}"},
                headers=_service_headers(prefer="return=representation"),
                json=updates,
            )
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            logger.error(
                f"update_user_profile: {response.status_code} - {response.text}"
            )
    except Exception as e:
        logger.error(f"update_user_profile error: {e}")
    return None


async def delete_user_profile(user_id: str) -> bool:
    """Delete a user profile row. Returns True on success."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{SUPABASE_URL}/rest/v1/user_profiles",
                params={"id": f"eq.{user_id}"},
                headers=_service_headers(),
            )
            return response.status_code in (200, 204)
    except Exception as e:
        logger.error(f"delete_user_profile error: {e}")
    return False


# ============================================================================
# RESPONSE BUILDER
# ============================================================================

def build_user_response(
    auth_data: Dict[str, Any],
    db_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a unified user response merging Supabase auth data with DB profile.

    Priority: DB profile  >  auth user_metadata  >  defaults

    This ensures profile data persists across sessions regardless of
    token state or OAuth metadata changes.
    """
    user_metadata = auth_data.get("user_metadata", {})
    app_metadata = auth_data.get("app_metadata", {})

    # --- Full Name ---
    full_name = (
        (db_profile.get("full_name") if db_profile else None)
        or user_metadata.get("full_name")
        or user_metadata.get("name")
        or user_metadata.get("preferred_username")
    )

    # --- Avatar URL ---
    avatar_url = (
        (db_profile.get("avatar_url") if db_profile else None)
        or user_metadata.get("picture_url")
        or user_metadata.get("avatar_url")
        or user_metadata.get("picture")
    )

    # --- Organization / Company ---
    organization = (
        (db_profile.get("company") if db_profile else None)
        or user_metadata.get("organization")
    )

    # --- Email confirmed ---
    email_confirmed = False
    if "email_confirmed_at" in auth_data:
        email_confirmed = auth_data.get("email_confirmed_at") is not None
    elif db_profile:
        email_confirmed = db_profile.get("email_verified", False)

    return {
        "id": auth_data.get("id"),
        "email": auth_data.get("email"),
        "full_name": full_name,
        "organization": organization,
        "avatar_url": avatar_url,
        "picture_url": avatar_url,          # backward compat alias
        "job_title": db_profile.get("job_title") if db_profile else None,
        "phone": db_profile.get("phone") if db_profile else None,
        "created_at": (
            auth_data.get("created_at")
            or (db_profile.get("created_at") if db_profile else None)
        ),
        "email_confirmed": email_confirmed,
        "tutorial_seen": db_profile.get("tutorial_seen", False) if db_profile else False,
        "user_metadata": user_metadata,
        "app_metadata": app_metadata,
    }
