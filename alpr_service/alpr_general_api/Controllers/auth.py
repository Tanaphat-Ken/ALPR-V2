"""
Authentication API endpoints for user login and registration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from Configs.dbconfig import get_db
from Models.users import User
from Models.schemas_user import (
    UserLoginRequest,
    UserLoginResponse,
    UserCreateRequest,
    UserRegisterResponse,
    UserInfoResponse
)
from Libs.auth import (
    get_password_hash,
    create_access_token,
    get_current_active_user
)
from datetime import timedelta

router = APIRouter()


@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    
    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 6 characters)
    
    Returns:
    - User ID, email, and success message
    """
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create new user
    result = await User.new_user(user_data.email, hashed_password, db)
    
    return UserRegisterResponse(
        user_id=result["user_id"],
        email=result["email"],
        message=result["message"]
    )


@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    credentials: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password
    
    - **email**: Registered email address
    - **password**: User password
    
    Returns:
    - JWT access token and user information
    """
    # Verify user credentials
    user = await User.verify_user_password(credentials.email, credentials.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"user_id": user.user_id, "email": user.email},
        expires_delta=timedelta(days=7)
    )
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        email=user.email,
        message="Login successful"
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user information
    
    Requires: Bearer token in Authorization header
    
    Returns:
    - Current user profile data
    """
    user = await User.get_user_info(current_user["user_id"], db)
    
    if not user or len(user) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_data = user[0]
    
    return UserInfoResponse(
        user_id=user_data.user_id,
        email=user_data.email,
        created_at=user_data.created_at,
        updated_at=user_data.updated_at
    )


@router.post("/logout")
async def logout_user(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Logout current user
    
    Note: Since we're using stateless JWT tokens, logout is handled client-side
    by removing the token from storage. This endpoint is provided for consistency.
    
    Requires: Bearer token in Authorization header
    
    Returns:
    - Logout success message
    """
    return {
        "message": "Logout successful",
        "user_id": current_user["user_id"]
    }
