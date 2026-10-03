import tempfile
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .graph import run_extraction
from .reports import build_weekly_report, save_weekly_report
from .scheduler import start_scheduler
from .transcription import transcribe

app = FastAPI(title="ActionLoop", description="AI meeting & initiative tracker")

Base.metadata.create_all(bind=engine)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.on_event("startup")
def _startup():
    start_scheduler()


def _create_meeting_with_items(db: Session, title: str, transcript: str) -> models.Meeting:
    meeting = models.Meeting(title=title, transcript=transcript)
    db.add(meeting)
    db.flush()

    for item in run_extraction(transcript):
        db.add(models.ActionItem(meeting_id=meeting.id, **item))

    db.commit()
    db.refresh(meeting)
    return meeting


@app.post("/meetings", response_model=schemas.MeetingOut)
def create_meeting(payload: schemas.MeetingCreate, db: Session = Depends(get_db)):
    return _create_meeting_with_items(db, payload.title, payload.transcript)


@app.post("/meetings/upload-audio", response_model=schemas.MeetingOut)
def upload_meeting_audio(title: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    suffix = Path(file.filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file.file.read())
        tmp_path = Path(tmp.name)

    try:
        transcript = transcribe(str(tmp_path))
    finally:
        tmp_path.unlink(missing_ok=True)

    return _create_meeting_with_items(db, title, transcript)


@app.get("/meetings", response_model=list[schemas.MeetingOut])
def list_meetings(db: Session = Depends(get_db)):
    return db.query(models.Meeting).order_by(models.Meeting.id.desc()).all()


@app.get("/meetings/{meeting_id}", response_model=schemas.MeetingOut)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.get(models.Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return meeting


@app.get("/action-items", response_model=list[schemas.ActionItemOut])
def list_action_items(status: Optional[models.ActionItemStatus] = None, db: Session = Depends(get_db)):
    query = db.query(models.ActionItem)
    if status:
        query = query.filter(models.ActionItem.status == status)
    return query.all()


@app.patch("/action-items/{item_id}", response_model=schemas.ActionItemOut)
def review_action_item(item_id: int, payload: schemas.ActionItemReview, db: Session = Depends(get_db)):
    item = db.get(models.ActionItem, item_id)
    if not item:
        raise HTTPException(404, "Action item not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@app.post("/initiatives", response_model=schemas.InitiativeOut)
def create_initiative(payload: schemas.InitiativeCreate, db: Session = Depends(get_db)):
    initiative = models.Initiative(**payload.model_dump())
    db.add(initiative)
    db.commit()
    db.refresh(initiative)
    return initiative


@app.get("/initiatives", response_model=list[schemas.InitiativeDashboard])
def list_initiatives(db: Session = Depends(get_db)):
    dashboard = []
    for initiative in db.query(models.Initiative).all():
        items = initiative.action_items
        dashboard.append(
            schemas.InitiativeDashboard(
                **schemas.InitiativeOut.model_validate(initiative).model_dump(),
                total_items=len(items),
                done_items=sum(1 for i in items if i.status == models.ActionItemStatus.done),
                overdue_items=sum(1 for i in items if i.is_overdue),
            )
        )
    return dashboard


@app.post("/reports/weekly/generate")
def generate_weekly_report(db: Session = Depends(get_db)):
    path = save_weekly_report(db)
    return {"path": str(path)}


@app.get("/reports/weekly/preview")
def preview_weekly_report(db: Session = Depends(get_db)):
    return {"report": build_weekly_report(db)}
