import hmac

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import UploadFile, File, Form
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

# serve static files (e.g. uploaded drawings)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
static_dir = os.path.abspath(static_dir)
if not os.path.exists(static_dir):
    try:
        os.makedirs(os.path.join(static_dir, "uploads"), exist_ok=True)
    except Exception:
        pass

app.mount("/static", StaticFiles(directory=static_dir), name="static")


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


@app.post(
    "/projects/create",
    response_model=schemas.ProjectOut,
    status_code=status.HTTP_201_CREATED,
)
def createProject(
    projectIn: schemas.ProjectCreate,
    currentUser: models.User = Depends(getCurrentUser),
    db: Session = Depends(getDb),
):
    return crud.createProject(db=db, ownerId=currentUser.id, projectIn=projectIn)


@app.get("/projects", response_model=list[schemas.ProjectOut])
def listProjects(
    currentUser: models.User = Depends(getCurrentUser),
    db: Session = Depends(getDb),
):
    return crud.listProjectsByOwner(db=db, ownerId=currentUser.id)


@app.get("/projects/{projectId}", response_model=schemas.ProjectOut)
def getProject(
    projectId: int,
    currentUser: models.User = Depends(getCurrentUser),
    db: Session = Depends(getDb),
):
    project = crud.getProjectByIdAndOwner(
        db=db, projectId=projectId, ownerId=currentUser.id
    )
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@app.get("/projects/{projectId}/drawings", response_model=list[schemas.DrawingOut])
def listDrawings(
    projectId: int,
    currentUser: models.User = Depends(getCurrentUser),
    db: Session = Depends(getDb),
):
    project = crud.getProjectByIdAndOwner(
        db=db, projectId=projectId, ownerId=currentUser.id
    )
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    drawings = crud.listDrawingsByProject(db, projectId=projectId)
    return drawings


@app.get("/drawings/{drawingId}", response_model=schemas.DrawingOut)
def getDrawing(
    drawingId: int,
    currentUser: models.User = Depends(getCurrentUser),
    db: Session = Depends(getDb),
):
    drawing = crud.getDrawingById(db, drawingId=drawingId)
    if drawing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Drawing not found"
        )
    # ensure user owns the project
    if drawing.project.ownerId != currentUser.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return drawing


@app.post(
    "/projects/{projectId}/drawings",
    response_model=schemas.DrawingOut,
    status_code=status.HTTP_201_CREATED,
)
def createDrawing(
    projectId: int,
    drawingIn: schemas.DrawingCreate,
    currentUser: models.User = Depends(getCurrentUser),
    db: Session = Depends(getDb),
):
    project = crud.getProjectByIdAndOwner(
        db=db, projectId=projectId, ownerId=currentUser.id
    )
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    drawing = crud.createDrawing(
        db=db, projectId=projectId, drawingIn=drawingIn.model_dump()
    )
    return drawing


@app.post("/projects/{projectId}/drawings/upload", response_model=schemas.DrawingOut)
async def uploadDrawing(
    projectId: int,
    file: UploadFile = File(...),
    name: str | None = Form(None),
    currentUser: models.User = Depends(getCurrentUser),
    db: Session = Depends(getDb),
):
    # validate project exists and belongs to user
    project = crud.getProjectByIdAndOwner(
        db=db, projectId=projectId, ownerId=currentUser.id
    )
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # validate file type
    filename = file.filename
    content_type = file.content_type
    allowed = ("image/png", "image/jpeg", "image/jpg")
    if content_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type"
        )

    # save file to static/uploads with unique name
    import uuid
    from pathlib import Path
    from PIL import Image

    uploads_dir = Path(
        os.path.join(os.path.dirname(__file__), "..", "static", "uploads")
    ).resolve()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(filename).suffix or (".png" if content_type == "image/png" else ".jpg")
    dest_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = uploads_dir / dest_name

    # write file to disk
    with open(dest_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # read image size
    try:
        img = Image.open(dest_path)
        width, height = img.size
    except Exception:
        width = None
        height = None

    fileUrl = f"/static/uploads/{dest_name}"

    drawing_data = {
        "name": name or filename,
        "filePath": fileUrl,
        "width": width,
        "height": height,
        "scale": None,
    }

    drawing = crud.createDrawing(db=db, projectId=projectId, drawingIn=drawing_data)
    return drawing


@app.get("/me/drawings", response_model=list[schemas.DrawingOut])
def myDrawings(
    currentUser: models.User = Depends(getCurrentUser), db: Session = Depends(getDb)
):
    # return all drawings for projects owned by current user
    projects = crud.listProjectsByOwner(db, ownerId=currentUser.id)
    all_drawings = []
    for p in projects:
        ds = crud.listDrawingsByProject(db, projectId=p.id)
        all_drawings.extend(ds)
    # sort by createdAt desc
    all_drawings.sort(key=lambda d: d.createdAt, reverse=True)
    return all_drawings


@app.delete("/drawings/{drawingId}")
def deleteDrawing(
    drawingId: int,
    currentUser: models.User = Depends(getCurrentUser),
    db: Session = Depends(getDb),
):
    drawing = crud.getDrawingById(db, drawingId=drawingId)
    if drawing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Drawing not found"
        )
    # allow only owner of project to delete
    if drawing.project.ownerId != currentUser.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    # attempt to delete file on disk if it's in uploads
    try:
        file_path = drawing.filePath
        # only delete files under static/uploads for safety
        if file_path and file_path.startswith("/static/uploads/"):
            full = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", file_path.lstrip("/"))
            )
            if os.path.exists(full):
                try:
                    os.remove(full)
                except Exception:
                    pass
    except Exception:
        pass

    # delete DB record
    crud.deleteDrawing(db, drawingId=drawingId)

    return {"status": "deleted"}
