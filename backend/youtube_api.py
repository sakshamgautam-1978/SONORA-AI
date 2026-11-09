import os
import json
import urllib.parse
import urllib.request
import urllib.error

from fastapi import APIRouter, HTTPException, Query
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/api/youtube", tags=["SONORA More"])
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

@router.get("/search")
def search_youtube(query: str = Query(..., min_length=1, max_length=160), limit: int = Query(10, ge=1, le=25)):
    if not YOUTUBE_API_KEY:
        raise HTTPException(status_code=503, detail="YouTube API key is not configured in backend/.env.")
    params = {"part": "snippet", "q": query.strip(), "type": "video", "videoCategoryId": "10", "maxResults": limit, "key": YOUTUBE_API_KEY}
    url = YOUTUBE_SEARCH_URL + "?" + urllib.parse.urlencode(params)
    try:
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        tracks = []
        for item in data.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            snippet = item.get("snippet", {})
            if not video_id:
                continue
            thumbnails = snippet.get("thumbnails", {})
            thumbnail = (thumbnails.get("high", {}).get("url") or thumbnails.get("medium", {}).get("url") or thumbnails.get("default", {}).get("url"))
            tracks.append({"videoId": video_id, "title": snippet.get("title", ""), "artist": snippet.get("channelTitle", ""), "thumbnail": thumbnail, "publishedAt": snippet.get("publishedAt", ""), "embedUrl": f"https://www.youtube.com/embed/{video_id}"})
        return {"results": tracks, "total": len(tracks)}
    except urllib.error.HTTPError as error:
        raise HTTPException(status_code=502, detail=f"YouTube API returned HTTP {error.code}.")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=502, detail="Unable to connect to YouTube right now.")
