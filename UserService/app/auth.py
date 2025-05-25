from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv, dotenv_values 

load_dotenv() 

context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def pwToHash(password: str) -> str:
    return context.hash(password)

def verifyPW(plain_password: str, hashed_password: str) -> bool:
    return context.verify(plain_password, hashed_password)

def createToken(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))