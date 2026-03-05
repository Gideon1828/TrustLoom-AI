"""
history.py - Evaluation History API

Stores and retrieves user evaluation history.
Enables ChatGPT-like sidebar with previous evaluations.

Endpoints:
- GET /api/history - List user's evaluations
- GET /api/history/{id} - Get specific evaluation
- POST /api/history - Save new evaluation
- PATCH /api/history/{id} - Update evaluation (archive, rename)
- DELETE /api/history/{id} - Delete evaluation
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_REST_URL = f"{SUPABASE_URL}/rest/v1"

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class EvaluationCreate(BaseModel):
    """Create evaluation request."""
    title: str = Field(..., min_length=1, max_length=200)
    evaluation_type: str = Field(default="single")
    resume_filename: Optional[str] = None
    resume_url: Optional[str] = None
    resume_text: Optional[str] = None
    result_data: Dict[str, Any]
    overall_score: Optional[float] = None
    trust_score: Optional[float] = None


class EvaluationUpdate(BaseModel):
    """Update evaluation request."""
    title: Optional[str] = None
    is_archived: Optional[bool] = None


class EvaluationResponse(BaseModel):
    """Evaluation response model."""
    id: str
    user_id: str
    title: str
    evaluation_type: str
    resume_filename: Optional[str] = None
    resume_url: Optional[str] = None
    result_data: Dict[str, Any]
    overall_score: Optional[float] = None
    trust_score: Optional[float] = None
    created_at: str
    updated_at: str
    is_archived: bool = False


class HistoryListResponse(BaseModel):
    """History list response."""
    success: bool
    evaluations: List[Dict[str, Any]]
    total: int
    page: int
    limit: int


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(prefix="/api/history", tags=["History"])
security = HTTPBearer()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_user_from_token(token: str) -> Optional[Dict]:
    """Verify token and get user info from Supabase."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {token}"
                }
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


async def supabase_request(
    method: str,
    endpoint: str,
    token: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None
) -> httpx.Response:
    """Make authenticated request to Supabase REST API."""
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    async with httpx.AsyncClient() as client:
        url = f"{SUPABASE_REST_URL}/{endpoint}"
        
        if method == "GET":
            return await client.get(url, headers=headers, params=params)
        elif method == "POST":
            return await client.post(url, headers=headers, json=data)
        elif method == "PATCH":
            return await client.patch(url, headers=headers, json=data, params=params)
        elif method == "DELETE":
            return await client.delete(url, headers=headers, params=params)
        else:
            raise ValueError(f"Unsupported method: {method}")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=HistoryListResponse)
async def list_evaluations(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    evaluation_type: Optional[str] = None,
    include_archived: bool = False
):
    """
    List user's evaluation history.
    
    Returns paginated list of evaluations for sidebar display.
    """
    token = credentials.credentials
    
    # Verify user
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        # Build query params
        params = {
            "select": "id,title,evaluation_type,resume_filename,overall_score,trust_score,created_at,is_archived",
            "order": "created_at.desc",
            "offset": str((page - 1) * limit),
            "limit": str(limit)
        }
        
        # Filter by type if specified
        if evaluation_type:
            params["evaluation_type"] = f"eq.{evaluation_type}"
        
        # Filter archived
        if not include_archived:
            params["is_archived"] = "eq.false"
        
        # Make request
        response = await supabase_request(
            "GET",
            "evaluation_history",
            token,
            params=params
        )
        
        if response.status_code != 200:
            logger.error(f"Supabase error: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to fetch evaluations")
        
        evaluations = response.json()
        
        # Get total count (separate query)
        count_params = {"select": "id", "user_id": f"eq.{user['id']}"}
        if not include_archived:
            count_params["is_archived"] = "eq.false"
        
        count_response = await supabase_request(
            "GET",
            "evaluation_history",
            token,
            params=count_params
        )
        
        total = len(count_response.json()) if count_response.status_code == 200 else 0
        
        return HistoryListResponse(
            success=True,
            evaluations=evaluations,
            total=total,
            page=page,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List evaluations error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch evaluations")


@router.get("/{evaluation_id}")
async def get_evaluation(
    evaluation_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get specific evaluation with full result data.
    
    Used when user clicks on a history item to view full results.
    """
    token = credentials.credentials
    
    # Verify user
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        response = await supabase_request(
            "GET",
            "evaluation_history",
            token,
            params={"id": f"eq.{evaluation_id}", "select": "*"}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch evaluation")
        
        evaluations = response.json()
        
        if not evaluations:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        return {
            "success": True,
            "evaluation": evaluations[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get evaluation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch evaluation")


@router.post("")
async def save_evaluation(
    evaluation: EvaluationCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Save a new evaluation to history.
    
    Called after each evaluation to persist results.
    """
    token = credentials.credentials
    
    # Verify user
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        # Prepare data
        data = {
            "user_id": user["id"],
            "title": evaluation.title,
            "evaluation_type": evaluation.evaluation_type,
            "resume_filename": evaluation.resume_filename,
            "resume_url": evaluation.resume_url,
            "resume_text": evaluation.resume_text,
            "result_data": evaluation.result_data,
            "overall_score": evaluation.overall_score,
            "trust_score": evaluation.trust_score
        }
        
        response = await supabase_request(
            "POST",
            "evaluation_history",
            token,
            data=data
        )
        
        if response.status_code not in [200, 201]:
            logger.error(f"Save error: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to save evaluation")
        
        saved = response.json()
        
        return {
            "success": True,
            "message": "Evaluation saved successfully",
            "evaluation": saved[0] if saved else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save evaluation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save evaluation")


@router.patch("/{evaluation_id}")
async def update_evaluation(
    evaluation_id: str,
    update: EvaluationUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update evaluation (rename, archive, etc.).
    """
    token = credentials.credentials
    
    # Verify user
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        # Build update data
        data = {}
        if update.title is not None:
            data["title"] = update.title
        if update.is_archived is not None:
            data["is_archived"] = update.is_archived
            if update.is_archived:
                data["archived_at"] = datetime.utcnow().isoformat()
        
        if not data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        response = await supabase_request(
            "PATCH",
            "evaluation_history",
            token,
            data=data,
            params={"id": f"eq.{evaluation_id}"}
        )
        
        if response.status_code != 200:
            logger.error(f"Update error: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to update evaluation")
        
        updated = response.json()
        
        return {
            "success": True,
            "message": "Evaluation updated successfully",
            "evaluation": updated[0] if updated else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update evaluation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update evaluation")


@router.delete("/{evaluation_id}")
async def delete_evaluation(
    evaluation_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    permanent: bool = False
):
    """
    Delete evaluation.
    
    By default, soft-deletes (archives). Use permanent=true for hard delete.
    """
    token = credentials.credentials
    
    # Verify user
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        if permanent:
            # Hard delete
            response = await supabase_request(
                "DELETE",
                "evaluation_history",
                token,
                params={"id": f"eq.{evaluation_id}"}
            )
        else:
            # Soft delete (archive)
            response = await supabase_request(
                "PATCH",
                "evaluation_history",
                token,
                data={"is_archived": True, "archived_at": datetime.utcnow().isoformat()},
                params={"id": f"eq.{evaluation_id}"}
            )
        
        if response.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail="Failed to delete evaluation")
        
        return {
            "success": True,
            "message": "Evaluation deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete evaluation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete evaluation")
