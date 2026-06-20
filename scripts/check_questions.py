import json
from pathlib import Path


def main() -> None:
    path = Path("data/questions.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = [item["id"] for item in data]
    assert len(ids) == len(set(ids)), "question ids must be unique"
    assert data, "question bank cannot be empty"
    for item in data:
        assert item["kind"] in {"single", "multiple"}, item["id"]
        assert item["answers"], item["id"]
        assert all(0 <= idx < len(item["options"]) for idx in item["answers"]), item["id"]
        if item["kind"] == "single":
            assert len(item["answers"]) == 1, item["id"]
        assert len(item["options"]) >= 4, item["id"]
    print(f"OK: {len(data)} questions")


if __name__ == "__main__":
    main()
