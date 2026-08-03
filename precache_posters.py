# ============================================================
# High-Speed Poster Pre-Caching Pipeline
# precache_posters.py — Fetches real TMDB posters for dataset movies
# ============================================================

import os
import sys
import json
import re
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANED_DATASET_PATH = os.path.join(BASE_DIR, "dataset", "movies_cleaned.csv")
POSTER_CACHE_FILE = os.path.join(BASE_DIR, "dataset", "poster_cache.json")

TMDB_API_KEY = "75b5470bdcfc8fa8b4650421e30efec0"
TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

def load_cache():
    if os.path.exists(POSTER_CACHE_FILE):
        try:
            with open(POSTER_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache):
    try:
        os.makedirs(os.path.dirname(POSTER_CACHE_FILE), exist_ok=True)
        with open(POSTER_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARNING] Failed to save poster cache: {e}")

def fetch_poster_from_tmdb(movie_tuple):
    title, year = movie_tuple
    if not title:
        return title, year, None

    clean_t = str(title).strip()
    search_query = re.sub(r'\s*\(\d{4}\)', '', clean_t).split(':')[0].split('-')[0].strip()

    try:
        params = {"api_key": TMDB_API_KEY, "query": search_query}
        if year and str(year).isdigit() and int(year) > 1900:
            params["year"] = int(year)

        resp = requests.get(f"{TMDB_BASE}/search/movie", params=params, timeout=1.5)
        results = resp.json().get("results", [])

        if not results and "year" in params:
            del params["year"]
            resp = requests.get(f"{TMDB_BASE}/search/movie", params=params, timeout=1.5)
            results = resp.json().get("results", [])

        if not results:
            resp = requests.get(f"{TMDB_BASE}/search/tv", params=params, timeout=1.5)
            results = resp.json().get("results", [])

        if results:
            match = results[0]
            p_path = match.get("poster_path")
            if p_path:
                return title, year, {
                    "poster_url": f"{TMDB_IMG}{p_path}",
                    "backdrop_url": f"https://image.tmdb.org/t/p/original{match.get('backdrop_path')}" if match.get('backdrop_path') else "",
                    "title": clean_t,
                    "overview": match.get("overview", ""),
                    "rating": round(float(match.get("vote_average", 7.5)), 1)
                }
    except Exception:
        pass

    return title, year, None

def run_precaching():
    print("="*60)
    print("  Starting High-Speed TMDB Poster Pre-Caching Pipeline")
    print("="*60)

    if not os.path.exists(CLEANED_DATASET_PATH):
        print(f"[ERROR] {CLEANED_DATASET_PATH} not found.")
        return

    df = pd.read_csv(CLEANED_DATASET_PATH, low_memory=False)
    print(f"[INFO] Total dataset rows: {len(df):,}")

    cache = load_cache()
    print(f"[INFO] Current poster cache entries: {len(cache):,}")

    # Prioritize movies that need poster fetch (e.g. popular, top rated, regional languages)
    df['vote_count_val'] = pd.to_numeric(df.get('vote_count', 0), errors='coerce').fillna(0)
    df_sorted = df.sort_values(by=['vote_count_val'], ascending=False)

    candidates = []
    for _, row in df_sorted.iterrows():
        title = str(row.get('title', '')).strip()
        year = row.get('release_year')
        if not title:
            continue
        key = f"{title.lower()}_{int(year) if str(year).isdigit() else ''}"
        existing = cache.get(key)
        # Fetch if missing or if cached entry is not a real http poster
        if not existing or not (isinstance(existing, dict) and existing.get("poster_url", "").startswith("http")):
            candidates.append((title, year))

    print(f"[INFO] Found {len(candidates):,} candidate movies requiring poster pre-fetching.")

    # Process first 3,000 top candidate movies in parallel with 30 worker threads
    batch = candidates[:3000]
    print(f"[INFO] Pre-fetching top {len(batch):,} titles via TMDB API...")

    success_count = 0
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = executor.map(fetch_poster_from_tmdb, batch)
        for title, year, data in results:
            if data:
                key = f"{str(title).lower().strip()}_{int(year) if str(year).isdigit() else ''}"
                cache[key] = data
                success_count += 1
                if success_count % 100 == 0:
                    print(f"  • Pre-cached {success_count:,} TMDB posters...")

    save_cache(cache)
    print(f"\n[SUCCESS] Pre-caching complete! Successfully added {success_count:,} real TMDB posters.")
    print(f"[INFO] Total cached entries in poster_cache.json: {len(cache):,}")

if __name__ == "__main__":
    run_precaching()
