# ============================================================
# Streaming AI Movie Recommendation Web App
# app.py — Backend, Poster Caching Pipeline & API Entry Point
# ============================================================

import os
import json
import requests
import urllib.parse
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file securely
load_dotenv()

# ── Import upgraded streaming recommender engine & TMDB integration ──
from recommendation import NetflixRecommender
from tmdb_integration import fetch_tmdb_poster_url, fetch_tmdb_details, fetch_trending_tmdb_movies

# ─────────────────────────────────────────────────────────────
# Configuration & API Keys
# ─────────────────────────────────────────────────────────────
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "").strip()

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG  = "https://image.tmdb.org/t/p/w500"
OMDB_BASE = "http://www.omdbapi.com/"

# Disk Cache Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTER_CACHE_FILE = os.path.join(BASE_DIR, "dataset", "poster_cache.json")

# ─────────────────────────────────────────────────────────────
# Local Disk Poster Caching System
# ─────────────────────────────────────────────────────────────
POSTER_CACHE = {}

def load_poster_cache():
    """Load poster cache from disk file."""
    global POSTER_CACHE
    if os.path.exists(POSTER_CACHE_FILE):
        try:
            with open(POSTER_CACHE_FILE, "r", encoding="utf-8") as f:
                POSTER_CACHE = json.load(f)
            print(f"[INFO] Local poster cache loaded: {len(POSTER_CACHE):,} entries.")
        except Exception as e:
            print(f"[WARNING] Error reading poster cache file: {e}")
            POSTER_CACHE = {}
    else:
        POSTER_CACHE = {}

def save_poster_cache():
    """Persist poster cache dict to disk file."""
    try:
        os.makedirs(os.path.dirname(POSTER_CACHE_FILE), exist_ok=True)
        with open(POSTER_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(POSTER_CACHE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARNING] Failed to save poster cache to disk: {e}")

load_poster_cache()

# ─────────────────────────────────────────────────────────────
# Flask Application Setup
# ─────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "antigravity_netflix_streaming_secret_key_2026")
CORS(app)

# ─────────────────────────────────────────────────────────────
# Load Recommendation Engine
# ─────────────────────────────────────────────────────────────
print("\n" + "="*65)
print("  AI Movie Streaming Platform Backend — Starting...")
print("="*65)

try:
    recommender = NetflixRecommender()
    ALL_TITLES  = recommender.df["title"].tolist()
    print(f"[INFO] Streaming Engine ready. Active Dataset: {len(ALL_TITLES):,} titles.")
except Exception as e:
    print(f"[ERROR] Failed to load recommender engine: {e}")
    recommender = None
    ALL_TITLES  = []


# ─────────────────────────────────────────────────────────────
# High-Quality Default SVG Placeholder Generator (Base64 Encoded)
# ─────────────────────────────────────────────────────────────
def generate_svg_placeholder(title: str) -> str:
    """Generate a premium dark Netflix-style SVG poster card URI fallback."""
    clean_t = (title or "Movie").replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    first_char = clean_t[0].upper() if clean_t else "M"
    disp_title = clean_t[:20] + "..." if len(clean_t) > 20 else clean_t

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1a1a24"/>
      <stop offset="50%" stop-color="#121218"/>
      <stop offset="100%" stop-color="#0a0a0d"/>
    </linearGradient>
    <linearGradient id="red" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#E50914"/>
      <stop offset="100%" stop-color="#b20710"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#bg)"/>
  <circle cx="150" cy="180" r="65" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="8"/>
  <circle cx="150" cy="180" r="50" fill="none" stroke="url(#red)" stroke-width="3" opacity="0.85"/>
  <text x="150" y="200" font-family="sans-serif" font-size="54" font-weight="900" fill="#ffffff" text-anchor="middle" opacity="0.95">{first_char}</text>
  <rect x="25" y="320" width="250" height="2" fill="url(#red)"/>
  <text x="150" y="358" font-family="sans-serif" font-size="17" font-weight="800" fill="#ffffff" text-anchor="middle">{disp_title}</text>
  <text x="150" y="388" font-family="sans-serif" font-size="11" font-weight="700" fill="#808088" letter-spacing="2" text-anchor="middle">STREAMING PLATFORM</text>
</svg>'''
    import base64
    b64_str = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64_str}"


# ─────────────────────────────────────────────────────────────
# 3-Tier Poster Fetching Pipeline (Cache -> TMDB -> OMDb -> SVG)
# ─────────────────────────────────────────────────────────────
def fetch_poster(title: str, year: int = None) -> str:
    """
    Delegate poster fetching to TMDB integration pipeline
    with local disk caching and OMDb/SVG fallback.
    """
    return fetch_tmdb_poster_url(title, year)


def get_movie_poster(m: dict) -> str:
    """Get valid poster URL from dict or POSTER_CACHE instantly."""
    if not m:
        return ""
    raw_p = str(m.get("poster_url") or m.get("poster") or "").strip()
    if raw_p and raw_p.lower() not in ["nan", "none", "null"] and raw_p.startswith("http"):
        return raw_p

    title = str(m.get("title") or "").strip()
    year = m.get("release_year")
    cache_key = f"{title.lower()}_{year if year else ''}"

    if cache_key in POSTER_CACHE and POSTER_CACHE[cache_key]:
        val = POSTER_CACHE[cache_key]
        p_url = val.get("poster_url", "") if isinstance(val, dict) else str(val)
        if p_url:
            m["poster"] = p_url
            m["poster_url"] = p_url
            return p_url

    p_url = fetch_poster(title, year)
    m["poster"] = p_url
    m["poster_url"] = p_url
    return p_url

def hydrate_posters(movie_list: list) -> list:
    """Ensure every movie dict in a list has a valid poster URL populated instantly."""
    if not movie_list:
        return movie_list

    for m in movie_list:
        m["poster"] = get_movie_poster(m)

    return movie_list


# ─────────────────────────────────────────────────────────────
# Search History Helpers
# ─────────────────────────────────────────────────────────────
def get_user_history() -> list:
    if "search_history" not in session:
        session["search_history"] = []
    return session["search_history"]

def add_user_history(movie_title: str):
    history = get_user_history()
    t_clean = movie_title.strip()
    if t_clean in history:
        history.remove(t_clean)
    history.append(t_clean)
    session["search_history"] = history[-15:]
    session.modified = True


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Homepage: Dynamic streaming interface with language and genre filters."""
    lang_filter = request.args.get("lang", "All").strip()
    genre_filter = request.args.get("genre", "All").strip()
    history = get_user_history()

    if recommender is None:
        return render_template("index.html", hero=None, recommended=[], trending=[], popular=[], selected_lang=lang_filter, selected_genre=genre_filter, history=history)

    hero_movie  = recommender.get_featured_hero_movie(lang_filter=lang_filter, genre_filter=genre_filter)
    recommended = recommender.get_personalized_recommendations(history, lang_filter=lang_filter, genre_filter=genre_filter, n=12)
    trending    = recommender.get_trending_movies(lang_filter=lang_filter, genre_filter=genre_filter, n=12)
    popular     = recommender.get_popular_movies(lang_filter=lang_filter, genre_filter=genre_filter, n=12)

    if hero_movie:
        hero_movie["poster"] = get_movie_poster(hero_movie)
    hydrate_posters(recommended)
    hydrate_posters(trending)
    hydrate_posters(popular)

    return render_template(
        "index.html",
        hero=hero_movie,
        recommended=recommended,
        trending=trending,
        popular=popular,
        selected_lang=lang_filter,
        selected_genre=genre_filter,
        history=history,
        total_titles=len(ALL_TITLES)
    )


@app.route("/search")
def search_page():
    """Dedicated YouTube-style mobile & desktop search page."""
    lang_filter = request.args.get("lang", "All").strip()
    query = request.args.get("q", "").strip()
    history = get_user_history()
    return render_template(
        "search.html",
        query=query,
        history=history,
        selected_lang=lang_filter
    )


@app.route("/recommend")
def recommend():
    """Results page: Recommendations for searched movie with history context & filters."""
    movie = request.args.get("movie", "").strip()
    lang_filter = request.args.get("lang", "All").strip()
    genre_filter = request.args.get("genre", "All").strip()
    top_n = min(max(int(request.args.get("top_n", 10)), 1), 50)

    if not movie:
        return redirect(url_for("index"))

    if recommender is None:
        return render_template("results.html", error="Recommendation service unavailable.", query=movie, results=[], query_movie=None, selected_lang=lang_filter, selected_genre=genre_filter)

    add_user_history(movie)
    history = get_user_history()

    results, query_movie = recommender.get_recommendations(
        movie, top_n=top_n, lang_filter=lang_filter, genre_filter=genre_filter, search_history=history
    )

    if results is None:
        return render_template(
            "results.html",
            error=f'<strong>"{movie}"</strong> was not found in our database. '
                  f'Try searching titles like <em>"Vikram"</em>, <em>"RRR"</em>, <em>"Manjummel Boys"</em>, or <em>"Inception"</em>.',
            query=movie, results=[], query_movie=None, selected_lang=lang_filter, selected_genre=genre_filter
        )

    if query_movie:
        query_movie["poster"] = get_movie_poster(query_movie)

    hydrate_posters(results)

    return render_template(
        "results.html",
        results=results,
        query=movie,
        query_movie=query_movie,
        selected_lang=lang_filter,
        selected_genre=genre_filter,
        history=history
    )


@app.route("/history")
def history():
    """Full Page Search History view with hydrated movie cards."""
    raw_history = get_user_history()
    history_items = []

    if recommender and raw_history:
        for title in reversed(raw_history):
            idx = recommender.find_movie_idx(title)
            if idx is not None:
                row = recommender.df.iloc[idx]
                m_dict = recommender._row_to_dict(row)
                m_dict["poster"] = get_movie_poster(m_dict)
                history_items.append(m_dict)
            else:
                history_items.append({
                    "title": title,
                    "poster": fetch_poster(title),
                    "language": "Movie",
                    "rating": "8.0",
                    "release_year": "2024",
                    "genres": "AI Recommended"
                })

    return render_template(
        "history.html",
        history_items=history_items,
        raw_history=raw_history,
        history=raw_history
    )


@app.route("/api/filter")
def api_filter():
    """AJAX Endpoint: Dynamic section updates when switching language/genre filters."""
    lang_filter = request.args.get("lang", "All").strip()
    genre_filter = request.args.get("genre", "All").strip()
    history = get_user_history()

    if recommender is None:
        return jsonify({"error": "Recommender unavailable"}), 503

    hero_movie  = recommender.get_featured_hero_movie(lang_filter=lang_filter, genre_filter=genre_filter)
    recommended = recommender.get_personalized_recommendations(history, lang_filter=lang_filter, genre_filter=genre_filter, n=12)
    trending    = recommender.get_trending_movies(lang_filter=lang_filter, genre_filter=genre_filter, n=12)
    popular     = recommender.get_popular_movies(lang_filter=lang_filter, genre_filter=genre_filter, n=12)

    if hero_movie:
        hero_movie["poster"] = get_movie_poster(hero_movie)
    hydrate_posters(recommended)
    hydrate_posters(trending)
    hydrate_posters(popular)

    return jsonify({
        "lang": lang_filter,
        "genre": genre_filter,
        "hero": hero_movie,
        "recommended": recommended,
        "trending": trending,
        "popular": popular
    })


@app.route("/api/recommend")
def api_recommend():
    """JSON API endpoint for movie recommendations."""
    movie = request.args.get("movie", "").strip()
    lang_filter = request.args.get("lang", "All").strip()
    top_n = min(max(int(request.args.get("top_n", 10)), 1), 50)

    if not movie:
        return jsonify({"error": "No movie name provided"}), 400
    if recommender is None:
        return jsonify({"error": "Recommender service unavailable"}), 503

    history = get_user_history()
    results, query_movie = recommender.get_recommendations(movie, top_n=top_n, lang_filter=lang_filter, search_history=history)

    if results is None:
        return jsonify({"error": f'"{movie}" not found in the dataset'}), 404

    return jsonify({
        "query":       movie,
        "query_movie": query_movie,
        "count":       len(results),
        "results":     results,
    })


@app.route("/api/poster")
def api_poster():
    """Poster Lookup API Endpoint (Cache -> TMDB -> OMDb -> SVG fallback)."""
    title = request.args.get("title", "")
    year  = request.args.get("year", "")
    poster = fetch_poster(title, int(year) if year.isdigit() else None)
    return jsonify({"poster_url": poster})


@app.route("/api/search")
def api_search():
    """Autocomplete API with poster thumbnails."""
    q = request.args.get("q", "").strip().lower()
    lang = request.args.get("lang", "All").strip().lower()

    if len(q) < 2:
        return jsonify([])

    matches = []
    count = 0

    df_subset = recommender.df
    if lang != "all":
        df_subset = recommender.df[recommender.df["language"].str.lower() == lang]

    for _, row in df_subset.iterrows():
        title = str(row.get("title", ""))
        orig_title = str(row.get("original_title", ""))

        if q in title.lower() or q in orig_title.lower():
            poster = fetch_poster(title, row.get("release_year"))
            matches.append({
                "title": title,
                "original_title": orig_title,
                "release_year": int(row.get("release_year", 2020)),
                "language": str(row.get("language", "English")),
                "rating": round(float(row.get("rating_val", 7.5)), 1),
                "genres": str(row.get("genres", "")),
                "poster": poster
            })
            count += 1
            if count >= 10:
                break

    return jsonify(matches)


@app.route("/api/history", methods=["GET", "DELETE"])
def api_history():
    """Manage search history."""
    if request.method == "DELETE":
        session["search_history"] = []
        session.modified = True
        return jsonify({"message": "Search history cleared", "history": []})

    return jsonify({"history": get_user_history()})


# ─────────────────────────────────────────────────────────────
# Run Flask Server
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n[INFO] Starting Flask server at http://127.0.0.1:5000")
    print("[INFO] Press Ctrl+C to stop.\n")
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5000)
