
import sqlite3
import json
import time
from youtube_api import router as youtube_router
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from recommender import (
    recommend_tracks,
    get_semantic_stats
)

from preferences import (
    record_feedback,
    remove_feedback,
    get_preferences,
    get_feedback_analytics
)
from learning import (
    record_event, get_implicit_preferences, get_listening_history,
    get_learning_analytics, ALLOWED_EVENTS
)

# Jamendo music integration
from jamendo_api import router as jamendo_router


# ---------------------------------
# DATABASE CONFIGURATION
# ---------------------------------

BASE_DIR = Path(__file__).resolve().parent
EVALUATION_DB = BASE_DIR / "sonora_evaluation.db"


def initialize_evaluation_database():
    """Create the recommendation history table if it doesn't exist."""

    with sqlite3.connect(EVALUATION_DB) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS recommendation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                query TEXT NOT NULL,
                mode TEXT NOT NULL,
                recommendation_count INTEGER NOT NULL,
                track_ids TEXT NOT NULL,
                response_time_ms REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        connection.commit()


def record_recommendation(
    user_id,
    query,
    mode,
    recommendations,
    response_time_ms
):
    """Save recommendation activity and measured response time."""

    track_ids = [
        str(track.get("id", track.get("track_id", "unknown")))
        for track in recommendations
    ]

    with sqlite3.connect(EVALUATION_DB) as connection:
        connection.execute("""
            INSERT INTO recommendation_history (
                user_id,
                query,
                mode,
                recommendation_count,
                track_ids,
                response_time_ms,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            query,
            mode,
            len(recommendations),
            json.dumps(track_ids),
            round(response_time_ms, 2),
            datetime.now(timezone.utc).isoformat()
        ))

        connection.commit()


initialize_evaluation_database()


# ---------------------------------
# CREATE FASTAPI APPLICATION
# ---------------------------------

app = FastAPI(
    title="SONORA AI API",
    description="Language-steerable music discovery and recommendation API",
    version="1.2.0"
)


# ---------------------------------
# CORS CONFIGURATION
# ---------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------
# REGISTER JAMENDO ROUTER
# ---------------------------------

app.include_router(jamendo_router)
app.include_router(youtube_router)


# ---------------------------------
# REQUEST MODELS
# ---------------------------------

class RecommendationRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    mode: str = "familiar"
    user_id: str = "demo_user"


class FeedbackRequest(BaseModel):
    user_id: str
    track_id: str
    action: str


class ListeningEventRequest(BaseModel):
    user_id: str = "demo_user"
    track_id: str | None = None
    event_type: str
    duration_seconds: float = 0
    track: dict = Field(default_factory=dict)


# ---------------------------------
# ROOT ROUTE
# ---------------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to SONORA AI API",
        "status": "running",
        "music_provider": "Jamendo"
    }


# ---------------------------------
# HEALTH CHECK
# ---------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "application": "SONORA AI"
    }
# ---------------------------------
# PHASE 2: SEMANTIC ENGINE STATUS
# ---------------------------------

@app.get("/api/recommender/status")
def recommender_status():
    """
    Check the status of the Phase 2 recommendation engine.
    """

    try:
        semantic_status = get_semantic_stats()

        return {
            "success": True,
            "application": "SONORA AI",
            "phase": 2,
            "recommendation_engine": {
                "name": "Hybrid Semantic Recommendation Engine",
                "semantic_engine": semantic_status
            }
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Recommender status error: {str(error)}"
        )


# ---------------------------------
# MUSIC RECOMMENDATION
# ---------------------------------

@app.post("/api/recommend")
def get_recommendations(request: RecommendationRequest):

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Please enter a music discovery query."
        )

    if request.mode not in ["familiar", "discovery"]:
        raise HTTPException(
            status_code=400,
            detail="Mode must be familiar or discovery."
        )

    start_time = time.perf_counter()

    try:
        preferences = get_preferences(request.user_id)
        # Blend explicit feedback with recency-decayed listening signals.
        implicit = get_implicit_preferences(request.user_id)
        for track_id, score in implicit.items():
            preferences[track_id] = max(-1.0, min(1.0,
                0.70 * float(preferences.get(track_id, 0.0)) + 0.30 * score))

        recommendations = recommend_tracks(
            query=query,
            mode=request.mode,
            user_preferences=preferences
        )

        response_time_ms = (
            time.perf_counter() - start_time
        ) * 1000

        # Record recommendation history.
        try:
            record_recommendation(
                user_id=request.user_id,
                query=query,
                mode=request.mode,
                recommendations=recommendations,
                response_time_ms=response_time_ms
            )
        except Exception as logging_error:
            # A logging failure should not break recommendations.
            print(f"Recommendation logging error: {logging_error}")

        return {
            "success": True,
            "query": query,
            "mode": request.mode,
            "user_id": request.user_id,
            "count": len(recommendations),
            "response_time_ms": round(response_time_ms, 2),
            "recommendations": recommendations
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation error: {str(error)}"
        )


# ---------------------------------
# USER FEEDBACK
# ---------------------------------

@app.post("/api/feedback")


@app.post("/api/feedback")
def submit_feedback(request: FeedbackRequest):

    allowed_actions = ["like", "dislike", "save", "remove"]

    if request.action not in allowed_actions:
        raise HTTPException(
            status_code=400,
            detail="Action must be like, dislike, save, or remove."
        )

    try:
        if request.action == "remove":
            remove_feedback(
                user_id=request.user_id,
                track_id=request.track_id
            )
        else:
            record_feedback(
                user_id=request.user_id,
                track_id=request.track_id,
                action=request.action
            )

        return {
            "success": True,
            "message": "Feedback updated successfully.",
            "user_id": request.user_id,
            "track_id": request.track_id,
            "action": request.action
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Feedback error: {str(error)}"
        )


# ---------------------------------
# FEEDBACK ANALYTICS API
# ---------------------------------

@app.get("/api/analytics/{user_id}")
def feedback_analytics(user_id: str):

    try:
        analytics = get_feedback_analytics(user_id)

        return {
            "success": True,
            "analytics": analytics
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Analytics error: {str(error)}"
        )


# ---------------------------------
# RECOMMENDATION EVALUATION API
# ---------------------------------

@app.get("/api/evaluation/{user_id}")
def recommendation_evaluation(user_id: str):

    try:
        with sqlite3.connect(EVALUATION_DB) as connection:

            connection.row_factory = sqlite3.Row

            total = connection.execute("""
                SELECT COUNT(*) AS total
                FROM recommendation_history
                WHERE user_id = ?
            """, (user_id,)).fetchone()["total"]

            average_latency = connection.execute("""
                SELECT AVG(response_time_ms) AS average
                FROM recommendation_history
                WHERE user_id = ?
            """, (user_id,)).fetchone()["average"]

            mode_counts = connection.execute("""
                SELECT mode, COUNT(*) AS count
                FROM recommendation_history
                WHERE user_id = ?
                GROUP BY mode
            """, (user_id,)).fetchall()

            recent = connection.execute("""
                SELECT *
                FROM recommendation_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 10
            """, (user_id,)).fetchall()

        return {
            "success": True,
            "evaluation": {
                "user_id": user_id,
                "total_queries": total,
                "average_response_time_ms": round(
                    average_latency or 0, 2
                ),
                "mode_usage": {
                    row["mode"]: row["count"]
                    for row in mode_counts
                },
                "recent_queries": [
                    {
                        "query": row["query"],
                        "mode": row["mode"],
                        "recommendation_count": row["recommendation_count"],
                        "track_ids": json.loads(row["track_ids"]),
                        "response_time_ms": row["response_time_ms"],
                        "created_at": row["created_at"]
                    }
                    for row in recent
                ]
            }
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation error: {str(error)}"
        )


# ---------------------------------
# LISTENING EVENTS / ADAPTIVE PROFILE
# ---------------------------------

@app.post("/api/events")
def create_listening_event(request: ListeningEventRequest):
    if request.event_type not in ALLOWED_EVENTS:
        raise HTTPException(status_code=400, detail=f"event_type must be one of: {', '.join(sorted(ALLOWED_EVENTS))}")
    if not request.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")
    try:
        event_id = record_event(
            user_id=request.user_id.strip(),
            track_id=request.track_id,
            event_type=request.event_type,
            duration_seconds=request.duration_seconds,
            track=request.track
        )
        return {"success": True, "event_id": event_id, "event_type": request.event_type}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Could not record listening event: {error}")


@app.get("/api/history/{user_id}")
def listening_history(user_id: str, limit: int = 50):
    return {"success": True, "history": get_listening_history(user_id, limit)}


@app.get("/api/learning/{user_id}")
def learning_analytics(user_id: str):
    return {"success": True, "learning": get_learning_analytics(user_id),
            "implicit_preference_tracks": len(get_implicit_preferences(user_id))}
