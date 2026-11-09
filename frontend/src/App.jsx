import { useEffect, useRef, useState } from "react";
import {
  Search, Home, Compass, Heart, Bookmark, User,
  Play, Pause, SkipBack, SkipForward, Volume2,
  Sparkles, Music2, Headphones, TrendingUp, Radio,
  SlidersHorizontal, ThumbsUp, ThumbsDown,
  ChevronRight, Menu, X, AudioWaveform, Shuffle, Repeat, ListMusic,
} from "lucide-react";

import "./App.css";

// -----------------------------------------
// SONORA AI - SAMPLE MUSIC CATALOG
// -----------------------------------------

const demoTracks = [
  {
    id: "track_001",
    title: "Weightless",
    artist: "Marconi Union",
    album: "Ambient Transmissions",
    genre: "Ambient",
    mood: "Calm",
    duration: "8:09",
    year: "2019",
    language: "Instrumental",
    image: "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=500",
    semanticId: "SID-A7F2-91C4",
    explanation: "Soft ambient textures and slow progression make this suitable for deep focus and relaxation.",
    familiarity: 92,
    tags: ["calm", "ambient", "focus", "peaceful", "study"],
  },
  {
    id: "track_002",
    title: "Experience",
    artist: "Ludovico Einaudi",
    album: "In a Time Lapse",
    genre: "Classical",
    mood: "Emotional",
    duration: "5:15",
    year: "2013",
    language: "Instrumental",
    image: "https://images.unsplash.com/photo-1519682337058-a94d519337bc?w=500",
    semanticId: "SID-B8E3-72D1",
    explanation: "Expressive piano arrangements create an emotional atmosphere while maintaining a gentle rhythm.",
    familiarity: 85,
    tags: ["piano", "emotional", "classical", "cinematic", "calm"],
  },
  {
    id: "track_003",
    title: "A Walk",
    artist: "Tycho",
    album: "Dive",
    genre: "Electronic",
    mood: "Dreamy",
    duration: "5:16",
    year: "2011",
    language: "Instrumental",
    image: "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=500",
    semanticId: "SID-C9D4-63A2",
    explanation: "Warm electronic layers and a steady instrumental rhythm create a relaxed but engaging atmosphere.",
    familiarity: 61,
    tags: ["electronic", "dreamy", "chill", "focus", "instrumental"],
  },
  {
    id: "track_004",
    title: "Sunset Lover",
    artist: "Petit Biscuit",
    album: "Presence",
    genre: "Electronic",
    mood: "Happy",
    duration: "3:57",
    year: "2015",
    language: "Instrumental",
    image: "https://images.unsplash.com/photo-1500530850457-b586d89ba3ee?w=500",
    semanticId: "SID-D2A5-84B3",
    explanation: "Light electronic melodies and warm textures create a positive and refreshing listening experience.",
    familiarity: 45,
    tags: ["happy", "chill", "summer", "electronic", "relax"],
  },
  {
    id: "track_005",
    title: "Nuvole Bianche",
    artist: "Ludovico Einaudi",
    album: "Una Mattina",
    genre: "Classical",
    mood: "Peaceful",
    duration: "5:57",
    year: "2004",
    language: "Instrumental",
    image: "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=500",
    semanticId: "SID-E3B6-95C4",
    explanation: "Minimalist piano and gradual melodic development create a peaceful atmosphere.",
    familiarity: 78,
    tags: ["piano", "peaceful", "calm", "classical", "study"],
  },
  {
    id: "track_006",
    title: "Intro",
    artist: "The xx",
    album: "xx",
    genre: "Indie",
    mood: "Mysterious",
    duration: "2:07",
    year: "2009",
    language: "Instrumental",
    image: "https://images.unsplash.com/photo-1519608487953-e999c86e7455?w=500",
    semanticId: "SID-F4C7-16D5",
    explanation: "Minimal production, atmospheric guitar and subtle electronic elements offer a distinctive listening experience.",
    familiarity: 32,
    tags: ["indie", "mysterious", "minimal", "atmospheric", "night"],
  },
];


const API_BASE = "https://sonora-ai-backend.onrender.com/api";
// Stable component outside App: prevents track cards from remounting on every player tick.
function TrackCard({
  track,
  index,
  savedTracks,
  likedTracks,
  dislikedTracks,
  playTrack,
  handleLike,
  handleDislike,
  handleSave,
  setSelectedTrack,
  addToQueue,
}) {
  const isSaved = savedTracks.some((item) => item.id === track.id);
  const isLiked = likedTracks.includes(track.id);
  const isDisliked = dislikedTracks.includes(track.id);

  return (
    <div className="track-card">
      <div className="track-number">{String(index + 1).padStart(2, "0")}</div>

      <div className="track-image-container">
        <img src={track.image} alt={track.title} className="track-image" />
        <button className="image-play-button" onClick={() => playTrack(track)}>
          <Play size={19} fill="currentColor" />
        </button>
      </div>

      <div className="track-information">
        <h3>{track.title}</h3>
        <p>{track.artist}</p>
        <div className="track-tags">
          <span>{track.genre}</span>
          <span>{track.mood}</span>
        </div>
      </div>

      <div className="track-semantic">
        <span className="semantic-label">SEMANTIC ID</span>
        <span className="semantic-value">{track.semanticId || "AI-GENERATED"}</span>
      </div>

      <div className="track-actions">
        <button className={isLiked ? "active-action" : ""} onClick={() => handleLike(track)} title="Like">
          <ThumbsUp size={17} />
        </button>
        <button className={isDisliked ? "active-action" : ""} onClick={() => handleDislike(track)} title="Dislike">
          <ThumbsDown size={17} />
        </button>
        <button className={isSaved ? "active-action" : ""} onClick={() => handleSave(track)} title="Save">
          <Bookmark size={17} />
        </button>
        <button onClick={() => addToQueue?.(track)} title="Add to playback queue">
          <ListMusic size={17} />
        </button>
        <button onClick={() => setSelectedTrack(track)} title="More information">
          <ChevronRight size={19} />
        </button>
      </div>
    </div>
  );
}

// -----------------------------------------
// MAIN APPLICATION
// -----------------------------------------

function App() {
  const [activePage, setActivePage] = useState("Discover");
  const [query, setQuery] = useState(
    "Something calm for a 3 a.m. study session"
  );
  const [mode, setMode] = useState("discovery");

  const [tracks, setTracks] = useState([]);
  // Restore saved tracks from this browser when the app starts.
  const [savedTracks, setSavedTracks] = useState(() => {
    try {
      const storedTracks = localStorage.getItem("sonora_saved_tracks_v1");
      const parsedTracks = storedTracks ? JSON.parse(storedTracks) : [];
      return Array.isArray(parsedTracks) ? parsedTracks : [];
    } catch (error) {
      console.error("Could not restore saved tracks:", error);
      return [];
    }
  });
  const [likedTracks, setLikedTracks] = useState([]);
  const [dislikedTracks, setDislikedTracks] = useState([]);

  // Persist every save/unsave change so it survives page refreshes.
  useEffect(() => {
    try {
      localStorage.setItem("sonora_saved_tracks_v1", JSON.stringify(savedTracks));
    } catch (error) {
      console.error("Could not persist saved tracks:", error);
      showToast("Saved tracks could not be stored in this browser.");
    }
  }, [savedTracks]);

  const [currentTrack, setCurrentTrack] = useState(demoTracks[0]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playQueue, setPlayQueue] = useState(() => {
    try { return JSON.parse(localStorage.getItem("sonora_queue_v1") || "[]"); }
    catch { return []; }
  });
  const [recentlyPlayed, setRecentlyPlayed] = useState(() => {
    try { return JSON.parse(localStorage.getItem("sonora_recent_v1") || "[]"); }
    catch { return []; }
  });
  const [shuffleEnabled, setShuffleEnabled] = useState(false);
  const [repeatMode, setRepeatMode] = useState("off");
  const [queueOpen, setQueueOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  // YouTube discovery and embedded playback
  const [youtubeQuery, setYoutubeQuery] = useState("");
  const [youtubeResults, setYoutubeResults] = useState([]);
  const [youtubeLoading, setYoutubeLoading] = useState(false);
  const [selectedYoutubeVideo, setSelectedYoutubeVideo] = useState(null);

  // REAL JAMENDO AUDIO PLAYER
  const audioRef = useRef(null);
  const [playbackTime, setPlaybackTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);

  const [selectedTrack, setSelectedTrack] = useState(null);
  const [toast, setToast] = useState("");
  const [mobileMenu, setMobileMenu] = useState(false);

  const [userId] = useState("demo_user");

  // ANALYTICS STATE
  const [analyticsData, setAnalyticsData] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  // EVALUATION STATE
  const [evaluationData, setEvaluationData] = useState(null);
  const [evaluationLoading, setEvaluationLoading] = useState(false);

  // ---------------------------------------
  // TOAST
  // ---------------------------------------

  const showToast = (message) => {
    setToast(message);
    setTimeout(() => setToast(""), 2500);
  };

  useEffect(() => { localStorage.setItem("sonora_queue_v1", JSON.stringify(playQueue)); }, [playQueue]);
  useEffect(() => { localStorage.setItem("sonora_recent_v1", JSON.stringify(recentlyPlayed.slice(0, 50))); }, [recentlyPlayed]);

  const recordListeningEvent = async (eventType, track, durationSeconds = 0) => {
    if (!track?.id) return;
    try {
      await fetch(`${API_BASE}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, track_id: track.id, event_type: eventType,
          duration_seconds: durationSeconds, track: { id: track.id, title: track.title,
            artist: track.artist, genre: track.genre, mood: track.mood } }),
      });
    } catch (error) {
      console.debug("Listening event was kept local only:", error);
    }
  };

  const addToQueue = (track) => {
    if (!track?.id) return;
    setPlayQueue((previous) => previous.some((item) => item.id === track.id)
      ? previous : [...previous, track]);
    showToast(`${track.title} added to your queue.`);
    recordListeningEvent("queue_add", track);
  };

  const playNextFromQueue = () => {
    if (!playQueue.length) return false;
    const [next, ...remaining] = playQueue;
    setPlayQueue(remaining);
    playTrack(next);
    return true;
  };

  // ---------------------------------------
  // SEARCH
  // ---------------------------------------

  const handleSearch = async (event) => {
    event?.preventDefault();

    if (!query.trim()) {
      showToast("Please describe what you want to listen to.");
      return;
    }

    setIsSearching(true);

    try {
      const response = await fetch(`${API_BASE}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          mode,
          user_id: userId,
        }),
      });

      if (!response.ok) {
        throw new Error("Backend unavailable");
      }

      const data = await response.json();
      const recommendations =
        data.recommendations || data.tracks || [];

      if (!Array.isArray(recommendations) || !recommendations.length) {
        throw new Error("No recommendations returned.");
      }

      const normalizedTracks = recommendations.map((track) => {
        const previewTrack = demoTracks.find(
          (item) => item.id === track.id
        );

        const moods = Array.isArray(track.mood)
          ? track.mood
          : track.mood
            ? [track.mood]
            : [];

        return {
          ...track,
          album: track.album || track.genre || "SONORA discovery",
          mood: moods.join(", ") || "Discovery",
          image:
            track.image ||
            previewTrack?.image ||
            "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=500",
          duration: track.duration || "—",
          year: String(track.year || "—"),
          familiarity:
            typeof track.familiarity === "number"
              ? Math.round(track.familiarity * 100)
              : 0,
          tags: Array.isArray(track.tags) ? track.tags : [],
        };
      });

      setTracks(normalizedTracks);
      setCurrentTrack(normalizedTracks[0]);
      showToast("Recommendations generated!");
    } catch (error) {
      console.error("SONORA recommendation error:", error);
      showToast("Could not reach SONORA AI. Check the backend.");
    } finally {
      setIsSearching(false);
    }
  };

  // ---------------------------------------
  // SONORA MORE SEARCH
  // ---------------------------------------

  const searchYouTube = async (event) => {
    event?.preventDefault();

    const searchTerm = youtubeQuery.trim();
    if (!searchTerm) {
      showToast("Enter a song, artist or album to search SONORA More.");
      return;
    }

    setYoutubeLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/youtube/search?query=${encodeURIComponent(searchTerm)}&limit=10`
      );
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || "SONORA More search failed.");
      }

      const results = Array.isArray(data.results) ? data.results : [];
      setYoutubeResults(results);

      if (results.length > 0) {
        setSelectedYoutubeVideo(results[0]);
        showToast(`Found ${results.length} songs.`);
      } else {
        setSelectedYoutubeVideo(null);
        showToast("No results found. Try another search.");
      }
    } catch (error) {
      console.error("SONORA More search error:", error);
      showToast(error.message || "Could not complete music search.");
    } finally {
      setYoutubeLoading(false);
    }
  };

  // ---------------------------------------
  // FEEDBACK API
  // ---------------------------------------

  const sendFeedback = async (trackId, action) => {
    try {
      const response = await fetch(`${API_BASE}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          track_id: trackId,
          action,
        }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok || data.success === false) {
        throw new Error(data.detail || "Feedback request failed");
      }

      return true;
    } catch (error) {
      console.error("Feedback error:", error);
      showToast("Feedback could not be synced. Please try again.");
      return false;
    }
  };

  // ---------------------------------------
  // LIKE
  // ---------------------------------------

  const handleLike = async (track) => {
    if (!track?.id) return;

    // Clicking an active Like removes the preference from the backend too.
    if (likedTracks.includes(track.id)) {
      const success = await sendFeedback(track.id, "remove");
      if (!success) return;

      setLikedTracks((prev) => prev.filter((id) => id !== track.id));
      showToast("Like removed.");
      return;
    }

    const success = await sendFeedback(track.id, "like");
    if (!success) return;

    setLikedTracks((prev) => [...new Set([...prev, track.id])]);
    setDislikedTracks((prev) => prev.filter((id) => id !== track.id));

    // Promote a liked recommendation after the backend confirms the action.
    setTracks((prev) => {
      const selected = prev.find((item) => item.id === track.id);
      if (!selected) return prev;
      return [selected, ...prev.filter((item) => item.id !== track.id)];
    });

    showToast("Liked — moved to the top of your recommendations ❤️");
  };

  // ---------------------------------------
  // DISLIKE
  // ---------------------------------------

  const handleDislike = async (track) => {
    if (!track?.id) return;

    // Clicking an active Dislike removes the preference.
    if (dislikedTracks.includes(track.id)) {
      const success = await sendFeedback(track.id, "remove");
      if (!success) return;

      setDislikedTracks((prev) => prev.filter((id) => id !== track.id));
      showToast("Dislike removed.");
      return;
    }

    const success = await sendFeedback(track.id, "dislike");
    if (!success) return;

    setDislikedTracks((prev) => [...new Set([...prev, track.id])]);
    setLikedTracks((prev) => prev.filter((id) => id !== track.id));

    // Remove a disliked track from the current recommendation list.
    setTracks((prev) => prev.filter((item) => item.id !== track.id));
    showToast("Disliked — removed from your recommendations");
  };

  // ---------------------------------------
  // SAVE
  // ---------------------------------------

  const handleSave = async (track) => {
    if (!track?.id) return;

    const alreadySaved = savedTracks.some((item) => item.id === track.id);

    if (alreadySaved) {
      const success = await sendFeedback(track.id, "remove");
      if (!success) return;

      setSavedTracks((prev) => prev.filter((item) => item.id !== track.id));
      showToast("Removed from saved tracks.");
      return;
    }

    const success = await sendFeedback(track.id, "save");
    if (!success) return;

    setSavedTracks((prev) => [...prev, track]);
    showToast("Track saved successfully!");
  };

  // ---------------------------------------
  // ANALYTICS API
  // ---------------------------------------

  const fetchAnalytics = async () => {
    setAnalyticsLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/analytics/${userId}`
      );

      if (!response.ok) {
        throw new Error("Analytics API unavailable");
      }

      const data = await response.json();

      if (!data.success || !data.analytics) {
        throw new Error("Invalid analytics response");
      }

      setAnalyticsData(data.analytics);
    } catch (error) {
      console.error("Analytics error:", error);
      showToast("Unable to load feedback analytics.");
    } finally {
      setAnalyticsLoading(false);
    }
  };

  // ---------------------------------------
  // EVALUATION API
  // ---------------------------------------

  const fetchEvaluation = async () => {
    setEvaluationLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/evaluation/${userId}`
      );

      if (!response.ok) {
        throw new Error("Evaluation API unavailable");
      }

      const data = await response.json();

      if (!data.success || !data.evaluation) {
        throw new Error("Invalid evaluation response");
      }

      setEvaluationData(data.evaluation);
    } catch (error) {
      console.error("Evaluation error:", error);
      showToast("Unable to load evaluation data.");
    } finally {
      setEvaluationLoading(false);
    }
  };

  const refreshAllAnalytics = () => {
    fetchAnalytics();
    fetchEvaluation();
  };

  // ---------------------------------------
  // REAL JAMENDO AUDIO PLAYER
  // ---------------------------------------

  const formatTime = (seconds) => {
    if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60).toString().padStart(2, "0");
    return `${mins}:${secs}`;
  };

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.volume = volume;
  }, [volume]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (currentTrack?.audioUrl && audio.src !== currentTrack.audioUrl) {
      audio.src = currentTrack.audioUrl;
      audio.load();
    }

    if (isPlaying && currentTrack?.audioUrl) {
      audio.play().catch(() => {
        setIsPlaying(false);
        showToast("Browser blocked playback. Press Play once more.");
      });
    } else {
      audio.pause();
    }
  }, [isPlaying, currentTrack?.audioUrl]);

  const playTrack = async (track) => {
    if (!track) return;

    // Toggle playback when the currently loaded track is selected again.
    if (currentTrack?.id === track.id && currentTrack?.audioUrl) {
      setIsPlaying((playing) => !playing);
      return;
    }

    const audio = audioRef.current;
    if (audio) audio.pause();

    setIsPlaying(false);
    setIsLoadingAudio(true);
    setPlaybackTime(0);
    setAudioDuration(0);
    setCurrentTrack({ ...track, audioUrl: null });
    setActivePage((page) => page);

    try {
      const response = await fetch(
        `${API_BASE}/music/search?query=${encodeURIComponent(
          `${track.title} ${track.artist || ""}`.trim()
        )}&limit=5`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Jamendo search failed.");
      }

      const data = await response.json();
      const results = Array.isArray(data.results) ? data.results : [];

      if (!results.length || !results[0].audio_url) {
        throw new Error("No playable Jamendo stream was found for this track.");
      }

      const match = results[0];
      const playableTrack = {
        ...track,
        title: match.name || track.title,
        artist: match.artist_name || track.artist,
        album: match.album_name || track.album,
        image: match.image || track.image,
        duration: formatTime(Number(match.duration)) || track.duration,
        audioUrl: match.audio_url,
        jamendoId: match.id,
        jamendoUrl: match.share_url,
        licenseUrl: match.license_url,
        audioSource: "Jamendo",
              };

      setCurrentTrack(playableTrack);
      setIsPlaying(true);
      setRecentlyPlayed((previous) => [playableTrack, ...previous.filter((item) => item.id !== playableTrack.id)].slice(0, 50));
      recordListeningEvent("play", playableTrack);
      showToast(`Loading ${playableTrack.title} from Jamendo`);
    } catch (error) {
      console.error("Jamendo playback error:", error);
      setIsPlaying(false);
      showToast(error.message || "Could not load this audio preview.");
    } finally {
      setIsLoadingAudio(false);
    }
  };

  const skipTrack = (direction) => {
    if (direction > 0 && playQueue.length) { playNextFromQueue(); return; }
    if (!tracks.length) return;
    if (direction > 0) recordListeningEvent("skip", currentTrack, playbackTime);
    const currentIndex = tracks.findIndex((track) => track.id === currentTrack?.id);
    const safeIndex = currentIndex < 0 ? 0 : currentIndex;
    let nextIndex;
    if (shuffleEnabled && tracks.length > 1) {
      const candidates = tracks.map((_, index) => index).filter((index) => index !== safeIndex);
      nextIndex = candidates[Math.floor(Math.random() * candidates.length)];
    } else {
      nextIndex = safeIndex + direction;
      if (nextIndex >= tracks.length) nextIndex = repeatMode === "off" ? 0 : 0;
      if (nextIndex < 0) nextIndex = tracks.length - 1;
    }
    playTrack(tracks[nextIndex]);
  };

  const handleTrackEnded = () => {
    recordListeningEvent("complete", currentTrack, audioDuration || playbackTime);
    setPlaybackTime(0);
    if (repeatMode === "one" && audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
      return;
    }
    if (playQueue.length) { playNextFromQueue(); return; }
    if (repeatMode === "all" || tracks.length > 1) { skipTrack(1); return; }
    setIsPlaying(false);
  };

  const handleSeek = (event) => {
    const nextTime = Number(event.target.value);
    if (audioRef.current && Number.isFinite(nextTime)) {
      audioRef.current.currentTime = nextTime;
      setPlaybackTime(nextTime);
    }
  };

  // ---------------------------------------
  // NAVIGATION
  // ---------------------------------------

  const navigation = [
    { name: "Discover", icon: Compass },
    { name: "SONORA More", icon: Search },
    { name: "For You", icon: Home },
    { name: "Saved", icon: Bookmark },
    { name: "My Taste", icon: User },
    { name: "Analytics", icon: TrendingUp },
  ];

  const handleNavigation = (page) => {
    setActivePage(page);
    setMobileMenu(false);

    if (page === "For You" && tracks.length === 0) {
      handleSearch();
    }

    if (page === "Analytics") {
      refreshAllAnalytics();
    }
  };

  // ---------------------------------------
  // DISCOVER PAGE
  // ---------------------------------------

  const DiscoverPage = () => (
    <>
      <div className="welcome-section">
        <div>
          <span className="eyebrow">
            <Sparkles size={14} />
            YOUR PERSONAL MUSIC INTELLIGENCE
          </span>

          <h1>
            Discover music
            <br />
            <span>beyond your habits.</span>
          </h1>

          <p>
            Tell us how you feel. We'll find the music
            that understands you.
          </p>
        </div>

        <div className="welcome-icon">
          <AudioWaveform size={100} strokeWidth={1} />
        </div>
      </div>

      <section className="search-panel">
        <div className="search-heading">
          <div>
            <Sparkles size={18} />
            <span>DESCRIBE YOUR MOMENT</span>
          </div>

          <span className="ai-badge">AI POWERED</span>
        </div>

        <form onSubmit={handleSearch}>
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Example: Something peaceful for a rainy evening..."
          />

          <div className="search-bottom">
            <div className="mode-switch">
              <button
                type="button"
                className={mode === "familiar" ? "mode-active" : ""}
                onClick={() => setMode("familiar")}
              >
                <Headphones size={15} />
                Familiar
              </button>

              <button
                type="button"
                className={mode === "discovery" ? "mode-active" : ""}
                onClick={() => setMode("discovery")}
              >
                <Compass size={15} />
                Discovery
              </button>
            </div>

            <button
              className="search-button"
              type="submit"
              disabled={isSearching}
            >
              {isSearching ? (
                "Finding music..."
              ) : (
                <>
                  <Search size={17} />
                  Discover music
                </>
              )}
            </button>
          </div>
        </form>

        <div className="mode-description">
          {mode === "familiar"
            ? "Familiar mode: Prioritizes music close to your existing preferences."
            : "Discovery mode: Explores new sounds while respecting your preferences."}
        </div>
      </section>

      <section className="recommendation-section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">
              <Sparkles size={14} />
              CURATED FOR YOUR MOMENT
            </span>

            <h2>Your discoveries</h2>
          </div>

          <button className="filter-button">
            <SlidersHorizontal size={16} />
            Personalized
          </button>
        </div>

        <div className="results-info">
          <span>{tracks.length} tracks found</span>
          <span>
            {mode === "discovery" ? "Discovery mode" : "Familiar mode"}
          </span>
        </div>

        <div className="tracks-list">
          {tracks.map((track, index) => (
            <TrackCard
              key={track.id}
              track={track}
              index={index}
              savedTracks={savedTracks}
              likedTracks={likedTracks}
              dislikedTracks={dislikedTracks}
              playTrack={playTrack}
              handleLike={handleLike}
              handleDislike={handleDislike}
              handleSave={handleSave}
              setSelectedTrack={setSelectedTrack}
              addToQueue={addToQueue}
            />
          ))}
        </div>

        {tracks.length === 0 && (
          <div className="empty-state">
            <Music2 size={35} />
            <h3>Ready to discover?</h3>
            <p>
              Describe your moment above and SONORA AI will find matching music.
            </p>
          </div>
        )}
      </section>
    </>
  );

  // ---------------------------------------
  // FOR YOU PAGE
  // ---------------------------------------

  const SonoraMorePage = () => (
    <div className="content-page">
      <span className="eyebrow">
        <Music2 size={14} />
        SONORA MORE • MUSIC DISCOVERY
      </span>

      <h1>Find your song.</h1>
      <p className="page-subtitle">
        Search Bollywood, Hollywood, Indian and international music,
        then play eligible videos inside SONORA AI.
      </p>

      <form
        onSubmit={searchYouTube}
        style={{
          display: "flex",
          gap: "12px",
          flexWrap: "wrap",
          margin: "26px 0",
        }}
      >
        <input
          value={youtubeQuery}
          onChange={(event) => setYoutubeQuery(event.target.value)}
          placeholder="Search a song, artist or album..."
          aria-label="Search SONORA More music"
          style={{
            flex: "1 1 260px",
            minWidth: 0,
            padding: "16px 18px",
            borderRadius: "12px",
            border: "1px solid rgba(255,255,255,0.14)",
            background: "rgba(255,255,255,0.06)",
            color: "inherit",
            font: "inherit",
          }}
        />
        <button className="search-button" type="submit" disabled={youtubeLoading}>
          <Search size={17} />
          {youtubeLoading ? "Searching..." : "Search SONORA More"}
        </button>
      </form>

      {selectedYoutubeVideo && (
        <section
          style={{
            marginBottom: "30px",
            padding: "18px",
            borderRadius: "18px",
            background: "rgba(255,255,255,0.045)",
            border: "1px solid rgba(255,255,255,0.10)",
          }}
        >
          <div style={{ marginBottom: "14px" }}>
            <span className="eyebrow">NOW PLAYING IN SONORA</span>
            <h2 style={{ margin: "8px 0 4px" }}>{selectedYoutubeVideo.title}</h2>
            <p style={{ margin: 0, color: "#aaa8bd" }}>{selectedYoutubeVideo.artist}</p>
          </div>

          <div
            style={{
              position: "relative",
              width: "100%",
              aspectRatio: "16 / 9",
              overflow: "hidden",
              borderRadius: "14px",
              background: "#000",
            }}
          >
            <iframe
              key={selectedYoutubeVideo.videoId}
              src={`https://www.youtube-nocookie.com/embed/${selectedYoutubeVideo.videoId}?autoplay=1&rel=0`}
              title={`SONORA video player: ${selectedYoutubeVideo.title}`}
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                border: 0,
              }}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              referrerPolicy="strict-origin-when-cross-origin"
              allowFullScreen
            />
          </div>
          <p style={{ color: "#aaa8bd", fontSize: "12px", marginTop: "10px" }}>
            Playback uses the official embedded video player. Some videos may
            restrict embedding or playback in certain regions.
          </p>
          <div
            aria-label="SONORA More branding"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "8px",
              marginTop: "16px",
              padding: "13px 15px",
              borderRadius: "12px",
              background: "linear-gradient(110deg, rgba(155,124,255,0.18), rgba(255,255,255,0.035))",
              border: "1px solid rgba(155,124,255,0.22)",
            }}
          >
            <strong style={{ letterSpacing: "0.16em", color: "#d8ccff" }}>SONORA</strong>
            <span style={{ fontSize: "11px", letterSpacing: "0.12em", color: "#aaa8bd" }}>
              MORE • YOUR MUSIC, YOUR WORLD
            </span>
          </div>
        </section>
      )}

      <section>
        <div className="section-heading">
          <div>
            <span className="eyebrow">SEARCH RESULTS</span>
            <h2>{youtubeResults.length ? "Choose a track" : "Search SONORA More"}</h2>
          </div>
          <span className="ai-badge">{youtubeResults.length} RESULTS</span>
        </div>

        {youtubeResults.length > 0 ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
              gap: "16px",
            }}
          >
            {youtubeResults.map((video) => {
              const isSelected = selectedYoutubeVideo?.videoId === video.videoId;

              return (
                <button
                  key={video.videoId}
                  type="button"
                  onClick={() => setSelectedYoutubeVideo(video)}
                  aria-pressed={isSelected}
                  style={{
                    textAlign: "left",
                    padding: "10px",
                    borderRadius: "14px",
                    cursor: "pointer",
                    color: "inherit",
                    background: isSelected
                      ? "rgba(155,124,255,0.15)"
                      : "rgba(255,255,255,0.045)",
                    border: isSelected
                      ? "1px solid rgba(155,124,255,0.75)"
                      : "1px solid rgba(255,255,255,0.10)",
                  }}
                >
                  <img
                    src={video.thumbnail}
                    alt=""
                    loading="lazy"
                    style={{
                      display: "block",
                      width: "100%",
                      aspectRatio: "16 / 9",
                      objectFit: "cover",
                      borderRadius: "9px",
                      marginBottom: "10px",
                    }}
                  />
                  <strong style={{ display: "block", fontSize: "14px", lineHeight: 1.45 }}>
                    {video.title}
                  </strong>
                  <span style={{ display: "block", color: "#aaa8bd", fontSize: "12px", marginTop: "6px" }}>
                    {video.artist}
                  </span>
                  <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", marginTop: "10px", fontSize: "12px", color: "#c7b7ff" }}>
                    <Play size={13} fill="currentColor" />
                    {isSelected ? "Selected" : "Play in SONORA"}
                  </span>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="empty-state">
            <Music2 size={35} />
            <h3>Your music search starts here</h3>
            <p>
              Try “Kesariya Arijit Singh” or “Blinding Lights The Weeknd”.
            </p>
          </div>
        )}
      </section>
    </div>
  );

  const ForYouPage = () => {
    const personalizedTracks = tracks.filter(
      (track) => !dislikedTracks.includes(track.id)
    );

    return (
      <div className="content-page">
        <span className="eyebrow">
          <Sparkles size={14} />
          PERSONALIZED MUSIC
        </span>

        <h1>Made for you.</h1>

        <p className="page-subtitle">
          Recommendations shaped by your preferences
          and listening feedback.
        </p>

        <div className="for-you-insights">
          <div className="insight-heading">
            <Sparkles size={19} />
            <div>
              <h2>Your listening profile</h2>
              <p>Built from your interactions with SONORA</p>
            </div>
          </div>

          <div className="insight-stats">
            <div>
              <strong>{likedTracks.length}</strong>
              <span>Liked</span>
            </div>

            <div>
              <strong>{dislikedTracks.length}</strong>
              <span>Disliked</span>
            </div>

            <div>
              <strong>{savedTracks.length}</strong>
              <span>Saved</span>
            </div>
          </div>

          <p className="insight-note">
            Your feedback helps SONORA adjust future recommendations.
          </p>
        </div>

        <div className="taste-evolving">
          <span className="evolving-dot"></span>
          <Sparkles size={15} />
          <span>
            {likedTracks.length + savedTracks.length > 0
              ? `Your taste is evolving — ${likedTracks.length + savedTracks.length} positive interactions`
              : "Your taste profile is learning from your feedback"}
          </span>
        </div>

        {personalizedTracks.length > 0 ? (
          <div className="tracks-list">
            {personalizedTracks.map((track, index) => (
              <TrackCard
                key={track.id}
                track={track}
                index={index}
                savedTracks={savedTracks}
                likedTracks={likedTracks}
                dislikedTracks={dislikedTracks}
                playTrack={playTrack}
                handleLike={handleLike}
                handleDislike={handleDislike}
                handleSave={handleSave}
                setSelectedTrack={setSelectedTrack}
              />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <Headphones size={35} />
            <h3>Your personal mix is waiting</h3>
            <p>
              Discover some music first. Like or save tracks
              to help SONORA understand your preferences.
            </p>

            <button
              className="search-button"
              onClick={() => {
                setActivePage("Discover");
                handleSearch();
              }}
            >
              <Sparkles size={16} />
              Generate recommendations
            </button>
          </div>
        )}
      </div>
    );
  };

  // ---------------------------------------
  // SAVED PAGE
  // ---------------------------------------

  const SavedPage = () => (
    <div className="content-page">
      <span className="eyebrow">
        <Bookmark size={14} />
        YOUR COLLECTION
      </span>

      <h1>Saved music.</h1>

      <p className="page-subtitle">
        Your personally collected discoveries.
      </p>

      {savedTracks.length > 0 ? (
        <div className="tracks-list">
          {savedTracks.map((track, index) => (
            <TrackCard
              key={track.id}
              track={track}
              index={index}
              savedTracks={savedTracks}
              likedTracks={likedTracks}
              dislikedTracks={dislikedTracks}
              playTrack={playTrack}
              handleLike={handleLike}
              handleDislike={handleDislike}
              handleSave={handleSave}
              setSelectedTrack={setSelectedTrack}
              addToQueue={addToQueue}
            />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <Bookmark size={35} />
          <h3>Your collection is waiting</h3>
          <p>Save tracks you love to find them here.</p>
        </div>
      )}
    </div>
  );

  // ---------------------------------------
  // MY TASTE PAGE
  // ---------------------------------------

  const TastePage = () => (
    <div className="content-page">
      <span className="eyebrow">
        <AudioWaveform size={14} />
        YOUR MUSIC DNA
      </span>

      <h1>Understand your taste.</h1>

      <p className="page-subtitle">
        Your music personality evolves with every interaction.
      </p>

      <div className="stats-grid">
        <div className="stat-card">
          <Heart size={23} />
          <h2>{likedTracks.length}</h2>
          <p>Liked tracks</p>
        </div>

        <div className="stat-card">
          <Bookmark size={23} />
          <h2>{savedTracks.length}</h2>
          <p>Saved tracks</p>
        </div>

        <div className="stat-card">
          <Music2 size={23} />
          <h2>{tracks.length}</h2>
          <p>Recommendations</p>
        </div>

        <div className="stat-card">
          <TrendingUp size={23} />
          <h2>{mode === "discovery" ? "ON" : "OFF"}</h2>
          <p>Discovery mode</p>
        </div>
      </div>

      <div className="taste-card">
        <h2>Your current preferences</h2>

        <p>
          Your profile will evolve as you like, dislike,
          and save music.
        </p>

        <div className="taste-tags">
          {[
            "Ambient",
            "Classical",
            "Electronic",
            "Instrumental",
            "Chill",
            "Indie",
          ].map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>

        <div className="taste-progress">
          <div>
            <span>Positive feedback</span>
            <span>{likedTracks.length} tracks</span>
          </div>

          <div className="progress-bar">
            <div
              style={{
                width: `${Math.min(likedTracks.length * 15, 100)}%`,
              }}
            />
          </div>
        </div>
      </div>

      <section className="taste-card" style={{ marginTop: 18 }}>
        <h2>Recently played</h2>
        <p>Your latest listening sessions on this device.</p>
        {recentlyPlayed.length ? recentlyPlayed.slice(0, 6).map((track) => (
          <div key={track.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderTop: "1px solid rgba(255,255,255,.07)" }}>
            <img src={track.image} alt="" style={{ width: 42, height: 42, borderRadius: 8, objectFit: "cover" }} />
            <div style={{ flex: 1 }}><strong>{track.title}</strong><p>{track.artist}</p></div>
            <button onClick={() => playTrack(track)} title="Play again"><Play size={17}/></button>
            <button onClick={() => addToQueue(track)} title="Add to queue"><ListMusic size={17}/></button>
          </div>
        )) : <p>No listening history yet. Play a Jamendo track to start building it.</p>}
      </section>
    </div>
  );

  // ---------------------------------------
  // ANALYTICS + EVALUATION PAGE
  // ---------------------------------------

  const AnalyticsPage = () => {
    const analytics = analyticsData;
    const evaluation = evaluationData;

    const discoveryQueries =
      evaluation?.mode_usage?.discovery || 0;
          const familiarQueries =
      evaluation?.mode_usage?.familiar || 0;

    const totalModeQueries =
      discoveryQueries + familiarQueries;

    const discoveryPercentage =
      totalModeQueries > 0
        ? (discoveryQueries / totalModeQueries) * 100
        : 0;

    const familiarPercentage =
      totalModeQueries > 0
        ? (familiarQueries / totalModeQueries) * 100
        : 0;

    const formatDate = (value) => {
      if (!value) return "Recently";

      const date = new Date(value);

      return Number.isNaN(date.getTime())
        ? value
        : date.toLocaleString();
    };

    return (
      <div className="content-page analytics-page">
        <span className="eyebrow">
          <TrendingUp size={14} />
          YOUR MUSIC INTELLIGENCE
        </span>

        <h1>Analytics overview.</h1>

        <p className="page-subtitle">
          Explore feedback statistics and measure recommendation
          engine performance.
        </p>

        <button
          className="filter-button"
          onClick={refreshAllAnalytics}
          disabled={analyticsLoading || evaluationLoading}
          style={{ marginBottom: "25px" }}
        >
          <TrendingUp size={15} />
          {analyticsLoading || evaluationLoading
            ? "Refreshing..."
            : "Refresh all data"}
        </button>

        {/* FEEDBACK ANALYTICS */}

        <div className="analytics-panel">
          <h2>Feedback analytics</h2>

          {analyticsLoading && !analytics ? (
            <p>Loading feedback analytics...</p>
          ) : !analytics ? (
            <button
              className="search-button"
              onClick={fetchAnalytics}
            >
              Load feedback analytics
            </button>
          ) : (
            <>
              <div className="stats-grid">
                <div className="stat-card">
                  <Music2 size={23} />
                  <h2>{analytics.total_feedback ?? 0}</h2>
                  <p>Total interactions</p>
                </div>

                <div className="stat-card">
                  <ThumbsUp size={23} />
                  <h2>{analytics.total_likes ?? 0}</h2>
                  <p>Total likes</p>
                </div>

                <div className="stat-card">
                  <ThumbsDown size={23} />
                  <h2>{analytics.total_dislikes ?? 0}</h2>
                  <p>Total dislikes</p>
                </div>

                <div className="stat-card">
                  <Bookmark size={23} />
                  <h2>{analytics.total_saves ?? 0}</h2>
                  <p>Saved interactions</p>
                </div>
              </div>

              <div className="analytics-panel">
                <h2>Engagement performance</h2>

                <div className="engagement-number">
                  {Number(
                    analytics.engagement_rate || 0
                  ).toFixed(2)}%
                </div>

                <p>Positive feedback rate</p>

                <div className="analytics-progress">
                  <div
                    style={{
                      width: `${Math.max(
                        0,
                        Math.min(
                          Number(analytics.engagement_rate) || 0,
                          100
                        )
                      )}%`,
                    }}
                  />
                </div>

                <div className="analytics-extra">
                  <div>
                    <strong>
                      {analytics.positive_feedback ?? 0}
                    </strong>
                    <span>Positive interactions</span>
                  </div>

                  <div>
                    <strong>
                      {analytics.unique_tracks ?? 0}
                    </strong>
                    <span>Unique tracks</span>
                  </div>
                </div>
              </div>

              <div className="analytics-panel">
                <h2>Recent feedback activity</h2>

                {analytics.recent_activity?.length > 0 ? (
                  <div className="activity-list">
                    {analytics.recent_activity.map(
                      (activity, index) => (
                        <div
                          className="activity-item"
                          key={`${activity.track_id}-${activity.created_at}-${index}`}
                        >
                          <div
                            className={`activity-icon ${activity.action}`}
                          >
                            {activity.action === "like" ? (
                              <ThumbsUp size={16} />
                            ) : activity.action === "dislike" ? (
                              <ThumbsDown size={16} />
                            ) : (
                              <Bookmark size={16} />
                            )}
                          </div>

                          <div className="activity-details">
                            <strong>
                              {activity.action.toUpperCase()}
                            </strong>
                            <span>{activity.track_id}</span>
                          </div>

                          <span className="activity-time">
                            {formatDate(activity.created_at)}
                          </span>
                        </div>
                      )
                    )}
                  </div>
                ) : (
                  <p>No recent feedback activity.</p>
                )}
              </div>
            </>
          )}
        </div>

        {/* EVALUATION METRICS */}

        <div className="analytics-panel evaluation-panel">
          <div className="section-heading">
            <div>
              <span className="eyebrow">
                <Sparkles size={14} />
                SYSTEM PERFORMANCE
              </span>

              <h2>Recommendation evaluation</h2>
            </div>

            <span className="ai-badge">LIVE METRICS</span>
          </div>

          {evaluationLoading && !evaluation ? (
            <p>Loading recommendation evaluation...</p>
          ) : !evaluation ? (
            <div className="empty-state">
              <TrendingUp size={30} />
              <h3>Evaluation data is waiting</h3>
              <p>
                Load recommendation performance statistics
                from the SONORA backend.
              </p>

              <button
                className="search-button"
                onClick={fetchEvaluation}
              >
                Load evaluation data
              </button>
            </div>
          ) : (
            <>
              <div className="stats-grid">
                <div className="stat-card">
                  <Search size={23} />
                  <h2>{evaluation.total_queries ?? 0}</h2>
                  <p>Total queries</p>
                </div>

                <div className="stat-card">
                  <AudioWaveform size={23} />
                  <h2>
                    {Number(
                      evaluation.average_response_time_ms || 0
                    ).toFixed(2)}
                    <small> ms</small>
                  </h2>
                  <p>Average response time</p>
                </div>

                <div className="stat-card">
                  <Compass size={23} />
                  <h2>{discoveryQueries}</h2>
                  <p>Discovery queries</p>
                </div>

                <div className="stat-card">
                  <Headphones size={23} />
                  <h2>{familiarQueries}</h2>
                  <p>Familiar queries</p>
                </div>
              </div>

              {/* MODE USAGE */}

              <div className="analytics-panel">
                <h2>Recommendation mode usage</h2>

                <p className="page-subtitle">
                  Distribution of Familiar and Discovery requests.
                </p>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: "15px",
                    margin: "22px 0 10px",
                    flexWrap: "wrap",
                  }}
                >
                  <strong>
                    Discovery — {discoveryQueries} (
                    {discoveryPercentage.toFixed(1)}%)
                  </strong>

                  <strong>
                    Familiar — {familiarQueries} (
                    {familiarPercentage.toFixed(1)}%)
                  </strong>
                </div>

                <div
                  style={{
                    height: "13px",
                    width: "100%",
                    display: "flex",
                    overflow: "hidden",
                    borderRadius: "20px",
                    background: "rgba(255,255,255,0.08)",
                  }}
                >
                  <div
                    style={{
                      width: `${discoveryPercentage}%`,
                      background: "#9b7cff",
                      transition: "width 0.4s ease",
                    }}
                  />

                  <div
                    style={{
                      width: `${familiarPercentage}%`,
                      background: "#42d6bd",
                      transition: "width 0.4s ease",
                    }}
                  />
                </div>

                <div className="analytics-extra">
                  <div>
                    <strong>
                      {discoveryPercentage.toFixed(2)}%
                    </strong>
                    <span>Discovery usage</span>
                  </div>

                  <div>
                    <strong>
                      {familiarPercentage.toFixed(2)}%
                    </strong>
                    <span>Familiar usage</span>
                  </div>
                </div>
              </div>

              {/* RECENT QUERIES */}

              <div className="analytics-panel">
                <h2>Recent recommendation queries</h2>

                <p className="page-subtitle">
                  Latest searches processed by the recommendation engine.
                </p>

                {evaluation.recent_queries?.length > 0 ? (
                  <div className="activity-list">
                    {evaluation.recent_queries.map(
                      (item, index) => (
                        <div
                          className="activity-item"
                          key={`${item.created_at}-${index}`}
                          style={{ alignItems: "flex-start" }}
                        >
                          <div className="activity-icon">
                            {item.mode === "discovery" ? (
                              <Compass size={17} />
                            ) : (
                              <Headphones size={17} />
                            )}
                          </div>

                          <div
                            className="activity-details"
                            style={{ flex: 1 }}
                          >
                            <strong>{item.query}</strong>

                            <span>
                              {item.mode?.toUpperCase()} MODE
                              {" · "}
                              {item.recommendation_count} recommendations
                            </span>

                            <span>
                              {Number(
                                item.response_time_ms || 0
                              ).toFixed(2)} ms
                            </span>

                            <span>
                              {formatDate(item.created_at)}
                            </span>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                ) : (
                  <p>No recommendation queries recorded yet.</p>
                )}
              </div>

              {/* TRANSPARENCY NOTE */}
                            <div
                style={{
                  padding: "18px",
                  borderRadius: "14px",
                  background: "rgba(155,124,255,0.08)",
                  border: "1px solid rgba(155,124,255,0.2)",
                  marginTop: "20px",
                }}
              >
                <strong>
                  <Sparkles
                    size={15}
                    style={{
                      display: "inline",
                      marginRight: "7px",
                    }}
                  />
                  Performance measurement
                </strong>

                <p
                  style={{
                    color: "#aaa8bd",
                    fontSize: "13px",
                    lineHeight: 1.7,
                    marginTop: "8px",
                  }}
                >
                  Response time measures how quickly the
                  recommendation API responds. Mode usage measures
                  how often each recommendation mode is requested.
                  These metrics do not represent recommendation
                  accuracy or user satisfaction.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    );
  };

  // ---------------------------------------
  // PAGE RENDERING
  // ---------------------------------------

  const renderPage = () => {
    switch (activePage) {
      case "Discover":
        return DiscoverPage();

      case "SONORA More":
        return SonoraMorePage();

      case "For You":
        return ForYouPage();

      case "Saved":
        return SavedPage();

      case "My Taste":
        return TastePage();

      case "Analytics":
        return AnalyticsPage();

      default:
        return DiscoverPage();
    }
  };

  // ---------------------------------------
  // MAIN RETURN
  // ---------------------------------------

  return (
    <div className="app-container">

      {/* SIDEBAR */}

      <aside
        className={`sidebar ${mobileMenu ? "mobile-open" : ""}`}
      >
        <div className="brand">
          <div className="brand-icon">
            <AudioWaveform size={26} />
          </div>

          <div>
            <h2>SONORA</h2>
            <span>AI MUSIC INTELLIGENCE</span>
          </div>

          <button
            className="close-menu"
            onClick={() => setMobileMenu(false)}
          >
            <X size={20} />
          </button>
        </div>

        <div className="sidebar-section">
          <span className="sidebar-label">MENU</span>

          {navigation.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.name}
                className={`nav-item ${
                  activePage === item.name ? "nav-active" : ""
                }`}
                onClick={() => handleNavigation(item.name)}
              >
                <Icon size={19} />
                <span>{item.name}</span>

                {activePage === item.name && (
                  <div className="nav-indicator" />
                )}
              </button>
            );
          })}
        </div>

        <div className="sidebar-bottom">
          <div className="sidebar-promo">
            <Sparkles size={20} />

            <h3>Music without limits.</h3>

            <p>
              Go beyond familiar sounds and discover
              something unexpected.
            </p>

            <button
              onClick={() => {
                setActivePage("Discover");
                setMode("discovery");
              }}
            >
              Explore now <ChevronRight size={15} />
            </button>
          </div>

          <div className="profile">
            <div className="profile-avatar">S</div>

            <div>
              <h4>Demo Listener</h4>
              <p>Free account</p>
            </div>

            <div className="profile-status" />
          </div>
        </div>
      </aside>

      {/* MAIN AREA */}

      <main className="main-content">
        <header className="topbar">
          <button
            className="mobile-menu-button"
            onClick={() => setMobileMenu(true)}
          >
            <Menu size={23} />
          </button>

          <div className="breadcrumb">
            <span>SONORA AI</span>
            <ChevronRight size={15} />
            <strong>{activePage}</strong>
          </div>

          <div className="topbar-right">
            <span className="online-indicator" />
            <span>AI Engine Ready</span>
            <div className="topbar-avatar">S</div>
          </div>
        </header>

        <div className="page-content">
          {renderPage()}
        </div>
      </main>

      {/* HTML AUDIO ELEMENT — streams licensed Jamendo catalogue tracks */}
      <audio
        ref={audioRef}
        preload="none"
        onTimeUpdate={(event) => {
          const nextSecond = Math.floor(event.currentTarget.currentTime || 0);
          setPlaybackTime((previous) => (previous === nextSecond ? previous : nextSecond));
        }}
        onLoadedMetadata={(event) => setAudioDuration(event.currentTarget.duration || 0)}
        onEnded={handleTrackEnded}
        onError={() => {
          setIsPlaying(false);
          showToast("This Jamendo stream is unavailable. Try another track.");
        }}
      />

      {/* REAL JAMENDO MUSIC PLAYER */}

      <footer className="music-player">
        <div className="player-track">
          {currentTrack && (
            <>
              <img
                src={currentTrack.image}
                alt={currentTrack.title}
              />

              <div>
                <h4>{currentTrack.title}</h4>
                <p>{currentTrack.artist}</p>
                {currentTrack.audioSource === "Jamendo" && currentTrack.jamendoUrl && (
                  <a
                    href={currentTrack.jamendoUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="jamendo-attribution"
                  >
                    Listen on Jamendo
                  </a>
                )}
                {currentTrack.audioSource === "Jamendo" && currentTrack.licenseUrl && (
                  <a
                    href={currentTrack.licenseUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="jamendo-attribution"
                    style={{ marginLeft: "8px" }}
                  >
                    Track licence
                  </a>
                )}
              </div>

              <button
                onClick={() => handleLike(currentTrack)}
                className={
                  likedTracks.includes(currentTrack.id)
                    ? "active-action"
                    : ""
                }
              >
                <Heart size={18} />
              </button>
            </>
          )}
        </div>

        <div className="player-controls">
          <div className="control-buttons">
            <button onClick={() => skipTrack(-1)} title="Previous recommendation">
              <SkipBack size={19} />
            </button>

            <button
              className="main-play-button"
              onClick={() => {
                if (!currentTrack?.audioUrl) {
                  playTrack(currentTrack);
                } else {
                  setIsPlaying((playing) => !playing);
                }
              }}
              disabled={isLoadingAudio}
              title={isPlaying ? "Pause" : "Play"}
            >
              {isLoadingAudio ? (
                <span className="player-loading-dot">•••</span>
              ) : isPlaying ? (
                <Pause size={19} fill="currentColor" />
              ) : (
                <Play size={19} fill="currentColor" />
              )}
            </button>

            <button onClick={() => skipTrack(1)} title="Next recommendation">
              <SkipForward size={19} />
            </button>
          </div>

          <div className="player-progress">
            <span>{formatTime(playbackTime)}</span>
            <input
              className="player-seek"
              type="range"
              min="0"
              max={audioDuration || 0}
              step="0.1"
              value={Math.min(playbackTime, audioDuration || 0)}
              onChange={handleSeek}
              aria-label="Track progress"
              disabled={!audioDuration}
            />
            <span>{formatTime(audioDuration) || currentTrack?.duration || "0:00"}</span>
          </div>
        </div>

        <div className="player-extra">
          <button className={shuffleEnabled ? "active-action" : ""} onClick={() => setShuffleEnabled((value) => !value)} title="Toggle shuffle" aria-label="Toggle shuffle"><Shuffle size={17} /></button>
          <button className={repeatMode !== "off" ? "active-action" : ""} onClick={() => setRepeatMode((modeValue) => modeValue === "off" ? "all" : modeValue === "all" ? "one" : "off")} title={`Repeat: ${repeatMode}`} aria-label="Change repeat mode"><Repeat size={17} /><small>{repeatMode === "one" ? "1" : ""}</small></button>
          <button className={queueOpen ? "active-action" : ""} onClick={() => setQueueOpen((value) => !value)} title="Open playback queue" aria-label="Open playback queue"><ListMusic size={18} />{playQueue.length}</button>
          <Radio size={19} />
          <Volume2 size={19} />
          <input
            className="player-volume"
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={volume}
            onChange={(event) => setVolume(Number(event.target.value))}
            aria-label="Volume"
          />
        </div>
      </footer>

      {queueOpen && (
        <section className="sonora-queue-panel" style={{ position: "fixed", right: 22, bottom: 112, zIndex: 250, width: "min(360px, calc(100vw - 32px))", maxHeight: "55vh", overflowY: "auto", padding: 18, border: "1px solid rgba(255,255,255,.12)", borderRadius: 16, background: "#141625", boxShadow: "0 18px 55px rgba(0,0,0,.5)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}><strong>Playback queue ({playQueue.length})</strong><button onClick={() => setQueueOpen(false)} aria-label="Close queue"><X size={18}/></button></div>
          {playQueue.length ? playQueue.map((item, index) => <div key={`${item.id}-${index}`} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 0", borderTop: "1px solid rgba(255,255,255,.07)" }}><img src={item.image} alt="" style={{ width: 38, height: 38, objectFit: "cover", borderRadius: 7 }}/><div style={{ flex: 1, minWidth: 0 }}><strong style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.title}</strong><small>{item.artist}</small></div><button onClick={() => { setPlayQueue((items) => items.filter((_, i) => i !== index)); }} title="Remove from queue"><X size={16}/></button></div>) : <p style={{ color: "#a5a6ba", fontSize: 13 }}>Your queue is empty. Add tracks using the queue icon on a track card.</p>}
          <button className="search-button" style={{ marginTop: 12 }} onClick={() => setPlayQueue([])} disabled={!playQueue.length}>Clear queue</button>
        </section>
      )}

      {/* TRACK DETAILS MODAL */}

      {selectedTrack && (
        <div
          className="modal-overlay"
          onClick={() => setSelectedTrack(null)}
        >
          <div
            className="track-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              className="modal-close"
              onClick={() => setSelectedTrack(null)}
            >
              <X size={21} />
            </button>

            <span className="eyebrow">
              <Sparkles size={14} />
              SONORA AI EXPLANATION
            </span>

            <img
              src={selectedTrack.image}
              alt={selectedTrack.title}
            />

            <h2>{selectedTrack.title}</h2>

            <p className="modal-artist">
              {selectedTrack.artist}
            </p>

            <div className="modal-explanation">
              <h3>Why this recommendation?</h3>
              <p>{selectedTrack.explanation}</p>
            </div>

            <div className="modal-semantic">
              <span>GENERATED SEMANTIC ID</span>

              <strong>
                {selectedTrack.semanticId || "AI-GENERATED"}
              </strong>
            </div>

            <button
              className="search-button modal-save"
              onClick={() => {
                handleSave(selectedTrack);
                setSelectedTrack(null);
              }}
            >
              <Bookmark size={17} />
              Save this track
            </button>
          </div>
        </div>
      )}

      {/* TOAST */}

      {toast && (
        <div className="toast-message">
          <Sparkles size={17} />
          {toast}
        </div>
      )}
    </div>
  );
}

export default App;