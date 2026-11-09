import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

# Client ID is an application identifier, not an account password.
JAMENDO_CLIENT_ID = os.getenv("JAMENDO_CLIENT_ID", "30b27eee")
JAMENDO_TRACKS_URL = "https://api.jamendo.com/v3.0/tracks/"


@router.get("/api/music/search")
def search_jamendo_tracks(
    query: str = Query(..., min_length=1, max_length=160),
    limit: int = Query(5, ge=1, le=20),
):
    """Search Jamendo and return playable stream URLs with attribution."""

    if not JAMENDO_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Jamendo Client ID is not configured.",
        )

    params = {
        "client_id": JAMENDO_CLIENT_ID,
        "format": "json",
        "search": query.strip(),
        "limit": limit,
        "audioformat": "mp31",
        "imagesize": 300,
        "include": "musicinfo",
        "type": "single albumtrack",
    }

    request_url = f"{JAMENDO_TRACKS_URL}?{urlencode(params)}"
    request = Request(
        request_url,
        headers={"User-Agent": "SONORA-AI/1.0"},
        method="GET",
    )

    try:
        with urlopen(request, timeout=18) as response:
            payload = json.loads(response.read().decode("utf-8"))

    except HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Jamendo returned HTTP {error.code}.",
        )

    except (URLError, TimeoutError):
        raise HTTPException(
            status_code=504,
            detail="Jamendo could not be reached. Please try again.",
        )

    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(
            status_code=502,
            detail="Jamendo returned an unreadable response.",
        )

    headers = payload.get("headers", {})

    if headers.get("status") != "success":
        raise HTTPException(
            status_code=502,
            detail=headers.get("error_message") or "Jamendo search failed.",
        )

    tracks = []

    for item in payload.get("results", []):
        stream_url = item.get("audio")

        if not stream_url:
            continue

        tracks.append({
            "id": str(item.get("id", "")),
            "name": item.get("name") or "Unknown track",
            "artist_name": item.get("artist_name") or "Unknown artist",
            "album_name": item.get("album_name") or "",
            "duration": int(item.get("duration") or 0),
            "image": item.get("image") or item.get("album_image") or "",
            "audio_url": stream_url,
            "share_url": item.get("shareurl") or item.get("shorturl") or "",
            "license_url": item.get("license_ccurl") or "",
            "audiodownload_allowed": bool(
                item.get("audiodownload_allowed", False)
            ),
            "musicinfo": item.get("musicinfo") or {},
        })

    return {
        "success": True,
        "source": "Jamendo",
        "query": query.strip(),
        "count": len(tracks),
        "results": tracks,
    }