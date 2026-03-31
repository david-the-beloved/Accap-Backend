from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import get_session
from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies import get_current_user
from app.models import User
from app.schemas import GoogleSignInRequest, LoginRequest, SignupRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, session: Session = Depends(get_session)) -> TokenResponse:
    existing = session.exec(select(User).where(
        User.email == payload.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

    user = User(email=payload.email,
                password_hash=hash_password(payload.password))
    session.add(user)
    session.commit()

    token = create_access_token(user.email)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    user = session.exec(select(User).where(
        User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user.email)
    return TokenResponse(access_token=token)


@router.post("/google", response_model=TokenResponse)
def google_sign_in(payload: GoogleSignInRequest, session: Session = Depends(get_session)) -> TokenResponse:
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google sign-in is not configured",
        )

    try:
        info = google_id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    email = info.get("email")
    email_verified = info.get("email_verified")
    if not email or not email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email is not verified",
        )

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        # This password is never used for Google sign-in accounts.
        user = User(email=email, password_hash=hash_password(
            "google-oauth-account"))
        session.add(user)
        session.commit()

    token = create_access_token(email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return UserPublic(
        id=current_user.id,
        email=current_user.email,
        current_streak=current_user.current_streak,
        highest_streak=current_user.highest_streak,
    )
