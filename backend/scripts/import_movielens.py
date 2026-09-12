"""
One-shot ETL: Load MovieLens ml-32m {links.csv, movies.csv, tags.csv}
into MongoDB collection `ml_movies` keyed by tmdb_id for fast lookup by the
profile-insights endpoint.

Document schema:
  {
    tmdb_id: int,
    ml_movie_id: int,
    genres: [str, ...],          # from movies.csv (pipe-split)
    top_tags: [{tag: str, count: int}]  # top-15 by frequency
  }

Run:  python /app/backend/scripts/import_movielens.py
"""
import csv
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

from pymongo import MongoClient, UpdateOne

# Bootstrap import path so backend .env is picked up
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv  # noqa: E402
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATA_DIR = Path("/app/data/movielens")
TOP_TAGS_PER_MOVIE = 15


def main():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = MongoClient(mongo_url)
    db = client[db_name]
    coll = db.ml_movies

    print("[1/4] Reading links.csv (movieId → tmdbId)…")
    ml_to_tmdb = {}
    with (DATA_DIR / "links.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tmdb = (row.get("tmdbId") or "").strip()
            if not tmdb:
                continue
            try:
                ml_to_tmdb[int(row["movieId"])] = int(tmdb)
            except (ValueError, TypeError):
                pass
    print(f"        ↳ {len(ml_to_tmdb):,} movies with tmdb_id")

    print("[2/4] Reading movies.csv (genres)…")
    ml_meta = {}
    with (DATA_DIR / "movies.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                mid = int(row["movieId"])
            except (ValueError, KeyError):
                continue
            if mid not in ml_to_tmdb:
                continue
            raw_genres = (row.get("genres") or "").strip()
            if raw_genres in ("", "(no genres listed)"):
                genres = []
            else:
                genres = [g.strip() for g in raw_genres.split("|") if g.strip()]
            ml_meta[mid] = {"genres": genres}
    print(f"        ↳ {len(ml_meta):,} movies with metadata")

    print("[3/4] Aggregating tags.csv (this file is ~70 MB)…")
    tag_counters = defaultdict(Counter)
    with (DATA_DIR / "tags.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                mid = int(row["movieId"])
            except (ValueError, KeyError):
                continue
            if mid not in ml_meta:
                continue
            tag = (row.get("tag") or "").strip().lower()
            if not tag:
                continue
            tag_counters[mid][tag] += 1
    print(f"        ↳ {len(tag_counters):,} movies with at least one tag")

    print("[4/4] Bulk-upserting into ml_movies…")
    ops = []
    for mid, meta in ml_meta.items():
        tmdb_id = ml_to_tmdb[mid]
        top = tag_counters.get(mid, Counter()).most_common(TOP_TAGS_PER_MOVIE)
        doc = {
            "tmdb_id": tmdb_id,
            "ml_movie_id": mid,
            "genres": meta["genres"],
            "top_tags": [{"tag": t, "count": c} for t, c in top],
        }
        ops.append(UpdateOne({"tmdb_id": tmdb_id}, {"$set": doc}, upsert=True))
        if len(ops) >= 2000:
            coll.bulk_write(ops, ordered=False)
            ops = []
    if ops:
        coll.bulk_write(ops, ordered=False)

    coll.create_index("tmdb_id", unique=True)
    coll.create_index("genres")
    print(f"        ↳ done. ml_movies has {coll.count_documents({}):,} docs")


if __name__ == "__main__":
    main()
