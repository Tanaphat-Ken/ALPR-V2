"""
Pytest configuration and fixtures for testing ALPR General API
"""
import pytest
import pytest_asyncio
import asyncio
import sys
import os
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from Configs.dbconfig import Base, get_db
from Models.users import User
from Models.subscription import Subscription
from Models.user_subscription import UserSubscription
from Models.token import Token
from Libs.auth import get_password_hash

# Load test environment variables
load_dotenv()

# Test database URL
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "alpr_service_test")
TEST_DB_USER = os.getenv("DB_USER", "alpr")
TEST_DB_PASSWORD = os.getenv("DB_PASSWORD", "P@ssw0rd").replace('@', '%40')
TEST_DB_HOST = os.getenv("DB_HOST", "localhost")
TEST_DB_PORT = os.getenv("DB_PORT", "5432")

TEST_DATABASE_URL = f"postgresql+asyncpg://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"


@pytest_asyncio.fixture(scope="module")
async def test_engine():
    """Create a test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database dependency override"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# Test Data Fixtures

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user"""
    hashed_password = get_password_hash("Test@12345")
    result = await User.new_user(
        email="test@example.com",
        password=hashed_password,
        db=db_session
    )
    # Get the full user object
    user = await User.get_user_by_email("test@example.com", db_session)
    return user


@pytest_asyncio.fixture
async def test_admin_user(db_session: AsyncSession) -> User:
    """Create a test admin user"""
    hashed_password = get_password_hash("Admin@12345")
    result = await User.new_user(
        email="admin@example.com",
        password=hashed_password,
        db=db_session
    )
    # Get the full user object
    user = await User.get_user_by_email("admin@example.com", db_session)
    return user


@pytest_asyncio.fixture
async def test_subscription_tier1(db_session: AsyncSession) -> Subscription:
    """Create TIER_1 subscription"""
    subscription = Subscription(
        billing_period="monthly",
        service_type="TIER_1",
        api_request_limit=1000,
        token_limit=5,
        price=0,
        has_api_access=1,
        has_websocket_access=0,
        has_video_upload=0,
        has_rtsp_stream=0,
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


@pytest_asyncio.fixture
async def test_subscription_tier2(db_session: AsyncSession) -> Subscription:
    """Create TIER_2 subscription"""
    subscription = Subscription(
        billing_period="monthly",
        service_type="TIER_2",
        api_request_limit=1000,
        token_limit=10,
        video_upload_limit=1000,
        price=299,
        has_api_access=1,
        has_websocket_access=1,
        has_video_upload=1,
        has_rtsp_stream=0,
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


@pytest_asyncio.fixture
async def test_subscription_tier3(db_session: AsyncSession) -> Subscription:
    """Create TIER_3 subscription"""
    subscription = Subscription(
        billing_period="monthly",
        service_type="TIER_3",
        api_request_limit=5000,
        token_limit=20,
        video_upload_limit=5000,
        price=999,
        has_api_access=1,
        has_websocket_access=1,
        has_video_upload=1,
        has_rtsp_stream=1,
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


@pytest_asyncio.fixture
async def test_user_subscription(
    db_session: AsyncSession, 
    test_user: User, 
    test_subscription_tier1: Subscription
) -> UserSubscription:
    """Create an active user subscription"""
    from datetime import date, timedelta
    
    user_sub = UserSubscription(
        user_id=test_user.user_id,
        sub_id=test_subscription_tier1.sub_id,
        is_activate=True,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        request_quota=test_subscription_tier1.api_request_limit
    )
    db_session.add(user_sub)
    await db_session.commit()
    await db_session.refresh(user_sub)
    return user_sub


@pytest_asyncio.fixture
async def test_token_api(
    db_session: AsyncSession,
    test_user: User,
    test_user_subscription: UserSubscription
) -> Token:
    """Create a test API token"""
    from datetime import datetime, timedelta
    
    token = await Token.new_token(
        user_id=test_user.user_id,
        service_type="API",
        token_name="Test API Token",
        expire_time=datetime.now() + timedelta(days=30),
        db=db_session
    )
    return token


@pytest_asyncio.fixture
async def test_token_websocket(
    db_session: AsyncSession,
    test_user: User,
) -> Token:
    """Create a test WebSocket token (requires TIER_2 or above)"""
    from datetime import datetime, timedelta
    
    # First, create a TIER_2 subscription for the user
    tier2_sub = Subscription(
        service_type="TIER_2",
        api_request_limit=1000,
        max_token=10,
        video_upload_limit=1000,
        price=299,
        has_api_access=True,
        has_websocket_access=True,
        has_video_upload=True,
        has_rtsp_stream=False,
    )
    db_session.add(tier2_sub)
    await db_session.commit()
    await db_session.refresh(tier2_sub)
    
    user_sub = await UserSubscription.create_user_subscription(
        user_id=test_user.user_id,
        sub_id=tier2_sub.sub_id,
        db=db_session
    )
    
    token = await Token.new_token(
        user_id=test_user.user_id,
        service_type="WEBSOCKET",
        token_name="Test WebSocket Token",
        expire_time=datetime.now() + timedelta(days=30),
        db=db_session
    )
    return token


@pytest.fixture
def sample_token_data():
    """Sample token data for testing"""
    from datetime import datetime, timedelta
    
    return {
        "service_type": "API",
        "token_name": "Sample Token",
        "expire_time": datetime.now() + timedelta(days=30)
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "NewUser@12345",
        "tel": "0823456789"
    }
