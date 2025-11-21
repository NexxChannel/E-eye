from sqlalchemy.orm import Session
from . import models, schemas
from argon2 import PasswordHasher, exceptions
from datetime import datetime, timedelta, UTC
from typing import Any
import json
import base64
import hmac
import hashlib

JWT_SECRET = "E-eye"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTS = 120

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

def _encodeBase64url(data: bytes) -> str:
    encoded = base64.urlsafe_b64encode(data)
    return encoded.rstrip(b"=").decode("ascii")

def _decodeBase64url(encoded: bytes) -> str:
    encoded += "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(s.encode("ascii"))

def _payloadFromUser(data: models.User | dict[str, Any]) -> dict[str, Any]:
    if isinstance(data, dict):
        return data.copy()

    payload = {
        "sub": getattr(data, "id", None),
        "email": getattr(data, "email", None),
        "role": getattr(data, "role", None),
        "subscriptionLevel": getattr(data, "subscriptionLevel", None),
        "isActive": getattr(data, "isActive", None),
    }
    return {key: value for key, value in payload.items() if value is not None}


def createAccessToken(data: models.User | dict[str, Any], expiresMinutes: int | None = None) -> str:
    header = {
        "alg": JWT_ALGORITHM,
        "typ": "JWT",
    }

    payload = _payloadFromUser(data)
    payload["iss"] = "E-eye API"

    if expiresMinutes is None:
        expiresMinutes = ACCESS_TOKEN_EXPIRE_MINUTS

    now = datetime.now(UTC)
    expire = now + timedelta(minutes=expiresMinutes)

    payload.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    })

    headerEncoded = _encodeBase64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payloadEncoded = _encodeBase64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    signingInput = f"{headerEncoded}.{payloadEncoded}"
    signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signingInput.encode("utf-8"),
        hashlib.sha256
    ).digest()

    signatureEncoded = _encodeBase64url(signature)

    return f"{signingInput}.{signatureEncoded}"

def verifyAccessToken(token: str, db: Session) -> models.User | None:
    parts = token.split(".")
    if len(parts) != 3:
        return

    headerB64, payloadB64, signatureB64 = parts

    header = json.loads(_decodeBase64url(bytes(headerB64)))
    payload = json.loads(_decodeBase64url(bytes(payloadB64)))

    now = datetime.now(UTC)
    if now.timestamp() > payload["exp"]:
        return

    if header["alg"] != "HS256":
        return

    signatureInput = f"{headerB64}.{payloadB64}"
    signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signatureInput.encode("utf-8"),
        hashlib.sha256
    ).digest()

    if not hmac.compare_digest(signature, _decodeBase64url(bytes(signatureB64))) :
        return

    return db.query(models.User).filter(models.User.id == payload["sub"]).first()
