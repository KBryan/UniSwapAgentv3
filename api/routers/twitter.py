"""
Twitter API endpoints for the NFT-Gated AI Trading Bot.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# Simple auth dependency
def simple_auth_optional():
    return {"authenticated": False, "bypass": True}

router = APIRouter(prefix="/twitter", tags=["twitter"])

# Import Twitter client
try:
    from core.twitter_integration import twitter_client
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False
    twitter_client = None

class TweetRequest(BaseModel):
    message: str
    hashtags: Optional[List[str]] = None

class TweetResponse(BaseModel):
    success: bool
    tweet_id: Optional[str] = None
    tweet_url: Optional[str] = None
    message: str
    task_id: Optional[str] = None

@router.get("/status")
async def get_twitter_status(user=Depends(simple_auth_optional)):
    """Get Twitter integration status."""
    if not TWITTER_AVAILABLE:
        return {
            "enabled": False,
            "status": "not_available",
            "message": "Twitter integration module not found"
        }

    return {
        "enabled": twitter_client.is_enabled() if twitter_client else False,
        "status": "connected" if twitter_client and twitter_client.is_enabled() else "disabled",
        "username": twitter_client.username if twitter_client else None,
        "message": "Twitter integration status"
    }

@router.post("/tweet", response_model=TweetResponse)
async def send_tweet(
        tweet_request: TweetRequest,
        user=Depends(simple_auth_optional)
):
    """Send a custom tweet."""
    if not TWITTER_AVAILABLE or not twitter_client or not twitter_client.is_enabled():
        return TweetResponse(
            success=False,
            message="Twitter integration is not enabled"
        )

    # For now, just log the tweet (since it's a stub)
    from core.tasks import tweet_custom_message
    task = tweet_custom_message.delay(tweet_request.message, tweet_request.hashtags)

    return TweetResponse(
        success=True,
        message="Tweet queued for sending",
        task_id=task.id
    )