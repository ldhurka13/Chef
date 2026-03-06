"""Import IMDB movie data from zip of CSVs into MongoDB movies collection."""
import csv
import io
import zipfile
import os
import re
import ast
from pymongo import MongoClient, UpdateOne, TEXT
from datetime import datetime

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "chef_db")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

def parse_list_field(val):
    """Parse stringified Python list or comma-separated string into a list."""
    if not val or val.strip() in ("", "[]", "nan"):
        return []
    val = val.strip()
    # Try ast.literal_eval for Python list format like "['a', 'b']"
    if val.startswith("["):
        try:
            result = ast.literal_eval(val)
            if isinstance(result, list):
                return [str(x).strip() for x in result if x]
        except (ValueError, SyntaxError):
            pass
    # Fallback: comma-separated
    return [x.strip() for x in val.split(",") if x.strip()]

def parse_money(val):
    """Parse money string like '$200,000,000' into integer."""
    if not val or val.strip() in ("", "nan", "-"):
        return None
    val = val.strip().replace(",", "").replace("$", "").replace("£", "").replace("€", "")
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None

def parse_float(val):
    if not val or val.strip() in ("", "nan", "-"):
        return None
    try:
        return float(val.strip())
    except (ValueError, TypeError):
        return None

def parse_int(val):
    if not val or val.strip() in ("", "nan", "-"):
        return None
    val = val.strip().replace(",", "")
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None

def clean_title(title):
    """Remove leading number prefix like '1. ' from titles."""
    if not title:
        return ""
    return re.sub(r'^\d+\.\s*', '', title.strip())

def normalize_row(row):
    """Convert a raw CSV row into a normalized movie document."""
    title = clean_title(row.get("Title", ""))
    if not title:
        return None
    
    year = parse_int(row.get("Year"))
    imdb_rating = parse_float(row.get("Rating"))
    
    # Extract IMDB ID from Movie Link
    movie_link = (row.get("Movie Link") or "").strip()
    imdb_id = ""
    match = re.search(r'(tt\d+)', movie_link)
    if match:
        imdb_id = match.group(1)
    
    # Parse duration - extract minutes
    duration_raw = (row.get("Duration") or "").strip()
    duration_min = None
    # Handle formats like "142", "2h 22m", "142 min"
    h_match = re.search(r'(\d+)\s*h', duration_raw)
    m_match = re.search(r'(\d+)\s*m', duration_raw)
    if h_match or m_match:
        hours = int(h_match.group(1)) if h_match else 0
        mins = int(m_match.group(1)) if m_match else 0
        duration_min = hours * 60 + mins
    elif duration_raw.isdigit():
        duration_min = int(duration_raw)
    
    genres = parse_list_field(row.get("genres"))
    directors = parse_list_field(row.get("directors"))
    writers = parse_list_field(row.get("writers"))
    stars = parse_list_field(row.get("stars"))
    languages = parse_list_field(row.get("Languages"))
    countries = parse_list_field(row.get("countries_origin"))
    
    doc = {
        "title": title,
        "title_lower": title.lower(),
        "year": year,
        "duration_min": duration_min,
        "mpa": (row.get("MPA") or "").strip() or None,
        "imdb_rating": imdb_rating,
        "imdb_votes": parse_int(row.get("Votes")),
        "meta_score": parse_float(row.get("méta_score") or row.get("meta_score")),
        "description": (row.get("description") or "").strip() or None,
        "imdb_id": imdb_id or None,
        "imdb_url": movie_link or None,
        "directors": directors,
        "writers": writers,
        "stars": stars,
        "budget": parse_money(row.get("budget")),
        "opening_weekend_gross": parse_money(row.get("opening_weekend_Gross")),
        "gross_worldwide": parse_money(row.get("grossWorldWWide") or row.get("grossWorldWide")),
        "gross_us_canada": parse_money(row.get("gross_US_Canada")),
        "release_date": (row.get("release_date") or "").strip() or None,
        "countries": countries,
        "filming_locations": (row.get("filming_locations") or "").strip() or None,
        "production_companies": parse_list_field(row.get("production_company")),
        "awards": (row.get("awards_content") or "").strip() or None,
        "genres": genres,
        "languages": languages,
        "source": "imdb_dataset",
    }
    return doc

def import_zip(zip_path):
    zf = zipfile.ZipFile(zip_path)
    csvs = sorted([
        n for n in zf.namelist()
        if n.endswith(".csv") and not n.startswith("__MACOSX") and "merged" in n.lower()
    ])
    
    print(f"Found {len(csvs)} CSV files to import")
    
    total_imported = 0
    total_skipped = 0
    bulk_ops = []
    
    for csv_path in csvs:
        raw = zf.read(csv_path)
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        
        reader = csv.DictReader(io.StringIO(text))
        file_count = 0
        
        for row in reader:
            doc = normalize_row(row)
            if not doc:
                total_skipped += 1
                continue
            
            # Upsert by title_lower + year (deduplicate)
            filter_key = {"title_lower": doc["title_lower"], "year": doc["year"]}
            bulk_ops.append(UpdateOne(filter_key, {"$set": doc}, upsert=True))
            file_count += 1
            
            # Flush in batches of 1000
            if len(bulk_ops) >= 1000:
                db.movies.bulk_write(bulk_ops, ordered=False)
                bulk_ops = []
        
        total_imported += file_count
        year_match = re.search(r'(\d{4})', csv_path)
        year_label = year_match.group(1) if year_match else "?"
        print(f"  {year_label}: {file_count} movies")
    
    # Flush remaining
    if bulk_ops:
        db.movies.bulk_write(bulk_ops, ordered=False)
    
    zf.close()
    
    print(f"\nTotal imported: {total_imported}, skipped: {total_skipped}")
    
    # Create indexes
    print("Creating indexes...")
    db.movies.create_index([("title_lower", 1), ("year", 1)], unique=True)
    db.movies.create_index([("title", TEXT)])
    db.movies.create_index("year")
    db.movies.create_index("imdb_rating")
    db.movies.create_index("genres")
    db.movies.create_index("directors")
    db.movies.create_index("stars")
    db.movies.create_index("imdb_id")
    db.movies.create_index("imdb_votes")
    print("Indexes created!")
    
    final_count = db.movies.count_documents({})
    print(f"Total movies in collection: {final_count}")
    return final_count

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/movies_data.zip"
    import_zip(path)
