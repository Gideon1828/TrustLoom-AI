"""
auth.py - Backend Authentication Module

Handles all authentication via Supabase on the server side.
API keys are kept secure on the backend.

Endpoints:
- POST /api/auth/register - Create new account
- POST /api/auth/login - Sign in
- POST /api/auth/logout - Sign out
- POST /api/auth/forgot-password - Request password reset
- GET /api/auth/me - Get current user
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv

from api.user_db import (
    get_user_profile,
    upsert_user_profile,
    build_user_response,
)

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Supabase client initialization
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Check if Supabase is configured
SUPABASE_CONFIGURED = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

auth_client = None

if SUPABASE_CONFIGURED:
    try:
        from supabase_auth import SyncGoTrueClient
        auth_client = SyncGoTrueClient(
            url=f"{SUPABASE_URL}/auth/v1",
            headers={"apikey": SUPABASE_ANON_KEY}
        )
        logger.info("✅ Supabase Auth client initialized successfully")
    except ImportError:
        logger.warning("⚠️ Supabase Auth SDK not installed. Run: pip install supabase-auth")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase Auth: {e}")
else:
    logger.warning("⚠️ Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY in .env")


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class RegisterRequest(BaseModel):
    """Registration request model."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    organization: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr


class AuthResponse(BaseModel):
    """Standard auth response model."""
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None
    session: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    """User info response model."""
    id: str
    email: str
    full_name: Optional[str] = None
    organization: Optional[str] = None
    created_at: Optional[str] = None


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_supabase():
    """Check if Supabase is available."""
    if not SUPABASE_CONFIGURED or not auth_client:
        raise HTTPException(
            status_code=503,
            detail="Authentication service not configured. Please contact administrator."
        )


def extract_user_info(user_data: Dict) -> Dict[str, Any]:
    """Extract relevant user info from Supabase response."""
    if not user_data:
        return None
    
    user_metadata = user_data.get("user_metadata", {})
    app_metadata = user_data.get("app_metadata", {})
    
    # For OAuth users, derive full_name from provider metadata if not explicitly set
    full_name = user_metadata.get("full_name")
    if not full_name:
        full_name = user_metadata.get("name") or user_metadata.get("preferred_username")
    
    # Get avatar URL from provider metadata
    avatar_url = (
        user_metadata.get("picture_url")
        or user_metadata.get("avatar_url")
        or user_metadata.get("picture")
    )
    
    return {
        "id": user_data.get("id"),
        "email": user_data.get("email"),
        "full_name": full_name,
        "organization": user_metadata.get("organization"),
        "created_at": user_data.get("created_at"),
        "email_confirmed": user_data.get("email_confirmed_at") is not None,
        "user_metadata": user_metadata,
        "app_metadata": app_metadata,
        "avatar_url": avatar_url
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[Dict]:
    """Get current user from JWT token."""
    if not credentials:
        return None
    
    check_supabase()
    
    try:
        # Get user from token
        token = credentials.credentials
        user_response = auth_client.get_user(token)
        
        if user_response and user_response.user:
            return extract_user_info(user_response.user.__dict__)
        return None
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        return None


async def check_user_exists_by_email(email: str) -> bool:
    """
    Check if a user exists with the given email.
    Uses Supabase Admin API with service role key.
    """
    if not SUPABASE_SERVICE_ROLE_KEY:
        # Fallback: try to query user_profiles table
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{SUPABASE_URL}/rest/v1/user_profiles",
                    params={
                        "email": f"eq.{email}",
                        "select": "id"
                    },
                    headers={
                        "apikey": SUPABASE_ANON_KEY,
                        "Content-Type": "application/json"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return len(data) > 0
        except Exception as e:
            logger.warning(f"Failed to check user_profiles: {e}")
        return None  # Return None to indicate we couldn't verify
    
    try:
        async with httpx.AsyncClient() as client:
            # Use Admin API to list users filtered by email
            response = await client.get(
                f"{SUPABASE_URL}/auth/v1/admin/users",
                params={"filter": f"email.eq.{email}"},
                headers={
                    "apikey": SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                return len(users) > 0
            
            logger.warning(f"Admin API returned {response.status_code}")
            return None  # Couldn't verify
    except Exception as e:
        logger.warning(f"Failed to check user existence: {e}")
        return None  # Couldn't verify


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """
    Register a new user account.
    
    Returns success with user info, or requires email confirmation.
    """
    check_supabase()
    
    try:
        # Create user with Supabase
        response = auth_client.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "full_name": request.full_name,
                    "organization": request.organization or "",
                    "created_at": datetime.utcnow().isoformat()
                }
            }
        })
        
        if response.user:
            raw_auth = response.user.__dict__
            
            # Sync to user_profiles DB table
            db_profile = await upsert_user_profile(response.user.id, {
                "email": request.email,
                "full_name": request.full_name,
                "company": request.organization or "",
                "email_verified": response.user.email_confirmed_at is not None
                    if hasattr(response.user, 'email_confirmed_at') else False,
            })
            
            user_info = build_user_response(raw_auth, db_profile)
            
            # Check if email confirmation is required
            if response.session is None:
                return AuthResponse(
                    success=True,
                    message="Account created! Please check your email to confirm your account.",
                    user=user_info
                )
            
            # Session exists - user is logged in
            session_data = {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at
            }
            
            return AuthResponse(
                success=True,
                message="Account created successfully!",
                user=user_info,
                session=session_data
            )
        
        raise HTTPException(status_code=400, detail="Failed to create account")
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Registration error: {error_msg}")
        
        # Handle common errors
        if "already registered" in error_msg.lower():
            raise HTTPException(status_code=400, detail="This email is already registered")
        if "password" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Password does not meet requirements")
        
        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Sign in with email and password.
    
    Returns session tokens on success.
    """
    check_supabase()
    
    try:
        response = auth_client.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if response.user and response.session:
            raw_auth = response.user.__dict__
            session_data = {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at
            }
            
            # Upsert profile in DB (creates row if missing, updates last_login_at)
            user_metadata = raw_auth.get("user_metadata", {})
            db_profile = await upsert_user_profile(response.user.id, {
                "email": request.email,
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
                "last_login_at": datetime.utcnow().isoformat(),
                "email_verified": response.user.email_confirmed_at is not None
                    if hasattr(response.user, 'email_confirmed_at') else True,
            })
            
            user_info = build_user_response(raw_auth, db_profile)
            
            return AuthResponse(
                success=True,
                message="Signed in successfully!",
                user=user_info,
                session=session_data
            )
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Login error: {error_msg}")
        
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if "email not confirmed" in error_msg.lower():
            raise HTTPException(status_code=401, detail="Please confirm your email before signing in")
        
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.post("/logout", response_model=AuthResponse)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Sign out the current user."""
    check_supabase()
    
    try:
        if credentials:
            auth_client.sign_out()
        
        return AuthResponse(
            success=True,
            message="Signed out successfully"
        )
    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Still return success - client should clear tokens anyway
        return AuthResponse(
            success=True,
            message="Signed out"
        )


@router.post("/forgot-password", response_model=AuthResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request a password reset email.
    Only sends if account exists.
    """
    check_supabase()
    
    try:
        # Check if user exists before sending reset email
        user_exists = await check_user_exists_by_email(request.email)
        
        if user_exists is False:
            # User definitely doesn't exist
            return AuthResponse(
                success=False,
                message="No account found with this email address. Please check the email or create a new account."
            )
        
        # user_exists is True or None (couldn't verify)
        # Send reset email
        auth_client.reset_password_email(request.email)
        
        return AuthResponse(
            success=True,
            message="Password reset link has been sent to your email."
        )
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        return AuthResponse(
            success=False,
            message="Failed to send password reset email. Please try again later."
        )


@router.get("/me")
async def get_me(user: Dict = Depends(get_current_user)):
    """
    Get current authenticated user info (merged with DB profile).
    """
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Merge with DB profile for complete data
    db_profile = await get_user_profile(user.get("id"))
    merged = build_user_response(user, db_profile) if db_profile else user
    
    return {
        "success": True,
        "user": merged
    }


@router.get("/status")
async def auth_status():
    """
    Check authentication service status.
    """
    return {
        "configured": SUPABASE_CONFIGURED,
        "available": auth_client is not None
    }


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    
    Returns new access and refresh tokens.
    """
    check_supabase()
    
    try:
        response = auth_client.refresh_session(request.refresh_token)
        
        if response.user and response.session:
            raw_auth = response.user.__dict__
            session_data = {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at,
                "expires_in": response.session.expires_in
            }
            
            # Merge with DB profile
            db_profile = await get_user_profile(response.user.id)
            user_info = build_user_response(raw_auth, db_profile)
            
            return AuthResponse(
                success=True,
                message="Token refreshed successfully",
                user=user_info,
                session=session_data
            )
        
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Token refresh error: {error_msg}")
        raise HTTPException(status_code=401, detail="Token refresh failed")


# ============================================================================
# OAUTH ENDPOINTS
# ============================================================================

# Frontend URL for OAuth redirects
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

class OAuthProviderRequest(BaseModel):
    """OAuth provider request."""
    redirect_url: Optional[str] = None


class OAuthUrlResponse(BaseModel):
    """OAuth URL response."""
    success: bool
    url: str
    provider: str


@router.post("/oauth/{provider}", response_model=OAuthUrlResponse)
async def initiate_oauth(provider: str, request: OAuthProviderRequest = None):
    """
    Initiate OAuth flow for a provider (google, github).
    
    Returns the authorization URL to redirect the user to.
    """
    check_supabase()
    
    # Validate provider
    valid_providers = ["google", "github"]
    if provider.lower() not in valid_providers:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid provider. Supported: {', '.join(valid_providers)}"
        )
    
    try:
        # Build redirect URL
        redirect_to = request.redirect_url if request else None
        if not redirect_to:
            redirect_to = f"{FRONTEND_URL}/auth/callback"
        
        # URL encode the redirect URL
        from urllib.parse import quote
        encoded_redirect = quote(redirect_to, safe='')
        
        # Use Supabase's OAuth sign-in URL
        # The auth URL format for Supabase OAuth
        oauth_url = (
            f"{SUPABASE_URL}/auth/v1/authorize"
            f"?provider={provider.lower()}"
            f"&redirect_to={encoded_redirect}"
        )
        
        logger.info(f"OAuth initiated for {provider}, redirect to: {redirect_to}")
        
        return OAuthUrlResponse(
            success=True,
            url=oauth_url,
            provider=provider.lower()
        )
        
    except Exception as e:
        logger.error(f"OAuth initiation error for {provider}: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth")


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request with code or tokens."""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    code: Optional[str] = None
    provider: Optional[str] = None


@router.post("/oauth-callback", response_model=AuthResponse)
async def oauth_callback(request: OAuthCallbackRequest):
    """
    Handle OAuth callback.
    
    Accepts either:
    - access_token + refresh_token (from URL hash after redirect)
    - code (authorization code to exchange)
    
    Returns session data like normal login.
    """
    check_supabase()
    
    # Debug logging
    logger.info(f"OAuth callback received - has access_token: {bool(request.access_token)}, has refresh_token: {bool(request.refresh_token)}, has code: {bool(request.code)}, provider: {request.provider}")
    
    try:
        # If we have tokens directly (Supabase redirects with tokens in hash)
        if request.access_token and request.refresh_token:
            logger.info(f"OAuth callback - Processing tokens for provider: {request.provider}")
            
            raw_auth = None
            
            # Verify the access token by getting user
            try:
                user_response = auth_client.get_user(request.access_token)
                logger.info(f"OAuth callback - get_user response: {bool(user_response)}")
                if user_response and user_response.user:
                    raw_auth = user_response.user.__dict__
            except Exception as auth_err:
                logger.error(f"OAuth callback - get_user failed: {auth_err}")
            
            # If get_user failed, try decoding the JWT directly
            if raw_auth is None:
                import jwt
                try:
                    decoded = jwt.decode(
                        request.access_token, 
                        options={"verify_signature": False}
                    )
                    logger.info(f"OAuth callback - JWT decoded, sub: {decoded.get('sub')}")
                    raw_auth = {
                        "id": decoded.get("sub"),
                        "email": decoded.get("email"),
                        "user_metadata": decoded.get("user_metadata", {}),
                        "app_metadata": decoded.get("app_metadata", {}),
                        "created_at": None,
                        "email_confirmed_at": True,
                    }
                except jwt.DecodeError as jwt_err:
                    logger.error(f"OAuth callback - JWT decode failed: {jwt_err}")
                    raise HTTPException(status_code=401, detail="Invalid access token")
            
            if raw_auth:
                user_metadata = raw_auth.get("user_metadata", {})
                user_id = raw_auth.get("id")
                
                # Get token expiry
                import jwt
                try:
                    decoded = jwt.decode(
                        request.access_token, 
                        options={"verify_signature": False}
                    )
                    expires_at = decoded.get("exp", 0)
                except Exception:
                    expires_at = int(datetime.utcnow().timestamp()) + 3600
                
                session_data = {
                    "access_token": request.access_token,
                    "refresh_token": request.refresh_token,
                    "expires_at": expires_at
                }
                
                # Upsert profile to DB with OAuth data
                db_profile = await upsert_user_profile(user_id, {
                    "email": raw_auth.get("email"),
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
                    "last_login_at": datetime.utcnow().isoformat(),
                    "email_verified": True,
                })
                
                user_info = build_user_response(raw_auth, db_profile)
                
                provider_name = request.provider or "OAuth"
                return AuthResponse(
                    success=True,
                    message=f"Signed in with {provider_name} successfully!",
                    user=user_info,
                    session=session_data
                )
        
        # If we have an authorization code, exchange it
        if request.code:
            # Exchange code for session using Supabase
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SUPABASE_URL}/auth/v1/token",
                    params={"grant_type": "authorization_code"},
                    json={"code": request.code},
                    headers={
                        "apikey": SUPABASE_ANON_KEY,
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    raw_auth = data.get("user", {})
                    user_metadata = raw_auth.get("user_metadata", {})
                    
                    session_data = {
                        "access_token": data.get("access_token"),
                        "refresh_token": data.get("refresh_token"),
                        "expires_at": data.get("expires_at")
                    }
                    
                    # Upsert profile to DB
                    user_id = raw_auth.get("id")
                    db_profile = await upsert_user_profile(user_id, {
                        "email": raw_auth.get("email"),
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
                        "last_login_at": datetime.utcnow().isoformat(),
                        "email_verified": True,
                    })
                    
                    user_info = build_user_response(raw_auth, db_profile)
                    
                    return AuthResponse(
                        success=True,
                        message="OAuth authentication successful!",
                        user=user_info,
                        session=session_data
                    )
        
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid OAuth callback. Missing tokens or code. access_token={bool(request.access_token)}, refresh_token={bool(request.refresh_token)}, code={bool(request.code)}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        import traceback
        logger.error(f"OAuth callback traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=401, 
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.get("/oauth/providers")
async def get_oauth_providers():
    """
    Get available OAuth providers.
    """
    return {
        "providers": [
            {
                "id": "google",
                "name": "Google",
                "enabled": True,
                "icon": "google"
            },
            {
                "id": "github",
                "name": "GitHub", 
                "enabled": True,
                "icon": "github"
            }
        ]
    }
