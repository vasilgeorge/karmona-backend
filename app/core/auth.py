"""
Authentication utilities for JWT token verification.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWTError

from app.core.config import settings

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> str:
    """
    Verify JWT token and extract user_id.
    
    This dependency:
    1. Extracts the Bearer token from Authorization header
    2. Verifies the JWT signature using Supabase JWT secret
    3. Extracts and returns the user_id (sub claim)
    
    Raises:
        HTTPException: If token is invalid, expired, or missing required claims
    """
    token = credentials.credentials
    
    # Get JWT secret from Supabase
    # The JWT secret is your Supabase project's JWT secret, not the API key
    jwt_secret = settings.supabase_jwt_secret
    
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret not configured",
        )
    
    try:
        # Decode and verify the JWT token
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",  # Supabase sets this
        )
        
        # Extract user_id from 'sub' claim
        user_id: str = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Type alias for cleaner endpoint signatures
CurrentUserId = Annotated[str, Depends(get_current_user_id)]

