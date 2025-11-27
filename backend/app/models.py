from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base
from datetime import datetime, UTC


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashedPassword = Column(String, nullable=False)
    isActive = Column(Boolean, default=True)
    subscriptionLevel = Column(String, default="free")
    role = Column(String, default="user")
    projects = relationship("Project", back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    createdAt = Column(DateTime, default=datetime.now(UTC))
    ownerId = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="projects")
    drawings = relationship("Drawing", back_populates="project")


class Drawing(Base):
    __tablename__ = "drawings"

    id = Column(Integer, primary_key=True, index=True)
    projectId = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    filePath = Column(String, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    scale = Column(String, nullable=True)
    # 比例尺校准数据
    pixelsPerMeter = Column(
        String, nullable=True
    )  # JSON string: {pixelsPerMeter: float, actualDistance: float, pixelDistance: float}
    createdAt = Column(DateTime, default=datetime.now(UTC))

    project = relationship("Project", back_populates="drawings")
