
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "sonora.db"


# -----------------------------------------
# DATABASE CONNECTION
# -----------------------------------------

def get_connection():
    return sqlite3.connect(DB_PATH)


# -----------------------------------------
# DATABASE INITIALIZATION
# -----------------------------------------


def initialize_database():

    with get_connection() as connection:

        # Preserve the complete feedback history.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                track_id TEXT NOT NULL,
                action TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Store only the latest preference per user and track.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS current_feedback (
                user_id TEXT NOT NULL,
                track_id TEXT NOT NULL,
                action TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, track_id)
            )
        """)

        # Migrate existing feedback without deleting history.
        connection.execute("""
            INSERT OR IGNORE INTO current_feedback (
                user_id,
                track_id,
                action,
                updated_at
            )
            SELECT
                f.user_id,
                f.track_id,
                f.action,
                COALESCE(f.created_at, CURRENT_TIMESTAMP)
            FROM feedback f
            WHERE f.id = (
                SELECT MAX(f2.id)
                FROM feedback f2
                WHERE f2.user_id = f.user_id
                AND f2.track_id = f.track_id
            )
        """)

# -----------------------------------------
# RECORD USER FEEDBACK
# -----------------------------------------



def record_feedback(user_id, track_id, action):

    allowed_actions = {
        "like": 1.0,
        "dislike": -1.0,
        "save": 0.7
    }

    if action not in allowed_actions:
        raise ValueError("Invalid feedback action")

    with get_connection() as connection:

        # Preserve every feedback action in history.
        connection.execute("""
            INSERT INTO feedback (user_id, track_id, action)
            VALUES (?, ?, ?)
        """, (user_id, track_id, action))

        # Update the latest preference for this track.
        connection.execute("""
            INSERT INTO current_feedback (
                user_id,
                track_id,
                action,
                updated_at
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)

            ON CONFLICT(user_id, track_id)
            DO UPDATE SET
                action = excluded.action,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, track_id, action))



# -----------------------------------------
# PERSONALIZED USER PREFERENCES
# -----------------------------------------


def remove_feedback(user_id, track_id):

    with get_connection() as connection:

        # Preserve the removal in feedback history.
        connection.execute("""
            INSERT INTO feedback (user_id, track_id, action)
            VALUES (?, ?, 'remove')
        """, (user_id, track_id))

        # Remove the track's active preference.
        connection.execute("""
            DELETE FROM current_feedback
            WHERE user_id = ? AND track_id = ?
        """, (user_id, track_id))


def get_preferences(user_id):
    action_scores = {
        "like": 1.0,
        "dislike": -1.0,
        "save": 0.7
    }

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT track_id, action
            FROM current_feedback
            WHERE user_id = ?
        """, (user_id,)).fetchall()

    scores = {}

    for track_id, action in rows:
        score = action_scores.get(action)

        if score is not None:
            scores[track_id] = score

    return scores



        


# -----------------------------------------
# FEEDBACK ANALYTICS
# -----------------------------------------

def get_feedback_analytics(user_id):

    with get_connection() as connection:

        totals = connection.execute("""
            SELECT
                COUNT(*) AS total_feedback,

                SUM(CASE WHEN action = 'like'
                    THEN 1 ELSE 0 END) AS total_likes,

                SUM(CASE WHEN action = 'dislike'
                    THEN 1 ELSE 0 END) AS total_dislikes,

                SUM(CASE WHEN action = 'save'
                    THEN 1 ELSE 0 END) AS total_saves,

                COUNT(DISTINCT track_id) AS unique_tracks

            FROM feedback
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        recent = connection.execute("""
            SELECT track_id, action, created_at
            FROM feedback
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 10
        """, (user_id,)).fetchall()

    total_feedback = totals[0] or 0
    total_likes = totals[1] or 0
    total_dislikes = totals[2] or 0
    total_saves = totals[3] or 0
    unique_tracks = totals[4] or 0

    positive_feedback = total_likes + total_saves

    engagement_rate = (
        round(positive_feedback / total_feedback * 100, 2)
        if total_feedback else 0
    )

    return {
        "user_id": user_id,

        "total_feedback": total_feedback,

        "total_likes": total_likes,

        "total_dislikes": total_dislikes,

        "total_saves": total_saves,

        "unique_tracks": unique_tracks,

        "positive_feedback": positive_feedback,

        "engagement_rate": engagement_rate,

        "recent_activity": [
            {
                "track_id": row[0],
                "action": row[1],
                "created_at": row[2]
            }
            for row in recent
        ]
    }


# -----------------------------------------
# INITIALIZE DATABASE
# -----------------------------------------

initialize_database()
