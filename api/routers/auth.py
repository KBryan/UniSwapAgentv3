"""
Authentication endpoints for NFT-based access control.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import jwt

from config import get_settings
from api.deps import verify_nft_ownership, get_current_user, get_optional_user

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


class NFTVerificationRequest(BaseModel):
    """Request model for NFT verification."""
    wallet_address: str = Field(..., description="Wallet address to verify")
    contract_address: Optional[str] = Field(None, description="NFT contract address (optional)")
    chain_id: Optional[int] = Field(None, description="Chain ID (optional)")
    signature: Optional[str] = Field(None, description="Signed message for verification (optional)")
    message: Optional[str] = Field(None, description="Original message that was signed (optional)")


class NFTVerificationResponse(BaseModel):
    """Response model for NFT verification."""
    verified: bool
    wallet_address: str
    has_nft: bool
    access_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    message: str


class UserInfoResponse(BaseModel):
    """Response model for user information."""
    wallet_address: str
    authenticated: bool
    bypass: bool
    nft_verified: bool
    permissions: Dict[str, bool]


def create_access_token(wallet_address: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token for authenticated user.
    
    Args:
        wallet_address: User's wallet address
        expires_delta: Token expiration time
    
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode = {
        "sub": wallet_address,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access_token"
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt


@router.post("/verify-nft", response_model=NFTVerificationResponse)
async def verify_nft_endpoint(request: NFTVerificationRequest):
    """
    Verify NFT ownership for a wallet address.
    
    This endpoint checks if the provided wallet address owns the required NFT
    and returns an access token if verification is successful.
    """
    try:
        logger.info(f"NFT verification request for wallet: {request.wallet_address}")
        
        # TODO: In production, verify the signature to ensure the user owns the wallet
        # For now, we'll skip signature verification
        
        # Verify NFT ownership
        has_nft = await verify_nft_ownership(
            wallet_address=request.wallet_address,
            contract_address=request.contract_address,
            chain_id=request.chain_id
        )
        
        if has_nft or settings.bypass_nft_gate:
            # Create access token
            access_token_expires = timedelta(hours=24)
            access_token = create_access_token(
                wallet_address=request.wallet_address,
                expires_delta=access_token_expires
            )
            
            return NFTVerificationResponse(
                verified=True,
                wallet_address=request.wallet_address,
                has_nft=has_nft,
                access_token=access_token,
                expires_in=int(access_token_expires.total_seconds()),
                message="NFT verification successful" if has_nft else "Access granted (bypass mode)"
            )
        else:
            return NFTVerificationResponse(
                verified=False,
                wallet_address=request.wallet_address,
                has_nft=False,
                message="NFT ownership required for access"
            )
            
    except Exception as e:
        logger.error(f"NFT verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Verification failed: {str(e)}"
        )


@router.get("/me", response_model=UserInfoResponse)
async def get_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current user information.
    
    Returns information about the authenticated user including wallet address,
    authentication status, and permissions.
    """
    return UserInfoResponse(
        wallet_address=current_user["wallet_address"],
        authenticated=current_user["authenticated"],
        bypass=current_user.get("bypass", False),
        nft_verified=not current_user.get("bypass", False),
        permissions={
            "trade": True,
            "view_portfolio": True,
            "manage_strategies": True,
            "admin": False  # TODO: Implement admin role logic
        }
    )


@router.post("/refresh-token")
async def refresh_access_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Refresh the access token for an authenticated user.
    
    This endpoint allows users to get a new access token without
    going through the full NFT verification process again.
    """
    try:
        # Re-verify NFT ownership for security
        has_nft = await verify_nft_ownership(current_user["wallet_address"])
        
        if has_nft or settings.bypass_nft_gate:
            # Create new access token
            access_token_expires = timedelta(hours=24)
            access_token = create_access_token(
                wallet_address=current_user["wallet_address"],
                expires_delta=access_token_expires
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": int(access_token_expires.total_seconds()),
                "message": "Token refreshed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="NFT ownership no longer valid"
            )
            
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Logout the current user.
    
    In a stateless JWT system, logout is primarily handled client-side
    by discarding the token. This endpoint can be used for logging purposes.
    """
    logger.info(f"User logout: {current_user['wallet_address']}")
    
    return {
        "message": "Logout successful",
        "wallet_address": current_user["wallet_address"]
    }


@router.get("/check-access")
async def check_access(user: Optional[Dict[str, Any]] = Depends(get_optional_user)):
    """
    Check if the current request has valid access.
    
    This endpoint can be used by frontend applications to check
    authentication status without requiring authentication.
    """
    if user:
        return {
            "has_access": True,
            "wallet_address": user["wallet_address"],
            "authenticated": user["authenticated"]
        }
    else:
        return {
            "has_access": False,
            "message": "No valid authentication found"
        }

