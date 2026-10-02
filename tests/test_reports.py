from datetime import date, timedelta

from app.models import ActionItem, ActionItemStatus


def test_is_overdue():
    overdue = ActionItem(deadline=date.today() - timedelta(days=1), status=ActionItemStatus.approved)
    assert overdue.is_overdue is True

    done = ActionItem(deadline=date.today() - timedelta(days=1), status=ActionItemStatus.done)
    assert done.is_overdue is False

    future = ActionItem(deadline=date.today() + timedelta(days=1), status=ActionItemStatus.approved)
    assert future.is_overdue is False

    no_deadline = ActionItem(deadline=None, status=ActionItemStatus.approved)
    assert no_deadline.is_overdue is False


if __name__ == "__main__":
    test_is_overdue()
    print("ok")
