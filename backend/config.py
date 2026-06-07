"""
Application configuration and environment variables.
"""
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# TMDB Configuration
TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/"

# Streaming Availability API (Movies of the Night)
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')
STREAMING_API_BASE = "https://streaming-availability.p.rapidapi.com"
ALLOWED_SERVICES = {"netflix", "prime", "disney", "hulu", "apple", "hbo", "paramount"}

# Resend email config
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))

# Cache settings
CACHE_TTL = 3600  # 1 hour

# CORS Origins
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
