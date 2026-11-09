
import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent

SOURCE_FILE = BASE_DIR / "catalog_upgraded.json"
OUTPUT_FILE = BASE_DIR / "catalog_repaired_test.json"


def clean_tags(tags):
    """Clean fragments created by the previous comma-splitting bug."""

    if not isinstance(tags, list):
        return []

    cleaned = []

    for tag in tags:
        tag = str(tag).strip()

        if not tag or tag == "[]":
            continue

        # Remove serialization fragments, not internal punctuation.
        tag = tag.strip("[]'\" ").strip()

        if tag and tag not in cleaned:
            cleaned.append(tag)

    return cleaned


def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(SOURCE_FILE)

    with open(SOURCE_FILE, "r", encoding="utf-8") as file:
        catalog = json.load(file)

    if not isinstance(catalog, list):
        raise ValueError("Catalogue must be a list.")

    if len(catalog) != 500:
        raise ValueError(
            f"Expected 500 tracks, found {len(catalog)}."
        )

    original_ids = [track.get("id") for track in catalog]

    if None in original_ids:
        raise ValueError("A track is missing its ID.")

    if len(original_ids) != len(set(original_ids)):
        raise ValueError("Duplicate IDs in source catalogue.")

    repaired = []

    for track in catalog:
        updated_track = dict(track)

        updated_track["tags"] = clean_tags(
            track.get("tags", [])
        )

        repaired.append(updated_track)

    repaired_ids = [track.get("id") for track in repaired]

    if repaired_ids != original_ids:
        raise ValueError("Track IDs or their order changed.")

    tag_counts = Counter(
        track["inference_method"]
        for track in repaired
        if "inference_method" in track
    )

    tracks_with_tags = sum(
        bool(track.get("tags"))
        for track in repaired
    )

    total_tags = sum(
        len(track.get("tags", []))
        for track in repaired
    )

    suspicious = [
        tag
        for track in repaired
        for tag in track.get("tags", [])
        if tag.startswith("[") or tag.endswith("]")
    ]

    # Write only to a separate test file.
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            repaired,
            file,
            indent=2,
            ensure_ascii=False
        )

    # Verify the saved file.
    with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
        saved = json.load(file)

    assert len(saved) == 500
    assert [t["id"] for t in saved] == original_ids
    assert not suspicious

    print("\nSONORA CATALOGUE REPAIR TEST")
    print("--------------------------------")
    print("Original tracks:", len(catalog))
    print("Repaired tracks:", len(saved))
    print("Unique IDs:", len(set(repaired_ids)))
    print("Tracks with tags:", tracks_with_tags)
    print("Total clean tags:", total_tags)
    print("Suspicious fragments:", len(suspicious))
    print("Inference methods:", dict(tag_counts))
    print("Output:", OUTPUT_FILE)

    print("\nFIRST 5 REPAIRED TAG SAMPLES:")

    for track in saved:
        if track.get("tags"):
            print(
                track.get("title"),
                "->",
                track["tags"]
            )

            if sum(1 for t in saved[:saved.index(track) + 1] if t.get("tags")) >= 5:
                break


if __name__ == "__main__":
    main()
