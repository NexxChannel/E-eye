import hmac

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import engine, SessionLocal, Base
from sqlalchemy.exc import IntegrityError


Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-eye MVP API")
authScheme = HTTPBearer(auto_error=False)

# CORS - allow origins from environment (development default for Vite)
_allowed = os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173")
allowed_origins = [o.strip() for o in _allowed.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def healthCheck():
    return {"status": "ok"}


@app.post("/users", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def registerUser(userIn: schemas.UserCreate, db: Session = Depends(getDb)):
    dbUser = crud.getUserByEmail(db, email=userIn.email)
    if dbUser:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    try:
        newUser = crud.createUser(db, userIn)
        return newUser
    except IntegrityError:
        # handle race-condition where email was inserted concurrently
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )


@app.post("/auth/login")
def loginUser(userIn: schemas.UserLogin, db: Session = Depends(getDb)):
    dbUser = crud.getUserByEmail(db, email=userIn.email)

    if dbUser and crud.verifyPassword(dbUser.hashedPassword, userIn.password):
        accessToken = crud.createAccessToken(dbUser)

        return {"accessToken": accessToken, "tokenType": "Bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )


def getCurrentUser(
    credentials: HTTPAuthorizationCredentials = Depends(authScheme),
    db: Session = Depends(getDb),
) -> models.User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )

    token = schemas.Token(
        accessToken=credentials.credentials, tokenType=credentials.scheme
    )

    if not hmac.compare_digest(token.tokenType, "Bearer"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )

    try:
        user = crud.getCurrentUser(token.accessToken, db)
    except Exception as e:
        # normalize any parsing/validation error from token handling
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e) or "Invalid token",
        )

    if isinstance(user, models.User):
        return user

    # If getCurrentUser returned None, treat as invalid
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
    )


@app.get("/me")
def verifyUser(currentUser: models.User = Depends(getCurrentUser)):
    return currentUser
