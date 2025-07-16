"""
Authentication and authorization utilities for the NFT-Gated AI Trading Bot.
"""

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from web3 import Web3
import jwt
from config import get_settings
from core.tasks import logger

settings = get_settings()
security = HTTPBearer(auto_error=False)


class AuthError(Exception):
    """Custom authentication error."""
    pass

def get_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        x_wallet_address: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get current user with real wallet address.

    This function now returns the real wallet address derived from the private key
    when in real data mode, or allows bypass mode for testing.
    """

    # If NFT gating is bypassed, get real wallet address
    if settings.bypass_nft_gate:

        # If we're in real data mode, get the actual wallet address
        if (settings.real_data_mode and
                hasattr(settings, 'private_key') and
                settings.private_key and
                settings.private_key != "0x0000000000000000000000000000000000000000000000000000000000000000"):

            try:
                # Get real wallet address from private key
                w3 = Web3()  # No provider needed just for address derivation
                account = w3.eth.account.from_key(settings.private_key)
                real_wallet_address = account.address

                return {
                    "wallet_address": real_wallet_address,  # Real address!
                    "authenticated": True,
                    "bypass": True,
                    "nft_verified": False,
                    "permissions": {
                        "trade": True,
                        "view_portfolio": True,
                        "manage_strategies": True,
                        "admin": settings.debug
                    }
                }

            except Exception as e:
                logger.error(f"Failed to derive wallet address: {e}")
                # Fall back to mock if there's an issue
                pass

        # Fallback to mock data if not in real mode or if there's an error
        return {
            "wallet_address": x_wallet_address or "0x0000000000000000000000000000000000000000",
            "authenticated": True,
            "bypass": True,
            "nft_verified": False,
            "permissions": {
                "trade": True,
                "view_portfolio": True,
                "manage_strategies": True,
                "admin": settings.debug
            }
        }

    # If no credentials provided and bypass is disabled
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Verify JWT token (for production NFT-gated access)
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=["HS256"]
        )

        wallet_address = payload.get("wallet_address")
        if not wallet_address:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing wallet address"
            )

        return {
            "wallet_address": wallet_address,
            "authenticated": True,
            "bypass": False,
            "nft_verified": payload.get("nft_verified", False),
            "permissions": payload.get("permissions", {})
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# Alternative simpler version if you want to force real wallet always:
def get_real_wallet_address() -> str:
    """Get the real wallet address from private key."""
    settings = get_settings()

    if not hasattr(settings, 'private_key') or not settings.private_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Private key not configured"
        )

    try:
        w3 = Web3()
        account = w3.eth.account.from_key(settings.private_key)
        return account.address
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to derive wallet address: {e}"
        )

def verify_access_optional(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        x_wallet_address: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication that allows access even without valid credentials.

    This function is used for endpoints that can work with or without authentication.
    It checks if NFT bypass is enabled or if valid credentials are provided.

    Args:
        credentials: Bearer token credentials (optional)
        x_wallet_address: Wallet address from header (optional)

    Returns:
        User info dict if authenticated, None if not authenticated but allowed

    Raises:
        HTTPException: Only if there's a critical authentication error
    """
    # If NFT gating is bypassed, allow access without authentication
    if settings.bypass_nft_gate:
        return {
            "wallet_address": x_wallet_address or "bypass_user",
            "authenticated": False,
            "bypass": True,
            "nft_verified": False,
            "permissions": {
                "trade": True,
                "view_portfolio": True,
                "admin": settings.debug  # Admin access only in debug mode
            }
        }

    # If no credentials provided, return None (unauthenticated but allowed)
    if not credentials:
        return None

    try:
        # Verify JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=["HS256"]
        )

        wallet_address = payload.get("wallet_address")
        if not wallet_address:
            return None

        return {
            "wallet_address": wallet_address,
            "authenticated": True,
            "bypass": False,
            "nft_verified": payload.get("nft_verified", False),
            "permissions": payload.get("permissions", {})
        }

    except jwt.ExpiredSignatureError:
        # Token expired - log but don't block for optional auth
        return None
    except jwt.InvalidTokenError:
        # Invalid token - log but don't block for optional auth
        return None
    except Exception as e:
        # Other auth errors - log but don't block for optional auth
        return None


def verify_access_required(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        x_wallet_address: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Required authentication that blocks access without valid credentials.

    This function is used for endpoints that require authentication.

    Args:
        credentials: Bearer token credentials (required)
        x_wallet_address: Wallet address from header (optional)

    Returns:
        User info dict

    Raises:
        HTTPException: If authentication fails
    """
    # If NFT gating is bypassed, allow access
    if settings.bypass_nft_gate:
        return {
            "wallet_address": x_wallet_address or "bypass_user",
            "authenticated": True,
            "bypass": True,
            "nft_verified": False,
            "permissions": {
                "trade": True,
                "view_portfolio": True,
                "admin": settings.debug
            }
        }

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Verify JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=["HS256"]
        )

        wallet_address = payload.get("wallet_address")
        if not wallet_address:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing wallet address"
            )

        return {
            "wallet_address": wallet_address,
            "authenticated": True,
            "bypass": False,
            "nft_verified": payload.get("nft_verified", False),
            "permissions": payload.get("permissions", {})
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def verify_admin_access(
        user: Dict[str, Any] = Depends(verify_access_required)
) -> Dict[str, Any]:
    """
    Verify admin access permissions.

    Args:
        user: User info from authentication

    Returns:
        User info dict

    Raises:
        HTTPException: If user doesn't have admin permissions
    """
    if not user.get("permissions", {}).get("admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return user


def create_access_token(wallet_address: str, nft_verified: bool = False) -> str:
    """
    Create a JWT access token for authenticated user.

    Args:
        wallet_address: User's wallet address
        nft_verified: Whether user has verified NFT ownership

    Returns:
        JWT token string
    """
    import datetime

    payload = {
        "wallet_address": wallet_address,
        "nft_verified": nft_verified,
        "permissions": {
            "trade": True,
            "view_portfolio": True,
            "admin": False  # Set based on your admin logic
        },
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }

    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return token


def verify_nft_ownership(wallet_address: str, contract_address: Optional[str] = None) -> bool:
    """
    Verify NFT ownership for a wallet address.

    Args:
        wallet_address: Wallet address to check
        contract_address: NFT contract address (optional)

    Returns:
        True if user owns required NFT, False otherwise
    """
    # If bypass is enabled, always return True
    if settings.bypass_nft_gate:
        return True

    # Add your actual NFT verification logic here
    # This could involve:
    # - Calling a blockchain RPC
    # - Checking with OpenSea API
    # - Using your own NFT verification service

    # For now, return True for demo purposes
    return True