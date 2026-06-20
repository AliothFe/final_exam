import json
from pathlib import Path


def main() -> None:
    path = Path("data/questions.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = [item["id"] for item in data]
    assert len(ids) == len(set(ids)), "question ids must be unique"
    assert data, "question bank cannot be empty"
    chapters = {item.get("chapter") for item in data}
    assert len(chapters) >= 14, "v3 question bank should cover PDF chapters plus current affairs"
    assert "14 时事政治" in chapters, "current affairs chapter is required"
    assert len(data) >= 190, "v3 should include the 90-question current affairs markdown"
    kinds = {item["kind"] for item in data}
    assert {"single", "multiple", "blank"}.issubset(kinds), "single/multiple/blank are all required"
    for item in data:
        assert item.get("chapter"), item["id"]
        assert item.get("topic"), item["id"]
        assert item["kind"] in {"single", "multiple", "blank"}, item["id"]
        assert item.get("question"), item["id"]
        assert item.get("explanation"), item["id"]
        if item["kind"] in {"single", "multiple"}:
            assert item.get("options"), item["id"]
            assert item.get("answers") is not None, item["id"]
            assert all(0 <= idx < len(item["options"]) for idx in item["answers"]), item["id"]
            if item["kind"] == "single":
                assert len(item["answers"]) == 1, item["id"]
            assert len(item["options"]) >= 4, item["id"]
        else:
            assert item.get("blanks"), item["id"]
            assert all(blank.strip() for blank in item["blanks"]), item["id"]
    print(f"OK: {len(data)} questions, {len(chapters)} chapters, kinds={sorted(kinds)}")


if __name__ == "__main__":
    main()
