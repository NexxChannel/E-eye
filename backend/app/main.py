import hmac

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import engine, SessionLocal, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-eye MVP API")

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
            status_code=status.HTTP_400_BAD_REQUEST,
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

@app.post("/auth/info")
def veriftUser(userIn: schemas.Token, db: Session = Depends(getDb)):
    if not hmac.compare_digest(userIn.tokenType, "Bearer"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user = crud.verifyPassword(userIn.accessToken, db)
    if user:
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )