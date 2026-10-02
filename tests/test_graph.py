from app.graph import _normalize


def test_normalize_filters_and_defaults():
    state = {
        "transcript": "",
        "raw_items": [
            {"description": "Ship the report", "owner": "Sam", "deadline": "2026-01-01", "priority": "high"},
            {"description": "", "owner": "ignored"},
            {"description": "Bad deadline task", "deadline": "not-a-date"},
            {"description": "Unknown priority", "priority": "urgent"},
        ],
        "items": [],
    }
    result = _normalize(state)["items"]

    assert len(result) == 3
    assert result[0]["owner"] == "Sam"
    assert result[1]["deadline"] is None
    assert result[2]["priority"] == "medium"


if __name__ == "__main__":
    test_normalize_filters_and_defaults()
    print("ok")
