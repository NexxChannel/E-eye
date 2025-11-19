from sqlalchemy.orm import Session
from . import models, schemas
from argon2 import PasswordHasher, exceptions

Hasher = PasswordHasher()

def hashPassword(rawPassword: str) -> str:
    return Hasher.hash(rawPassword)

def verifyPassword(hashedPassword: str, rawPassword: str) -> bool:
    try:
        return Hasher.verify(hashedPassword, rawPassword)
    except exceptions.VerifyMismatchError:
        return False

def getUserByEmail(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def createUser(db: Session, userIn: schemas.UserCreate) -> models.User:
    hashed = hashPassword(userIn.password)
    dbUser = models.User(
        email=userIn.email,
        hashedPassword=hashed
    )
    db.add(dbUser)
    db.commit()
    db.refresh(dbUser)
    return dbUser
