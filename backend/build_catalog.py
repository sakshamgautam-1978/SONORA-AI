
import csv
import json
import random
from pathlib import Path
from collections import defaultdict

# -----------------------------------------
# SONORA AI - FMA CATALOG BUILDER
# -----------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datasets" / "fma_metadata"

TRACKS_FILE = DATA_DIR / "tracks.csv"
OUTPUT_FILE = BASE_DIR / "catalog.json"

TARGET_TOTAL = 500
ORIGINAL_TRACKS = 6
FMA_TARGET = TARGET_TOTAL - ORIGINAL_TRACKS

RANDOM_SEED = 42

# -----------------------------------------
# ORIGINAL SIX TRACKS
# -----------------------------------------

def load_original_tracks():
    with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
        tracks = json.load(file)

    if len(tracks) != ORIGINAL_TRACKS:
        raise ValueError(
            f"Expected {ORIGINAL_TRACKS} original tracks, "
            f"but found {len(tracks)}. "
            "Restore your original six-track catalog.json first."
        )

    return tracks


# -----------------------------------------
# METADATA HELPERS
# -----------------------------------------

def clean(value):
    if value is None:
        return ""

    return str(value).strip()


def parse_year(value):
    value = clean(value)

    if len(value) >= 4 and value[:4].isdigit():
        year = int(value[:4])

        if 1900 <= year <= 2035:
            return year

    return None


def infer_metadata(genre, title, tags):
    """
    These are heuristic labels inferred from metadata.
    They are NOT original FMA mood annotations.
    """

    text = f"{genre} {title} {tags}".lower()

    rules = [
        (
            ["ambient", "drone", "meditation"],
            ["calm", "peaceful", "dreamy"],
            ["study", "meditation", "relaxation"],
            0.15
        ),
        (
            ["classical", "piano", "orchestral"],
            ["emotional", "reflective", "inspiring"],
            ["study", "reading", "relaxation"],
            0.35
        ),
        (
            ["electronic", "dance", "techno", "house"],
            ["energetic", "uplifting", "exciting"],
            ["workout", "walking", "travel"],
            0.75
        ),
        (
            ["jazz", "blues", "soul"],
            ["smooth", "relaxed", "reflective"],
            ["relaxation", "reading", "travel"],
            0.45
        ),
        (
            ["rock", "metal", "punk"],
            ["intense", "energetic", "powerful"],
            ["workout", "walking", "focus"],
            0.80
        ),
        (
            ["folk", "country", "acoustic"],
            ["warm", "peaceful", "nostalgic"],
            ["walking", "reading", "relaxation"],
            0.40
        ),
        (
            ["hip-hop", "hip hop", "rap"],
            ["confident", "energetic", "expressive"],
            ["workout", "walking", "focus"],
            0.70
        )
    ]

    for keywords, moods, activities, energy in rules:
        if any(keyword in text for keyword in keywords):
            return {
                "mood": moods,
                "activities": activities,
                "energy": energy,
                "label_source": "heuristic_from_genre_and_metadata"
            }

    return {
        "mood": ["varied", "expressive"],
        "activities": ["general_listening"],
        "energy": 0.5,
        "label_source": "generic_fallback"
    }


def make_fma_track(row, columns):
    data = dict(zip(columns, row))

    track_id = clean(data.get("track_id"))
    title = clean(data.get("track.title"))
    artist = clean(data.get("artist.name"))
    genre = clean(data.get("track.genre_top"))

    if not track_id or not title or not artist or not genre:
        return None

    if genre.lower() in ["none", "nan", "unknown"]:
        return None

    duration = clean(data.get("track.duration"))
    year = parse_year(data.get("album.date_released"))

    tags = clean(data.get("track.tags"))
    if not tags:
        tags = clean(data.get("album.tags"))

    inferred = infer_metadata(genre, title, tags)

    # Keep the actual dataset fields separate from inferred fields.
    return {
        "id": f"fma_{track_id}",
        "source": "Free Music Archive",
        "source_track_id": track_id,
        "title": title,
        "artist": artist,
        "genre": genre,
        "mood": inferred["mood"],
        "activities": inferred["activities"],
        "energy": inferred["energy"],
        "familiarity": 0.0,
        "language": clean(data.get("track.language_code")) or "Unknown",
        "tags": [
            item.strip()
            for item in tags.split(",")
            if item.strip()
        ][:10],
        "duration": duration or "Unknown",
        "year": year,
        "metadata_source": "FMA",
        "inference_method": inferred["label_source"],
        "mood_is_inferred": True,
        "license": clean(data.get("track.license")) or "Check source",
        "attribution": "Metadata from the Free Music Archive (FMA) dataset, CC BY 4.0"
    }


# -----------------------------------------
# READ FMA MULTI-ROW CSV HEADER
# -----------------------------------------

def read_fma_tracks():
    print("Reading FMA metadata...")

    candidates_by_genre = defaultdict(list)
    seen_ids = set()

    with open(
        TRACKS_FILE,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.reader(file)

        first_header = next(reader)
        second_header = next(reader)

        # FMA exports a separate index-name row after its two
        # MultiIndex header rows. Skip that row.
        index_row = next(reader)

        columns = []

        for first, second in zip(first_header, second_header):
            first = clean(first)
            second = clean(second)

            if not first and not second:
                columns.append("track_id")
            elif first and second:
                columns.append(f"{first}.{second}")
            else:
                columns.append(first or second)

        # Track IDs are stored in the first column.
        columns[0] = "track_id"

        processed = 0

        for row in reader:
            if not row:
                continue

            processed += 1

            track = make_fma_track(row, columns)

            if track is None:
                continue

            if track["source_track_id"] in seen_ids:
                continue

            seen_ids.add(track["source_track_id"])

            candidates_by_genre[track["genre"]].append(track)

            if processed % 10000 == 0:
                print(f"Processed {processed} rows...")

    print(f"Valid FMA records: {sum(map(len, candidates_by_genre.values()))}")
    print(f"Available genres: {len(candidates_by_genre)}")

    return candidates_by_genre


# -----------------------------------------
# BALANCED TRACK SELECTION
# -----------------------------------------

def select_tracks(candidates_by_genre, target):
    random.seed(RANDOM_SEED)

    genres = sorted(candidates_by_genre.keys())

    for genre in genres:
        random.shuffle(candidates_by_genre[genre])

    selected = []

    # Round-robin selection helps avoid filling the catalog
    # with only the largest genres.
    while len(selected) < target:
        added_this_round = False

        for genre in genres:
            if candidates_by_genre[genre]:
                selected.append(
                    candidates_by_genre[genre].pop()
                )
                added_this_round = True

                if len(selected) == target:
                    break

        if not added_this_round:
            break

    return selected


# -----------------------------------------
# VALIDATE AND BUILD CATALOG
# -----------------------------------------

def main():
    if not TRACKS_FILE.exists():
        raise FileNotFoundError(
            f"Cannot find FMA tracks file: {TRACKS_FILE}"
        )

    original_tracks = load_original_tracks()

    print(f"Preserving {len(original_tracks)} original tracks.")

    candidates = read_fma_tracks()

    selected = select_tracks(
        candidates,
        FMA_TARGET
    )

    if len(selected) < FMA_TARGET:
        raise ValueError(
            f"Only {len(selected)} usable FMA records found. "
            f"Need {FMA_TARGET}. Catalog was not modified."
        )

    final_catalog = original_tracks + selected

    ids = [track["id"] for track in final_catalog]

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate track IDs detected.")

    if len(final_catalog) != TARGET_TOTAL:
        raise ValueError("Final catalog size is incorrect.")

    # Save only after all validation succeeds.
    temp_file = OUTPUT_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(
            final_catalog,
            file,
            indent=2,
            ensure_ascii=False
        )

    temp_file.replace(OUTPUT_FILE)

    print("\nSONORA AI CATALOG BUILD COMPLETE")
    print("--------------------------------")
    print(f"Original tracks: {len(original_tracks)}")
    print(f"FMA tracks: {len(selected)}")
    print(f"Total tracks: {len(final_catalog)}")
    print(f"Unique IDs: {len(set(ids))}")
    print(f"Output: {OUTPUT_FILE}")

    print("\nGenre distribution:")

    distribution = defaultdict(int)

    for track in selected:
        distribution[track["genre"]] += 1

    for genre, count in sorted(
        distribution.items(),
        key=lambda item: item[1],
        reverse=True
    ):
        print(f"{genre}: {count}")


if __name__ == "__main__":
    main()