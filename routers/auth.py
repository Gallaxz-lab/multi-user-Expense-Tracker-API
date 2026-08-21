from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timezone, timedelta

from database.connection import get_db
import models.user as models_user
import schemas.auth as schemas_auth
from services.security import hash_password, verify_password, create_access_token
from config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: schemas_auth.UserRegister, db: Session = Depends(get_db)):
    existing = db.query(models_user.User).filter(models_user.User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = models_user.User(username=payload.username, hashed_password=hash_password(payload.password))
    db.add(new_user)
    db.commit()
    return {"status": "success", "message": "User registered successfully"}

@router.post("/login", response_model=schemas_auth.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models_user.User).filter(models_user.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models_user.User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token credentials")
    user = db.query(models_user.User).filter(models_user.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
