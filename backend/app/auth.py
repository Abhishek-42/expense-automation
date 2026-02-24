from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Secret key to sign the JWT tokens (In production, load this from an environment variable)
SECRET_KEY = "super_secret_temporary_key_for_testing"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Setup Passlib for bcrypt hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Password Hashing Functions ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that a plain password matches the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Creates a bcrypt hash of the given password."""
    return pwd_context.hash(password)


# --- JWT Token Functions ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Generates a secure JWT token containing the given data."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# OAuth2 scheme setup for FastAPI to extract token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Decodes the JWT token and returns the username (user_id)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username


# --- Pydantic Models for JSON Bodies ---

class UserCreate(BaseModel):
    """Defines the JSON structure expected when registering a user."""
    username: str
    password: str

class Token(BaseModel):
    """Defines the structure of the token response."""
    access_token: str
    token_type: str
