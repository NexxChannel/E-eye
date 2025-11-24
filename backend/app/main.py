import hmac

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import engine, SessionLocal, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-eye MVP API")
authScheme = HTTPBearer(auto_error=False)

def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def healthCheck():
    return  {"status": "ok"}

@app.post("/users", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def registerUser(userIn: schemas.UserCreate, db: Session = Depends(getDb)):
    dbUser = crud.getUserByEmail(db, email=userIn.email)
    if dbUser:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    newUser = crud.createUser(db, userIn)
    return newUser

@app.post("/auth/login")
def loginUser(userIn: schemas.UserLogin, db: Session = Depends(getDb)):
    dbUser = crud.getUserByEmail(db, email=userIn.email)

    if dbUser and crud.verifyPassword(dbUser.hashedPassword, userIn.password):
        accessToken = crud.createAccessToken(dbUser)

        return {"accessToken": accessToken, "tokenType": "Bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

def getCurrentUser(
    credentials: HTTPAuthorizationCredentials = Depends(authScheme),
    db: Session = Depends(getDb),
) -> models.User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )

    token = schemas.Token(
        accessToken=credentials.credentials,
        tokenType=credentials.scheme
    )

    if not hmac.compare_digest(token.tokenType, "Bearer"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user = crud.getCurrentUser(token.accessToken, db)
    if isinstance(user, models.User):
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=user or "Invalid token"
    )

@app.post("/me")
def veriftUser(currentUser: models.User = Depends(getCurrentUser)):
    return currentUser
