import enum
from datetime import date

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .database import Base


class InitiativeStatus(str, enum.Enum):
    active = "active"
    at_risk = "at_risk"
    completed = "completed"


class ActionItemStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    done = "done"


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Initiative(Base):
    __tablename__ = "initiatives"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, default="")
    status = Column(Enum(InitiativeStatus), default=InitiativeStatus.active, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    action_items = relationship("ActionItem", back_populates="initiative")


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    transcript = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    action_items = relationship("ActionItem", back_populates="meeting")


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    initiative_id = Column(Integer, ForeignKey("initiatives.id"), nullable=True)
    description = Column(Text, nullable=False)
    owner = Column(String(120), nullable=True)
    deadline = Column(Date, nullable=True)
    priority = Column(Enum(Priority), default=Priority.medium, nullable=False)
    status = Column(Enum(ActionItemStatus), default=ActionItemStatus.pending_review, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    meeting = relationship("Meeting", back_populates="action_items")
    initiative = relationship("Initiative", back_populates="action_items")

    @property
    def is_overdue(self) -> bool:
        return (
            self.deadline is not None
            and self.deadline < date.today()
            and self.status not in (ActionItemStatus.done, ActionItemStatus.rejected)
        )
