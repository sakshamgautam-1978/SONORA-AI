"""
SONORA AI recommendation engine.

Uses TF-IDF metadata similarity, intent detection, preference feedback,
familiarity/novelty weighting, and Maximal Marginal Relevance (MMR).

Important:
- Metadata-based recommender, not a neural embedding model.
- semanticId is a deterministic SHA-256 metadata identifier.
- Mood/activity/energy values depend on catalogue metadata.
"""

import hashlib
import json
import re
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from semantic_engine import SemanticEmbeddingIndex

# ============================================================
# 1. LOAD CATALOGUE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
# Prefer the validated enriched catalogue when available.
# Fall back to the original catalogue before enrichment is available.
ENRICHED_CATALOG_PATH = BASE_DIR / "catalog_upgraded.json"
ORIGINAL_CATALOG_PATH = BASE_DIR / "catalog.json"
CATALOG_PATH = (
    ENRICHED_CATALOG_PATH
    if ENRICHED_CATALOG_PATH.exists()
    else ORIGINAL_CATALOG_PATH
)

with CATALOG_PATH.open("r", encoding="utf-8") as file:
    CATALOG_DATA = json.load(file)

if isinstance(CATALOG_DATA, dict):
    CATALOG = CATALOG_DATA.get("tracks", [])
else:
    CATALOG = CATALOG_DATA

if not isinstance(CATALOG, list) or not CATALOG:
    raise ValueError("catalog.json must contain a non-empty list of tracks.")


# ============================================================
# 2. QUERY INTENT DICTIONARIES
# ============================================================



    
    
INTENT_MAP = {
    "calm": [
        "calm",
        "peaceful",
        "relaxing",
        "relaxed",
        "relax",
        "quiet",
        "soothing",
        "chill",
        "serene",
        "smooth"
    ],

    "energetic": [
        "energetic",
        "energy",
        "exciting",
        "high energy",
        "hype",
        "intense",
        "powerful"
    ],

    "happy": [
        "happy",
        "joyful",
        "cheerful",
        "uplifting",
        "positive",
        "feel good",
        "warm"
    ],

    
    
    "emotional": [
    "emotional", "sad", "melancholic", "heartbroken"
],

"nostalgic": [
    "nostalgic", "nostalgia", "reminiscent"
],

    "dreamy": [
        "dreamy",
        "ethereal",
        "floating",
        "atmospheric",
        "spacey",
        "mysterious"
    ],

    "focus": [
        "focus",
        "concentration",
        "deep work",
        "productive"
    ],

    "romantic": [
        "romantic",
        "love",
        "intimate",
        "date night",
        "warm",
        "tender"
    ],

    "aggressive": [
        "aggressive",
        "hardcore",
        "heavy",
        "powerful",
        "intense"
    ]
}

 



ACTIVITY_MAP = {
    "study": [
        "study",
        "studying",
        "reading",
        "homework",
        "coding",
        "deep work",
        "focus",
        "concentration"
    ],

    "sleep": [
        "sleep",
        "sleeping",
        "bedtime",
        "insomnia",
        "night"
    ],

    "walking": [
        "walking",
        "walk",
        "strolling"
    ],

    "meditation": [
        "meditation",
        "meditating",
        "mindfulness"
    ],

    "workout": [
        "workout",
        "gym",
        "exercise",
        "running",
        "training"
    ],

    "travel": [
        "travel",
        "road trip",
        "driving",
        "journey"
    ],

    "relaxation": [
        "relaxation",
        "unwind",
        "rest",
        "relax",
        "relaxing",
        "relaxed",
        "soothing"
    ]
}


GENRE_MAP = {
    "classical": ["classical", "orchestral", "symphony"],
    "electronic": ["electronic", "edm", "techno", "house", "trance"],
    "ambient": ["ambient", "soundscape", "atmospheric"],
    "jazz": ["jazz", "smooth jazz", "bebop"],
    "blues": ["blues"],
    "rock": ["rock", "punk", "metal", "alternative rock"],
    "pop": ["pop music", "pop"],
    "hip-hop": ["hip-hop", "hip hop", "hiphop", "rap"],
    "folk": ["folk", "acoustic folk"],
    "country": ["country"],
    "experimental": ["experimental", "avant garde", "avant-garde"],
    "soul-rnb": ["soul-rnb", "soul rnb", "soul", "rnb", "r&b"],
}

LANGUAGE_MAP = {
    "Arabic": ["arabic", "in arabic"],
    "Chinese": ["chinese", "mandarin"],
    "Dutch": ["dutch"],
    "English": ["english", "in english"],
    "French": ["french", "in french"],
    "German": ["german", "in german"],
    "Hindi": ["hindi", "in hindi"],
    "Italian": ["italian", "in italian"],
    "Japanese": ["japanese", "in japanese"],
    "Korean": ["korean", "in korean"],
    "Portuguese": ["portuguese", "in portuguese"],
    "Russian": ["russian", "in russian"],
    "Spanish": ["spanish", "in spanish"],
    "Swahili": ["swahili"],
}


# ============================================================
# 3. GENERAL HELPERS
# ============================================================

def safe_text(value):
    """Convert nested metadata values into searchable text."""

    if value is None:
        return ""

    if isinstance(value, dict):
        return " ".join(safe_text(v) for v in value.values())

    if isinstance(value, (list, tuple, set)):
        return " ".join(safe_text(v) for v in value)

    return str(value)


def normalize_words(value):
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        safe_text(value).lower()
    ).strip()


def contains_phrase(text, phrase):
    """Whole-phrase matching to avoid accidental substring matches."""

    text = normalize_words(text)
    phrase = normalize_words(phrase)

    if not text or not phrase:
        return False

    pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"

    return re.search(pattern, text) is not None


def detect_categories(query, mapping):
    text = str(query).lower()

    return [
        category
        for category, keywords in mapping.items()
        if any(
            contains_phrase(text, word)
            for word in keywords
        )
    ]


def get_track_id(track):
    return str(
        track.get("id")
        or track.get("track_id")
        or track.get("trackId")
        or ""
    )


def get_track_genre_list(track):
    """Return unique genre labels from original and enriched fields."""
    values = []

    for field in ("genre", "genre_top", "genres", "genres_all"):
        values.extend(get_list(track.get(field)))

    hierarchy = track.get("genre_hierarchy_all", [])
    if isinstance(hierarchy, list):
        for item in hierarchy:
            if isinstance(item, dict):
                name = safe_text(item.get("name", "")).strip().lower()
                if name:
                    values.append(name)

    unique = []
    seen = set()
    for value in values:
        normalized = normalize_words(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(value)

    return unique


def get_track_genres(track):
    """Return all searchable genre labels as one text string."""
    return " ".join(get_track_genre_list(track))


def get_list(value):
    if value is None:
        return []

    values = value if isinstance(value, list) else [value]
    cleaned = []

    for item in values:
        text = safe_text(item).strip().lower()
        text = text.strip(" \t\r\n[]{}'\"")

        if text:
            cleaned.append(text)

    return cleaned


def clamp(value, minimum=0.0, maximum=1.0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return minimum

    return max(minimum, min(maximum, number))


# ============================================================
# 4. QUERY UNDERSTANDING
# ============================================================

def understand_query(query):
    text = str(query).lower()

    moods = detect_categories(text, INTENT_MAP)
    activities = detect_categories(text, ACTIVITY_MAP)
    genres = detect_categories(text, GENRE_MAP)
    languages = detect_categories(text, LANGUAGE_MAP)

    instrumental_phrases = [
        "instrumental",
        "no vocals",
        "without vocals",
        "no singing",
        "music without singing",
    ]

    instrumental = any(
        contains_phrase(text, phrase)
        for phrase in instrumental_phrases
    )

    high_energy = [
        "high energy",
        "energetic",
        "intense",
        "workout",
        "gym",
        "powerful",
    ]

    low_energy = [
        "calm",
        "quiet",
        "relaxing",
        "peaceful",
        "sleep",
        "soft",
    ]

    if any(
        contains_phrase(text, phrase)
        for phrase in high_energy
    ):
        energy = 0.85

    elif any(
        contains_phrase(text, phrase)
        for phrase in low_energy
    ):
        energy = 0.20

    else:
        energy = None

    late_night = any(
        contains_phrase(text, phrase)
        for phrase in [
            "late night",
            "3 am",
            "3 a.m.",
            "midnight",
            "at night",
            "night time",
        ]
    )

    unfamiliar = any(
        contains_phrase(text, phrase)
        for phrase in [
            "unfamiliar",
            "new music",
            "something new",
            "different music",
            "outside my taste",
            "discover something",
            "surprise me",
        ]
    )

    return {
        "moods": moods,
        "activities": activities,
        "genres": genres,
        "languages": languages,
        "instrumental": instrumental,
        "energy": energy,
        "late_night": late_night,
        "unfamiliar": unfamiliar,
    }


# ============================================================
# 5. TEXT REPRESENTATION AND TF-IDF
# ============================================================

def track_text(track):
    fields = [
        track.get("title", track.get("name", "")),
        track.get("artist", ""),
        get_track_genres(track),
        safe_text(track.get("genre_hierarchy_all", [])),
        safe_text(track.get("mood", [])),
        safe_text(track.get("activities", [])),
        safe_text(track.get("tags", [])),
        track.get("language", ""),
        track.get("language_name", ""),
        track.get("language_code", ""),
        track.get("album_title", ""),
        track.get("publisher", ""),
        track.get("lyricist", ""),
        track.get("track_information", ""),
        track.get("metadata_source", ""),
    ]

    return " ".join(
        str(value)
        for value in fields
        if value
    )


TRACK_TEXTS = [
    track_text(track)
    for track in CATALOG
]

VECTORIZER = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
    max_features=30000,
    sublinear_tf=True,
)

TRACK_MATRIX = VECTORIZER.fit_transform(TRACK_TEXTS)
# ============================================================
# PHASE 2: HYBRID SEMANTIC SEARCH ENGINE
# ============================================================

SEMANTIC_INDEX = SemanticEmbeddingIndex(TRACK_TEXTS)


def calculate_hybrid_similarity(query):
    """
    Combine TF-IDF and neural semantic similarity.

    When the embedding model is unavailable, use TF-IDF alone.
    """

    tfidf_scores = calculate_similarity(query)

    embedding_scores = SEMANTIC_INDEX.query_scores(query)

    if embedding_scores is None:
        return normalize_similarity(tfidf_scores), "tfidf"

    embedding_scores = np.asarray(
        embedding_scores,
        dtype=float
    )

    tfidf_scores = normalize_similarity(tfidf_scores)

    if embedding_scores.shape != tfidf_scores.shape:
        return tfidf_scores, "tfidf"

    hybrid_scores = (
        0.65 * embedding_scores
        + 0.35 * tfidf_scores
    )

    return normalize_similarity(hybrid_scores), "hybrid"


def calculate_similarity(query):
    query_vector = VECTORIZER.transform([str(query)])

    return cosine_similarity(
        query_vector,
        TRACK_MATRIX
    ).flatten()


def normalize_similarity(values):
    values = np.asarray(values, dtype=float)

    if values.size == 0:
        return values

    low = float(np.min(values))
    high = float(np.max(values))

    if high == low:
        return np.zeros_like(values)

    return (values - low) / (high - low)


# ============================================================
# 6. DETERMINISTIC METADATA ID
# ============================================================

def generate_semantic_id(track):
    metadata = "|".join([
        safe_text(track.get("title", "")),
        safe_text(track.get("artist", "")),
        get_track_genres(track),
    ])

    digest = hashlib.sha256(
        metadata.encode("utf-8")
    ).hexdigest()[:16]

    return "SON-" + digest.upper()


# ============================================================
# 7. FEATURE SCORING
# ============================================================



def get_mood_score(track, requested_moods):
    if not requested_moods:
        return 0.5

    # Generic fallback moods are unknown, not actual mismatches.
    if track.get("inference_method") == "generic_fallback":
        return 0.5

    track_moods = get_list(track.get("mood", []))

    if not track_moods:
        return 0.5

    matched = []

    for mood in requested_moods:
        synonyms = INTENT_MAP.get(mood, [mood])

        found = any(
            contains_phrase(track_mood, synonym)
            for track_mood in track_moods
            for synonym in synonyms
        )

        if found:
            matched.append(mood)

    return len(matched) / len(requested_moods)




def get_activity_score(track, requested_activities):
    if not requested_activities:
        return 0.5

    # Generic fallback activities are unknown, not mismatches.
    if track.get("inference_method") == "generic_fallback":
        return 0.5

    track_activities = get_list(track.get("activities", []))

    if not track_activities:
        return 0.5

    matched_activities = 0

    for activity in requested_activities:
        synonyms = ACTIVITY_MAP.get(activity, [activity])

        matched = any(
            contains_phrase(track_activity, synonym)
            or contains_phrase(synonym, track_activity)
            for track_activity in track_activities
            for synonym in synonyms
        )

        if matched:
            matched_activities += 1

    return matched_activities / len(requested_activities)


def get_genre_score(track, requested_genres):
    if not requested_genres:
        return 0.5

    # Preserve hyphens so power-pop is not mistaken for pop.
    track_genre_text = re.sub(
        r"[^a-z0-9-]+",
        " ",
        get_track_genres(track).lower()
    ).strip()

    matched = []

    for genre in requested_genres:
        synonyms = GENRE_MAP.get(genre, [genre])

        found = False

        for synonym in synonyms:
            normalized_synonym = re.sub(
                r"[^a-z0-9-]+",
                " ",
                synonym.lower()
            ).strip()

            pattern = (
                r"(?<![a-z0-9-])"
                + re.escape(normalized_synonym)
                + r"(?![a-z0-9-])"
            )

            if re.search(pattern, track_genre_text):
                found = True
                break

        if found:
            matched.append(genre)

    return len(matched) / len(requested_genres)

def get_language_score(track, requested_languages):
    """
    Match requested language against catalogue language metadata.
    Unknown/missing language remains neutral instead of being penalized.
    """
    if not requested_languages:
        return 0.5

    code = safe_text(track.get("language_code", "")).strip().lower()
    name = safe_text(track.get("language_name", "")).strip().lower()
    legacy = safe_text(track.get("language", "")).strip().lower()
    known_values = {value for value in (code, name, legacy) if value}

    if not known_values or "unknown" in known_values:
        return 0.5

    codes = {
        "arabic": "ar", "chinese": "zh", "dutch": "nl",
        "english": "en", "french": "fr", "german": "de",
        "hindi": "hi", "italian": "it", "japanese": "ja",
        "korean": "ko", "portuguese": "pt", "russian": "ru",
        "spanish": "es", "swahili": "sw",
    }

    for requested in requested_languages:
        requested = requested.lower()
        requested_code = codes.get(requested, "")
        if requested in known_values or (
            requested_code and requested_code in known_values
        ):
            return 1.0

    return 0.0


def get_instrumental_score(track):
    explicit = track.get("is_instrumental")

    if isinstance(explicit, bool):
        return 1.0 if explicit else 0.0

    vocal_status = safe_text(
        track.get("vocal_status", "")
    ).lower()

    if vocal_status in ("instrumental", "no vocals"):
        return 1.0

    if vocal_status in ("vocal", "vocals", "with vocals"):
        return 0.0

    tags = get_list(track.get("tags", []))
    title = safe_text(track.get("title", "")).lower()
    language = safe_text(track.get("language", "")).lower()

    if "instrumental" in tags or "instrumental" in title:
        return 1.0

    if language == "instrumental":
        return 0.9

    return 0.35


def get_familiarity_score(track):
    value = track.get("familiarity")

    if value is not None:
        return clamp(value)

    return 0.5


def get_novelty_score(track):
    value = track.get("novelty")

    if value is not None:
        return clamp(value)

    return 1.0 - get_familiarity_score(track)


def get_user_preference(track_id, user_preferences):
    value = user_preferences.get(track_id, 0.0)

    if isinstance(value, dict):
        likes = float(value.get("likes", 0) or 0)
        dislikes = float(value.get("dislikes", 0) or 0)
        saves = float(value.get("saves", 0) or 0)

        value = likes - dislikes + (0.7 * saves)

    try:
        return max(-1.0, min(1.0, float(value)))

    except (TypeError, ValueError):
        return 0.0
        # ============================================================
# 8. USER TASTE PROFILE
# ============================================================



def build_user_taste_profile(user_preferences):
    """
    Learn genre, mood and activity preferences from rated tracks.

    Generic fallback mood/activity labels are excluded because
    they do not represent reliable information about a track.
    """

    profile = {
        "genres": {},
        "moods": {},
        "activities": {},
        "rated_tracks": set(),
    }

    if not user_preferences:
        return profile

    track_lookup = {
        get_track_id(track): track
        for track in CATALOG
        if get_track_id(track)
    }

    for track_id, raw_score in user_preferences.items():

        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            continue

        score = max(-1.0, min(1.0, score))

        if score == 0:
            continue

        track = track_lookup.get(str(track_id))

        if not track:
            continue

        profile["rated_tracks"].add(str(track_id))

        # Genre remains usable even when mood/activity are unknown.
        genres = get_track_genre_list(track)

        for genre in genres:
            profile["genres"][genre] = (
                profile["genres"].get(genre, 0.0) + score
            )

        # Do not learn generic fallback labels.
        if track.get("inference_method") != "generic_fallback":

            moods = get_list(track.get("mood", []))
            activities = get_list(track.get("activities", []))

            for mood in moods:
                profile["moods"][mood] = (
                    profile["moods"].get(mood, 0.0) + score
                )

            for activity in activities:
                profile["activities"][activity] = (
                    profile["activities"].get(activity, 0.0) + score
                )

    # Normalize profile values.
    for category in ("genres", "moods", "activities"):

        values = profile[category]

        for key in values:
            values[key] = max(
                -1.0,
                min(1.0, values[key] / 3.0)
            )

    return profile




def calculate_profile_match(track, profile):
    """
    Calculate how closely a track matches the user's learned taste.
    """

    if not profile:
        return 0.0

    track_genres = get_track_genre_list(track)
    track_moods = get_list(track.get("mood", []))
    track_activities = get_list(track.get("activities", []))

    values = []

    for genre in track_genres:
        if genre in profile["genres"]:
            values.append(profile["genres"][genre])

    for mood in track_moods:
        if mood in profile["moods"]:
            values.append(profile["moods"][mood])

    for activity in track_activities:
        if activity in profile["activities"]:
            values.append(profile["activities"][activity])

    if not values:
        return 0.0

    return max(-1.0, min(1.0, sum(values) / len(values)))


# ============================================================
# 9. PERSONALIZED FAMILIARITY AND NOVELTY
# ============================================================

def calculate_personal_familiarity(track, profile):
    """
    Estimate familiarity using actual user feedback.

    This is a taste-affinity estimate, not proof that the
    user has listened to the track.
    """

    track_id = get_track_id(track)

    if track_id in profile["rated_tracks"]:
        return 1.0

    profile_match = calculate_profile_match(track, profile)

    # Convert positive taste affinity into a 0..1 score.
    learned_familiarity = (
        0.5 + (0.5 * profile_match)
    )

    return clamp(learned_familiarity)



# Calculate genre frequencies once when the recommender loads.
GENRE_COUNTS = {}

for catalogue_track in CATALOG:
    catalogue_genres = set(
        get_track_genre_list(catalogue_track) or ["unknown"]
    )

    for genre in catalogue_genres:
        GENRE_COUNTS[genre] = GENRE_COUNTS.get(genre, 0) + 1


def calculate_catalogue_novelty(track):
    """
    Estimate metadata rarity using precomputed genre frequencies.
    This is a catalogue-rarity proxy, not audio novelty.
    """
    track_genres = get_track_genre_list(track) or ["unknown"]

    frequencies = [
        GENRE_COUNTS.get(genre, 1) / max(1, len(CATALOG))
        for genre in track_genres
    ]

    average_frequency = (
        sum(frequencies) / len(frequencies)
        if frequencies else 1.0
    )

    genre_novelty = 1.0 - average_frequency

    return clamp(0.75 * genre_novelty + 0.25 * 0.5)



# ============================================================
# 10. MAXIMAL MARGINAL RELEVANCE (MMR)
# ============================================================

def diversify_recommendations(results, mode="familiar"):

    if len(results) <= 1:

        output = []

        for result in results:
            item = result.copy()

            item["mmrScore"] = round(
                item.get("score", 0.0),
                4
            )

            item["diversityNote"] = (
                "Selected for relevance and variety."
            )

            item.pop("_catalog_index", None)

            output.append(item)

        return output

    candidates = results[:min(50, len(results))]

    indices = [
        item["_catalog_index"]
        for item in candidates
    ]

    similarity_matrix = cosine_similarity(
        TRACK_MATRIX[indices]
    )

    # Familiar prioritizes relevance.
    # Discovery gives more importance to diversity.
    relevance_weight = (
        0.82 if mode == "familiar" else 0.58
    )

    selected_positions = []
    remaining = set(range(len(candidates)))
    selected_mmr_scores = {}

    while remaining and len(selected_positions) < 10:

        best_position = None
        best_mmr = -float("inf")

        for position in remaining:

            relevance = float(
                candidates[position]["score"]
            )

            if selected_positions:

                redundancy = max(
                    float(similarity_matrix[position][selected])
                    for selected in selected_positions
                )

            else:
                redundancy = 0.0

            mmr = (
                relevance_weight * relevance
                - (1.0 - relevance_weight) * redundancy
            )

            if mmr > best_mmr:
                best_mmr = mmr
                best_position = position

        selected_positions.append(best_position)
        remaining.remove(best_position)

        selected_mmr_scores[best_position] = best_mmr

    diversified = []

    for position in selected_positions:

        item = candidates[position].copy()

        item["mmrScore"] = round(
            selected_mmr_scores[position],
            4
        )

        item["diversityNote"] = (
            "Balanced relevance with similarity "
            "to already selected tracks."
        )

        item.pop("_catalog_index", None)

        diversified.append(item)

    return diversified
    # ============================================================
# 11. MAIN RECOMMENDATION FUNCTION
# ============================================================

def recommend_tracks(
    query,
    mode="familiar",
    user_preferences=None
):
    """
    Return up to 10 personalized recommendations.

    Familiar mode:
    Prioritizes query relevance and learned user taste.

    Discovery mode:
    Prioritizes query relevance, catalogue novelty,
    and diversity.
    """

    if not isinstance(query, str) or not query.strip():
        return []

    mode = (
        mode
        if mode in ("familiar", "discovery")
        else "familiar"
    )

    user_preferences = user_preferences or {}

    intent = understand_query(query)

    # Build taste profile from user feedback.
    profile = build_user_taste_profile(user_preferences)

    
    semantic_scores, semantic_method = calculate_hybrid_similarity(
    query
)

    results = []

    for index, track in enumerate(CATALOG):

        # Strict language filtering: when a language is requested,
        # only tracks with confirmed matching metadata are eligible.
        if intent["languages"]:
            language_match = get_language_score(
                track,
                intent["languages"]
            )
            if language_match < 1.0:
                continue

        track_id = get_track_id(track)

        if not track_id:
            track_id = f"track_{index + 1:04d}"

        # Query relevance.
        semantic_score = float(
            semantic_scores[index]
        )

        mood_score = get_mood_score(
            track,
            intent["moods"]
        )

        activity_score = get_activity_score(
            track,
            intent["activities"]
        )

        genre_score = get_genre_score(
            track,
            intent["genres"]
        )

        language_score = get_language_score(
            track,
            intent["languages"]
        )

        # Energy matching.
        track_energy = clamp(
            track.get("energy", 0.5)
        )

        if intent["energy"] is not None:

            energy_score = max(
                0.0,
                1.0 - abs(
                    track_energy - intent["energy"]
                )
            )

        else:
            energy_score = 0.5

        instrumental_score = get_instrumental_score(track)

        # Exact-track feedback.
        preference_score = get_user_preference(
            track_id,
            user_preferences
        )

        normalized_preference = (
            preference_score + 1.0
        ) / 2.0

        # Learned genre, mood and activity preferences.
        profile_match = calculate_profile_match(
            track,
            profile
        )

        normalized_profile = (
            profile_match + 1.0
        ) / 2.0

        # User-specific familiarity.
        familiarity_score = calculate_personal_familiarity(
            track,
            profile
        )

        # Metadata rarity plus personal familiarity.
        catalogue_novelty = calculate_catalogue_novelty(
            track
        )

        novelty_score = clamp(
            0.65 * catalogue_novelty
            + 0.35 * (1.0 - familiarity_score)
        )

        # ----------------------------------------------------
        # QUERY RELEVANCE
        # ----------------------------------------------------

        relevance_score = (
            0.25 * semantic_score
            + 0.22 * mood_score
            + 0.13 * activity_score
            + 0.16 * genre_score
            + 0.09 * energy_score
            + 0.07 * normalized_preference
            + 0.08 * language_score
        )

        # ----------------------------------------------------
        # MODE-SPECIFIC RANKING
        # ----------------------------------------------------

        if mode == "familiar":

            # Familiar mode learns from the user's taste.
            final_score = (
                0.68 * relevance_score
                + 0.22 * normalized_profile
                + 0.10 * familiarity_score
            )

        else:

            # Discovery mode explores outside the user's
            # established taste while respecting the query.
            final_score = (
                0.66 * relevance_score
                + 0.25 * novelty_score
                + 0.09 * (1.0 - normalized_profile)
            )

        # ----------------------------------------------------
        # DISLIKE PENALTY
        # ----------------------------------------------------

        if preference_score < 0:

            final_score *= (
                1.0 - min(0.40, abs(preference_score) * 0.40)
            )

        # ----------------------------------------------------
        # INSTRUMENTAL PREFERENCE
        # ----------------------------------------------------

        if intent["instrumental"]:

            final_score *= (
                0.60 + 0.40 * instrumental_score
            )

        # ----------------------------------------------------
        # LATE-NIGHT PREFERENCE
        # ----------------------------------------------------

        if intent["late_night"]:

            final_score *= (
                0.85 + 0.15 * (1.0 - track_energy)
            )

        # ----------------------------------------------------
        # STRONG GENRE CONSTRAINT
        # ----------------------------------------------------

        if intent["genres"]:

            if genre_score >= 1.0:
                final_score *= 1.0

            elif genre_score > 0.0:
                final_score *= 0.75

            else:
                final_score *= 0.35

        final_score = clamp(final_score)

        # ----------------------------------------------------
        # EXPLANATIONS
        # ----------------------------------------------------

        explanations = []

        if semantic_score >= 0.30:
            explanations.append(
                "Strong metadata match with your description"
            )

        
        
        has_mood_metadata = (
            bool(get_list(track.get("mood", [])))
            and track.get("inference_method") != "generic_fallback"
        )

        has_activity_metadata = (
            bool(get_list(track.get("activities", [])))
            and track.get("inference_method") != "generic_fallback"
        )
         

        if intent["moods"] and has_mood_metadata and mood_score > 0:
            explanations.append("Matches your requested mood")

        if intent["activities"] and has_activity_metadata and activity_score > 0:
            explanations.append("Suitable for your activity")

        if intent["genres"]:

            if genre_score >= 1.0:
                explanations.append(
                    "Matches your requested genre"
                )

            elif genre_score > 0:
                explanations.append(
                    "Partially matches your requested genre"
                )

            else:
                explanations.append(
                    "Alternative genre selected"
                )

        if intent["languages"] and language_score >= 1.0:
            explanations.append(
                "Matches your requested language"
            )
        elif intent["languages"] and language_score == 0.0:
            explanations.append(
                "Language metadata does not match your request"
            )

        if profile_match > 0.15:
            explanations.append(
                "Matches your learned music preferences"
            )

        elif profile_match < -0.15:
            explanations.append(
                "Explores music outside your usual taste"
            )

        if preference_score > 0:
            explanations.append(
                "Supported by your positive track feedback"
            )

        if preference_score < 0:
            explanations.append(
                "Adjusted using your negative feedback"
            )

        if mode == "familiar":
            explanations.append(
                "Familiar mode prioritizes your learned taste"
            )

        else:
            explanations.append(
                "Discovery mode prioritizes novelty and variety"
            )

        if intent["instrumental"]:
            explanations.append(
                "Instrumental preference considered"
            )

        if intent["late_night"] and track_energy <= 0.4:
            explanations.append(
                "Lower-energy selection for late night"
            )

        if not explanations:
            explanations.append(
                "Selected using overall metadata relevance"
            )

        # ----------------------------------------------------
        # RESPONSE OBJECT
        # ----------------------------------------------------

        result = track.copy()

        result["id"] = track_id

        result["semanticId"] = generate_semantic_id(track)

        result["score"] = round(
            final_score,
            4
        )

        result["familiarity"] = round(
            familiarity_score,
            4
        )

        result["novelty"] = round(
            novelty_score,
            4
        )

        result["explanation"] = (
            ". ".join(explanations) + "."
        )

        result["scoreBreakdown"] = {
            "semantic_method": semantic_method,
            "semantic": round(semantic_score, 3),
            "mood": round(mood_score, 3),
            "activity": round(activity_score, 3),
            "genre": round(genre_score, 3),
            "language": round(language_score, 3),
            "energy": round(energy_score, 3),
            "preference": round(normalized_preference, 3),
            "profile": round(normalized_profile, 3),
            "instrumental": round(instrumental_score, 3),
            "familiarity": round(familiarity_score, 3),
            "novelty": round(novelty_score, 3),
        }

        result["_catalog_index"] = index

        results.append(result)

    # Sort before applying MMR.
    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return diversify_recommendations(
        results,
        mode
    )[:10]


# ============================================================
# 12. CATALOGUE DIAGNOSTICS
# ============================================================

def get_catalog_stats():
    """Return basic catalogue diagnostics without pandas."""

    genre_counts = {}

    for track in CATALOG:

        genre = get_track_genres(track) or "unknown"

        genre_counts[genre] = (
            genre_counts.get(genre, 0) + 1
        )

    track_ids = [
        get_track_id(track)
        for track in CATALOG
        if get_track_id(track)
    ]

    return {
        "total_tracks": len(CATALOG),
        "unique_track_ids": len(set(track_ids)),
        "catalogue_file": CATALOG_PATH.name,
        "enriched_tracks": sum(
            1 for track in CATALOG
            if track.get("enrichment_status") == "matched"
        ),
        "genres": dict(sorted(genre_counts.items())),
    }
    # ============================================================
# PHASE 2: SEMANTIC ENGINE DIAGNOSTICS
# ============================================================

def get_semantic_stats():
    """
    Return semantic engine status and configuration.
    """

    return SEMANTIC_INDEX.status()