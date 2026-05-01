from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

load_dotenv()

# load secrets from .env file
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "secret-key-123")
ALGORITHM = "HS256"
EXPIRE_MINUTES = 30

# setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def check_password(plain_pass, hashed_pass):
    # check if the typed password matches the saved hash
    return pwd_context.verify(plain_pass, hashed_pass)

def hash_password(password):
    # turn the password into a secure hash
    return pwd_context.hash(password)

def make_token(data):
    # create a jwt token for the user
    to_encode = data.copy()
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire_time})
    
    # sign it with our secret key
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token=Depends(oauth2_scheme)):
    # read the token to see who is logged in
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise error
    except JWTError:
        raise error

    return username

# models for incoming data
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
