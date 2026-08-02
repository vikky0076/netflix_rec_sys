# ============================================================
# TMDB & OMDb API Integration Module
# tmdb_integration.py
# ============================================================
# Automatically handles:
#   1. TMDB & OMDb API authentication via environment variables (.env)
#   2. Movie search by Title and Release Year
#   3. Fetching high-resolution Poster URLs and Backdrop URLs
#   4. Robust URL parsing if full API query link is pasted in .env
#   5. Local disk caching in dataset/poster_cache.json
# ============================================================

import os
import sys
import re
import json
import requests
import urllib.parse
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTER_CACHE_FILE = os.path.join(BASE_DIR, "dataset", "poster_cache.json")

TMDB_BASE     = "https://api.themoviedb.org/3"
TMDB_IMG_W500 = "https://image.tmdb.org/t/p/w500"
TMDB_IMG_ORIG = "https://image.tmdb.org/t/p/original"
OMDB_BASE     = "http://www.omdbapi.com/"


def parse_api_key(raw_val: str, param_name: str = "apikey") -> str:
    """Extract clean API key string even if user pasted full URL into .env."""
    if not raw_val:
        return ""
    raw_val = raw_val.strip()
    if f"{param_name}=" in raw_val.lower():
        match = re.search(rf'{param_name}=([a-zA-Z0-9]+)', raw_val, re.IGNORECASE)
        if match:
            return match.group(1)
    return raw_val


TMDB_API_KEY = parse_api_key(os.getenv("TMDB_API_KEY", ""), "api_key")
OMDB_API_KEY = parse_api_key(os.getenv("OMDB_API_KEY", ""), "apikey")

# In-memory poster cache
POSTER_CACHE = {}


def load_cache():
    """Load poster cache from local disk file dataset/poster_cache.json."""
    global POSTER_CACHE
    if os.path.exists(POSTER_CACHE_FILE):
        try:
            with open(POSTER_CACHE_FILE, "r", encoding="utf-8") as f:
                POSTER_CACHE = json.load(f)
        except Exception:
            POSTER_CACHE = {}
    else:
        POSTER_CACHE = {}


def save_cache():
    """Save poster cache dict to local disk file dataset/poster_cache.json."""
    try:
        os.makedirs(os.path.dirname(POSTER_CACHE_FILE), exist_ok=True)
        cache_copy = dict(POSTER_CACHE)
        with open(POSTER_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_copy, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


load_cache()


def generate_svg_placeholder(title: str) -> str:
    """Generate a high-quality dark Netflix-style SVG poster card URI fallback."""
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


def fetch_tmdb_details(title: str, year: int = None) -> dict:
    """
    Search TMDB API & OMDb API for a movie by Title and optional Release Year.
    Checks dataset/poster_cache.json first.
    """
    if not title:
        return {"poster_url": generate_svg_placeholder("Movie"), "backdrop_url": ""}
    clean_t = title.strip()
    cache_key = f"{clean_t.lower()}_{year if year else ''}"

    tmdb_key = parse_api_key(os.getenv("TMDB_API_KEY", ""), "api_key")
    omdb_key = parse_api_key(os.getenv("OMDB_API_KEY", ""), "apikey")

    # Step 1: Check local disk cache (only return if poster_url is a real image URL, not SVG or mock broken URL)
    if cache_key in POSTER_CACHE and POSTER_CACHE[cache_key]:
        val = POSTER_CACHE[cache_key]
        cached_poster = ""
        if isinstance(val, dict):
            cached_poster = val.get("poster_url", "")
        elif isinstance(val, str):
            cached_poster = val

        is_svg = cached_poster.startswith("data:image/svg+xml")
        is_dummy_mock = any(cached_poster.endswith(x) for x in ["pushpa.jpg", "pushpa2.jpg", "manjummel.jpg", "premalu.jpg", "aavesham.jpg", "kgf1.jpg", "kgf2.jpg", "kantara.jpg", "dangal.jpg", "3idiots.jpg", "12thfail.jpg", "baahubali.jpg"])

        if cached_poster and cached_poster.startswith("http") and not is_svg and not is_dummy_mock:
            if isinstance(val, dict):
                return val
            else:
                return {"poster_url": cached_poster, "backdrop_url": ""}

    fetched_poster = None
    fetched_backdrop = ""
    fetched_overview = ""
    fetched_rating = 7.5

    # Step 2: TMDB API Lookup
    if tmdb_key:
        try:
            params = {"api_key": tmdb_key, "query": clean_t}
            if year and int(year) > 1900:
                params["year"] = int(year)

            resp = requests.get(f"{TMDB_BASE}/search/movie", params=params, timeout=2.5)
            results = resp.json().get("results", [])

            if not results:
                resp = requests.get(f"{TMDB_BASE}/search/tv", params=params, timeout=2.5)
                results = resp.json().get("results", [])

            # Fallback with sanitized title (stripping parenthetical year / subtitle)
            if not results:
                clean_query = re.sub(r'\s*\(\d{4}\)', '', clean_t).split(':')[0].strip()
                if clean_query and clean_query != clean_t:
                    resp = requests.get(f"{TMDB_BASE}/search/movie", params={"api_key": tmdb_key, "query": clean_query}, timeout=2.5)
                    results = resp.json().get("results", [])
                    if not results:
                        resp = requests.get(f"{TMDB_BASE}/search/tv", params={"api_key": tmdb_key, "query": clean_query}, timeout=2.5)
                        results = resp.json().get("results", [])

            if results:
                match = results[0]
                p_path = match.get("poster_path")
                b_path = match.get("backdrop_path")

                if p_path:
                    fetched_poster = f"{TMDB_IMG_W500}{p_path}"
                if b_path:
                    fetched_backdrop = f"{TMDB_IMG_ORIG}{b_path}"
                fetched_overview = match.get("overview", "")
                fetched_rating = round(float(match.get("vote_average", 7.5)), 1)
        except Exception as e:
            print(f"[WARNING] TMDB API fetch failed for '{clean_t}': {e}")

    # Step 3: OMDb API Lookup if TMDB returned no poster
    if not fetched_poster and omdb_key:
        try:
            params = {"apikey": omdb_key, "t": clean_t}
            if year and int(year) > 1900:
                params["y"] = int(year)

            resp = requests.get(OMDB_BASE, params=params, timeout=3.5)
            data = resp.json()
            if data.get("Response") == "True" and data.get("Poster") and data.get("Poster") != "N/A":
                fetched_poster = data["Poster"]
                if not fetched_overview:
                    fetched_overview = data.get("Plot", "")
                if data.get("imdbRating") and data["imdbRating"] != "N/A":
                    try:
                        fetched_rating = float(data["imdbRating"])
                    except:
                        pass
                print(f"[SUCCESS] OMDb fetched poster for '{clean_t}': {fetched_poster}")
        except Exception as e:
            print(f"[WARNING] OMDb API fetch failed for '{clean_t}': {e}")

    # Step 4: Base64 SVG Fallback if both APIs return no poster
    if not fetched_poster:
        fetched_poster = generate_svg_placeholder(clean_t)

    res_dict = {
        "poster_url": fetched_poster,
        "backdrop_url": fetched_backdrop,
        "title": clean_t,
        "overview": fetched_overview,
        "rating": fetched_rating
    }

    POSTER_CACHE[cache_key] = res_dict
    save_cache()
    return res_dict


def fetch_tmdb_poster_url(title: str, year: int = None) -> str:
    """Convenience helper returning poster URL string."""
    details = fetch_tmdb_details(title, year)
    return details.get("poster_url", generate_svg_placeholder(title))


def fetch_trending_tmdb_movies() -> list:
    """Fetch live daily trending movies from TMDB API if key is present."""
    tmdb_key = parse_api_key(os.getenv("TMDB_API_KEY", ""), "api_key")
    if not tmdb_key:
        return []

    try:
        resp = requests.get(f"{TMDB_BASE}/trending/movie/day", params={"api_key": tmdb_key}, timeout=3.5)
        results = resp.json().get("results", [])

        trending_list = []
        for m in results[:15]:
            p_path = m.get("poster_path")
            b_path = m.get("backdrop_path")
            trending_list.append({
                "title": m.get("title", ""),
                "original_title": m.get("original_title", m.get("title", "")),
                "overview": m.get("overview", ""),
                "poster_url": f"{TMDB_IMG_W500}{p_path}" if p_path else generate_svg_placeholder(m.get("title")),
                "backdrop_url": f"{TMDB_IMG_ORIG}{b_path}" if b_path else "",
                "release_year": int(m.get("release_date", "2024").split("-")[0]) if m.get("release_date") else 2024,
                "rating": round(float(m.get("vote_average", 7.5)), 1),
                "vote_count": int(m.get("vote_count", 1000)),
                "language": m.get("original_language", "en").upper(),
                "genres": "Trending, Action",
                "type": "Movie"
            })
        return trending_list
    except Exception as e:
        print(f"[WARNING] TMDB Trending fetch failed: {e}")
        return []


if __name__ == "__main__":
    print("[TEST] TMDB & OMDb API Integration Module")
    res = fetch_tmdb_details("Vikram", 2022)
    print(f"  • Title: {res.get('title')}")
    print(f"  • Poster URL: {res.get('poster_url')[:80]}...")
