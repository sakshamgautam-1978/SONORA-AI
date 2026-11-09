
import ast
import csv
import json
import re
from pathlib import Path

# Safe additive enrichment: writes catalog_upgraded.json only.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datasets" / "fma_metadata"
CATALOG_FILE = BASE_DIR / "catalog.json"
TRACKS_FILE = DATA_DIR / "tracks.csv"
GENRES_FILE = DATA_DIR / "genres.csv"
OUTPUT_FILE = BASE_DIR / "catalog_upgraded.json"

LANGUAGE_NAMES = {
    "ar": "Arabic", "de": "German", "en": "English", "es": "Spanish",
    "fr": "French", "hi": "Hindi", "it": "Italian", "ja": "Japanese",
    "ko": "Korean", "nl": "Dutch", "pt": "Portuguese", "ru": "Russian",
    "sw": "Swahili", "zh": "Chinese",
}


def clean(value):
    return "" if value is None else str(value).strip()


def parse_id_list(value):
    value = clean(value)
    if not value:
        return []
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, (list, tuple, set)):
            return [str(x).strip() for x in parsed if str(x).strip()]
        if isinstance(parsed, (int, float)):
            return [str(parsed)]
    except (ValueError, SyntaxError):
        pass
    return re.findall(r"\d+", value)


def read_genres():
    with open(GENRES_FILE, encoding="utf-8", newline="") as f:
        rows = csv.DictReader(f)
        result = {}
        for row in rows:
            gid = clean(row.get("genre_id"))
            if gid:
                result[gid] = {
                    "genre_id": gid,
                    "title": clean(row.get("title")) or "Unknown",
                    "parent_id": clean(row.get("parent")) or None,
                    "top_level_id": clean(row.get("top_level")) or None,
                }
    return result


def read_fma_rows():
    records = {}
    with open(TRACKS_FILE, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        first = next(reader, None)
        second = next(reader, None)
        index_row = next(reader, None)

        if first is None or second is None or index_row is None:
            raise ValueError("Unexpected FMA tracks.csv header structure.")

        columns = []
        for a, b in zip(first, second):
            a, b = clean(a), clean(b)
            columns.append(
                f"{a}.{b}" if a and b else (a or b or "track_id")
            )
        columns[0] = "track_id"

        for row in reader:
            if not row:
                continue

            data = {
                columns[i]: row[i] if i < len(row) else ""
                for i in range(len(columns))
            }

            track_id = clean(data.get("track_id"))
            if track_id:
                records[track_id] = data

    return records


def resolve_genres(ids, genre_map):
    names, hierarchy = [], []

    for gid in ids:
        item = genre_map.get(str(gid))
        if not item:
            continue

        names.append(item["title"])

        parent_id = item["parent_id"]
        top_id = item["top_level_id"]

        parent = (
            genre_map.get(parent_id)
            if parent_id and parent_id != "0"
            else None
        )
        top = genre_map.get(top_id) if top_id else None

        hierarchy.append({
            "genre_id": item["genre_id"],
            "name": item["title"],
            "parent_id": parent_id,
            "parent_name": parent["title"] if parent else None,
            "top_level_id": top_id,
            "top_level_name": top["title"] if top else item["title"],
        })

    return names, hierarchy


def enrich_track(track, fma_records, genre_map):
    # Keep the six original tracks exactly unchanged.
    if not str(track.get("id", "")).startswith("fma_"):
        return track

    source_id = clean(
        track.get("source_track_id")
        or str(track.get("id", ""))[4:]
    )

    row = fma_records.get(source_id)

    if not row:
        track["enrichment_status"] = "no_exact_fma_match"
        return track

    genre_ids = parse_id_list(row.get("track.genres"))
    all_ids = parse_id_list(row.get("track.genres_all"))

    genre_names, hierarchy = resolve_genres(genre_ids, genre_map)
    all_names, all_hierarchy = resolve_genres(all_ids, genre_map)

    language_code = clean(
        row.get("track.language_code")
    ).lower()

    track.update({
        "fma_genre_ids": genre_ids,
        "genres": genre_names,
        "fma_genres_all_ids": all_ids,
        "genres_all": all_names,
        "genre_hierarchy": hierarchy,
        "genre_hierarchy_all": all_hierarchy,

        "album_title": clean(row.get("album.title")) or None,
        "artist_id": clean(row.get("artist.id")) or None,

        "language_code": language_code or None,
        "language_name": LANGUAGE_NAMES.get(
            language_code, "Unknown"
        ),

        "publisher": clean(row.get("track.publisher")) or None,
        "lyricist": clean(row.get("track.lyricist")) or None,
        "track_information": clean(
            row.get("track.information")
        ) or None,

        "fma_interest": clean(row.get("track.interest")) or None,
        "album_track_number": clean(
            row.get("track.number")
        ) or None,

        "enrichment_source": "FMA tracks.csv and genres.csv",
        "enrichment_status": "matched",
    })

    return track


def main():
    for required in (
        CATALOG_FILE,
        TRACKS_FILE,
        GENRES_FILE
    ):
        if not required.exists():
            raise FileNotFoundError(
                f"Required file not found: {required}"
            )

    with open(CATALOG_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    if not isinstance(catalog, list):
        raise ValueError(
            "catalog.json must contain a JSON list."
        )

    original_ids = [x.get("id") for x in catalog]

    if len(original_ids) != len(set(original_ids)):
        raise ValueError(
            "Original catalogue contains duplicate IDs."
        )

    original_tracks = [
        x for x in catalog
        if not str(x.get("id", "")).startswith("fma_")
    ]

    fma_tracks = [
        x for x in catalog
        if str(x.get("id", "")).startswith("fma_")
    ]

    print(f"Loaded tracks: {len(catalog)}")
    print(f"Original/non-FMA tracks: {len(original_tracks)}")
    print(f"FMA tracks: {len(fma_tracks)}")

    genre_map = read_genres()
    fma_records = read_fma_rows()

    print(f"Genre definitions: {len(genre_map)}")
    print(f"FMA metadata records: {len(fma_records)}")

    upgraded = [
        enrich_track(dict(track), fma_records, genre_map)
        for track in catalog
    ]

    upgraded_ids = [x.get("id") for x in upgraded]

    if len(upgraded) != len(catalog):
        raise ValueError("Track count changed.")

    if upgraded_ids != original_ids:
        raise ValueError("Track IDs or ordering changed.")

    if len(upgraded_ids) != len(set(upgraded_ids)):
        raise ValueError("Duplicate IDs detected.")

    by_id = {x["id"]: x for x in upgraded}

    for track in original_tracks:
        if by_id[track["id"]] != track:
            raise ValueError(
                f"Original track unexpectedly changed: {track['id']}"
            )

    matched = sum(
        x.get("enrichment_status") == "matched"
        for x in upgraded
    )

    unmatched = sum(
        x.get("enrichment_status") == "no_exact_fma_match"
        for x in upgraded
    )

    temp = OUTPUT_FILE.with_suffix(".tmp")

    with open(temp, "w", encoding="utf-8") as f:
        json.dump(
            upgraded,
            f,
            indent=2,
            ensure_ascii=False
        )
        f.write("\n")

    temp.replace(OUTPUT_FILE)

    with open(OUTPUT_FILE, encoding="utf-8") as f:
        verified = json.load(f)

    if len(verified) != len(catalog):
        raise ValueError("Output verification failed.")

    print("\nCATALOG ENRICHMENT COMPLETE")
    print("--------------------------------")
    print(f"Original tracks preserved: {len(original_tracks)}")
    print(f"FMA tracks: {len(fma_tracks)}")
    print(f"Matched FMA records: {matched}")
    print(f"Unmatched FMA records: {unmatched}")
    print(f"Total tracks: {len(verified)}")
    print(
        f"Unique IDs: {len(set(x['id'] for x in verified))}"
    )
    print(f"Output: {OUTPUT_FILE}")
    print("Original catalog.json was NOT modified.")


if __name__ == "__main__":
    main()
