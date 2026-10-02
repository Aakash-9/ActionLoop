from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from .config import settings
from .models import ActionItem, ActionItemStatus, Initiative


def _initiative_section(name: str, items: list[ActionItem]) -> str:
    done = sum(1 for i in items if i.status == ActionItemStatus.done)
    overdue = [i for i in items if i.is_overdue]

    lines = [
        f"## {name}",
        f"- Total action items: {len(items)}",
        f"- Completed: {done}",
        f"- Overdue: {len(overdue)}",
    ]
    if overdue:
        lines.append("\n**Overdue items:**")
        for item in overdue:
            lines.append(f"- {item.description} (owner: {item.owner or 'unassigned'}, due {item.deadline})")
    return "\n".join(lines)


def build_weekly_report(db: Session) -> str:
    initiatives = db.query(Initiative).all()
    sections = [f"# Weekly Status Report — {date.today().isoformat()}"]

    for initiative in initiatives:
        sections.append(_initiative_section(initiative.name, initiative.action_items))

    unassigned = db.query(ActionItem).filter(ActionItem.initiative_id.is_(None)).all()
    if unassigned:
        sections.append(_initiative_section("Unassigned", unassigned))

    return "\n\n".join(sections)


def save_weekly_report(db: Session) -> Path:
    report = build_weekly_report(db)
    reports_dir = Path(settings.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"weekly-{date.today().isoformat()}.md"
    path.write_text(report, encoding="utf-8")
    return path
