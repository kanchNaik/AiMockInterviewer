from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from ..core.database import db  # <-- relative import

from datetime import datetime, timedelta
import secrets
from typing import Optional


router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v):
        return str(v).strip().lower()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v):
        return str(v).strip().lower()

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v):
        return str(v).strip().lower()


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    # optional extra safety check
    email: Optional[EmailStr] = None

@router.post("/signup")
async def signup(payload: SignupRequest):
    hashed_pw = pwd_context.hash(payload.password)
    try:
        res = await db["users"].insert_one({
            "email": str(payload.email),
            "password": hashed_pw,
            "createdAt": datetime.utcnow(),
        })
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="User already exists")
    # return userId so frontend can store it
    return {
        "message": "Signup successful",
        "email": str(payload.email),
        "userId": str(res.inserted_id),
    }

@router.post("/login")
async def login(payload: LoginRequest):
    user = await db["users"].find_one({"email": str(payload.email)})
    if not user or not pwd_context.verify(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # include userId for linking sessions
    return {
        "message": "Login successful",
        "email": user["email"],
        "userId": str(user["_id"]),
    }

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    """
    Generate a one-time reset token.

    In a real app you would email this link.
    For this project we return the token in JSON so the frontend
    can redirect straight to the reset form.
    """
    email = str(payload.email)

    user = await db["users"].find_one({"email": email})
    if not user:
        # don't reveal if user exists; keep the message generic
        return {"message": "If this email exists, we sent a reset link."}

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    await db["users"].update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "resetToken": token,
                "resetExpires": expires_at,
            }
        },
    )

    return {
        "message": "If this email exists, we sent a reset link.",
        "token": token,  # frontend will use this to go to /reset-password
    }


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest):
    """
    Validate reset token and update the user's password.
    """
    token = payload.token.strip()
    new_password = payload.new_password

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password too short.")

    now = datetime.utcnow()

    user = await db["users"].find_one(
        {
            "resetToken": token,
            "resetExpires": {"$gt": now},
        }
    )

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")

    # optional: double-check email if the client sends it
    if payload.email:
        if user.get("email", "").lower() != str(payload.email).strip().lower():
            raise HTTPException(status_code=400, detail="Token does not match this email.")

    # hash new password & update
    hashed = pwd_context.hash(new_password)

    await db["users"].update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password": hashed},
            "$unset": {"resetToken": "", "resetExpires": ""},
        },
    )

    return {"message": "Password has been reset successfully."}
