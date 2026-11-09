# SONORA AI — Integrated Upgrade Build

This package is based on the source files supplied in the conversation. It preserves the existing React/Vite interface, FastAPI routes, Jamendo search, SONORA More YouTube search, SQLite feedback, catalogue and TF-IDF recommender.

## What is implemented in this build

### Phase 1 — Listening experience
- Persistent local playback queue and recently played list.
- Add-to-queue controls on track cards and a queue drawer.
- Shuffle and repeat-off / repeat-all / repeat-one controls.
- Automatic next-track behaviour when a Jamendo audio stream ends.

### Phase 2 — Recommendation intelligence foundation
- Existing TF-IDF metadata relevance, intent, mood, activity, genre and language matching.
- Existing Familiar / Discovery ranking, taste-profile matching and MMR diversification.
- Existing explanation metadata and deterministic metadata identifiers.
- This is not a neural embedding model. Vector embeddings / ANN retrieval are not claimed as implemented.

### Phase 3 — Adaptive listening signals
- SQLite listening event stream for play, skip, complete, like, dislike, save, search and queue-add events.
- Recency-decayed implicit preferences, blended with explicit feedback for recommendation requests.
- Listening history and learning analytics endpoints.
- The current user identifier remains the existing demo user; authentication is not included.

### Phase 4 — Audio intelligence status
- The supplied catalogue contains heuristic metadata labels (mood/activity/energy) rather than measured waveform features.
- BPM, spectral, rhythm and audio-embedding extraction are not fabricated or represented as complete in this build.

### Phase 5 — User ecosystem status
- Existing browser-local saved tracks remain intact; queue and recent history are also stored locally.
- Cross-device sync, user accounts, collaborative playlists and social profiles require authentication and a deployed database and are not enabled in this local build.

### Phase 6 — Evaluation and engineering foundation
- Existing benchmark runner and recommendation-history database retained.
- SQLite indexes added for listening-event queries.
- Health, recommendation, feedback, analytics, evaluation, event, history and learning endpoints available.

## Requirements

- Python 3.10 or newer
- Node.js compatible with Vite 8 (Node.js 20.19+ or 22.12+ recommended)
- Internet connection for Jamendo / YouTube search and remote fonts / images

## Backend setup (Windows PowerShell)

```powershell
cd backend
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` and add your own YouTube Data API key locally. Do not paste it into source code, frontend files, chat, or Git. Jamendo's client ID is configurable there too.

Start the API:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

## Frontend setup (new terminal)

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173

## Useful API endpoints

- `GET /api/health`
- `POST /api/recommend`
- `POST /api/feedback`
- `GET /api/analytics/{user_id}`
- `GET /api/evaluation/{user_id}`
- `POST /api/events`
- `GET /api/history/{user_id}`
- `GET /api/learning/{user_id}`
- `GET /api/music/search?query=ambient&limit=5`
- `GET /api/youtube/search?query=artist%20song&limit=10`

## Benchmark

From `backend/` with the virtual environment active:

```powershell
python run_benchmark.py
```

The benchmark script evaluates the supplied query set and writes `benchmark_results.csv`. Its labels are catalogue metadata checks, not human relevance judgments. Interpret its scores accordingly.

## Data and licensing notes

- The FMA catalogue contains metadata; audio licensing is track-specific. Do not assume all catalogue metadata implies permission to stream or download audio.
- Jamendo playback results include attribution and license links. Respect the track-specific terms.
- YouTube search uses the Data API and playback remains in the official embedded player. Some videos may block embedding or autoplay. Do not extract or download YouTube audio.
- The supplied SQLite databases are copied into this project folder. Keep backups before running migrations or experimenting with user data.

## Upgrade scope

This is an integrated local development build, not a production deployment. It does not claim production authentication, cloud synchronization, distributed event streaming, Redis, a trained collaborative model, a neural audio model, or a contextual-bandit experiment. Those require credentials, deployment infrastructure, sufficient interaction data, and offline/online evaluation before safe activation.
