from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .models import ActionItemStatus, InitiativeStatus, Priority


class InitiativeCreate(BaseModel):
    name: str
    description: str = ""


class InitiativeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    status: InitiativeStatus
    created_at: datetime


class InitiativeDashboard(InitiativeOut):
    total_items: int
    done_items: int
    overdue_items: int


class MeetingCreate(BaseModel):
    title: str
    transcript: str


class ActionItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    meeting_id: int
    initiative_id: Optional[int]
    description: str
    owner: Optional[str]
    deadline: Optional[date]
    priority: Priority
    status: ActionItemStatus
    is_overdue: bool


class MeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    transcript: str
    created_at: datetime
    action_items: list[ActionItemOut]


class ActionItemReview(BaseModel):
    status: Optional[ActionItemStatus] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    deadline: Optional[date] = None
    priority: Optional[Priority] = None
    initiative_id: Optional[int] = None
