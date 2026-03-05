"""
Letterboxd Import Feature Tests
Tests for ZIP and CSV import functionality - diary entries, watchlist, rating conversion, LB badge (source field)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestLetterboxdImport:
    """Tests for the Letterboxd ZIP/CSV import feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create a unique test user for each test"""
        self.timestamp = int(time.time() * 1000)
        self.email = f"lbtest_{self.timestamp}@example.com"
        self.password = "test1234"
        self.username = f"lbtest_{self.timestamp}"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Register user
        reg_resp = self.session.post(f"{BASE_URL}/api/auth/register", json={
            "email": self.email,
            "password": self.password,
            "username": self.username,
            "birth_year": 1990
        })
        assert reg_resp.status_code == 200, f"Registration failed: {reg_resp.text}"
        self.token = reg_resp.json().get("token")
        self.user_id = reg_resp.json().get("user", {}).get("id")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        
        # Cleanup: delete watch history and watchlist for this user
        try:
            # Get and delete all diary entries
            diary_resp = self.session.get(f"{BASE_URL}/api/user/watch-history")
            if diary_resp.status_code == 200:
                for item in diary_resp.json() or []:
                    self.session.delete(f"{BASE_URL}/api/user/watch-history/{item['tmdb_id']}")
            
            # Get and delete all watchlist items
            wl_resp = self.session.get(f"{BASE_URL}/api/user/watchlist")
            if wl_resp.status_code == 200:
                for item in wl_resp.json() or []:
                    self.session.delete(f"{BASE_URL}/api/user/watchlist/{item['tmdb_id']}")
        except:
            pass

    # ============ ZIP IMPORT TESTS ============
    
    def test_zip_import_accepts_zip_file(self):
        """POST /api/auth/import-letterboxd accepts .zip files"""
        zip_path = "/tmp/letterboxd_test.zip"
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            # Remove content-type for multipart
            resp = requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        assert resp.status_code == 200, f"ZIP import failed: {resp.text}"
        data = resp.json()
        assert "stats" in data, "Response should contain stats"
        print(f"ZIP import response: {data}")

    def test_zip_import_creates_diary_entries_from_ratings(self):
        """Zip import parses ratings.csv and creates diary entries"""
        zip_path = "/tmp/letterboxd_test.zip"
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        assert resp.status_code == 200, f"Import failed: {resp.text}"
        
        # Check diary was populated
        diary_resp = self.session.get(f"{BASE_URL}/api/user/watch-history")
        assert diary_resp.status_code == 200
        diary = diary_resp.json() or []
        
        # ratings.csv has: Fight Club (4.5), Parasite (5), Whiplash (5)
        # At least 3 diary entries should be created
        assert len(diary) >= 3, f"Expected at least 3 diary entries, got {len(diary)}"
        
        # Check titles are present (Fight Club, Parasite, Whiplash)
        titles = [item.get("title", "").lower() for item in diary]
        assert any("fight club" in t for t in titles), "Fight Club should be in diary"
        assert any("parasite" in t for t in titles), "Parasite should be in diary"
        assert any("whiplash" in t for t in titles), "Whiplash should be in diary"

    def test_zip_import_converts_5_star_to_10_point_rating(self):
        """Letterboxd 5-star ratings are converted to 10-point scale (multiply by 2)"""
        zip_path = "/tmp/letterboxd_test.zip"
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        diary_resp = self.session.get(f"{BASE_URL}/api/user/watch-history")
        diary = diary_resp.json() or []
        
        # Find Fight Club (rated 4.5 on Letterboxd = 9.0 on our scale)
        fight_club = next((d for d in diary if "fight club" in d.get("title", "").lower()), None)
        if fight_club:
            assert fight_club.get("user_rating") == 9.0, f"Fight Club rating should be 9.0 (4.5*2), got {fight_club.get('user_rating')}"
        
        # Find Parasite (rated 5 on Letterboxd = 10.0 on our scale)
        parasite = next((d for d in diary if "parasite" in d.get("title", "").lower()), None)
        if parasite:
            assert parasite.get("user_rating") == 10.0, f"Parasite rating should be 10.0 (5*2), got {parasite.get('user_rating')}"

    def test_zip_import_merges_reviews_as_comments(self):
        """Reviews from reviews.csv are merged as comments on diary entries"""
        zip_path = "/tmp/letterboxd_test.zip"
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        diary_resp = self.session.get(f"{BASE_URL}/api/user/watch-history")
        diary = diary_resp.json() or []
        
        # Find Fight Club - should have review "First rule of Fight Club..."
        fight_club = next((d for d in diary if "fight club" in d.get("title", "").lower()), None)
        if fight_club:
            watches = fight_club.get("watches", [])
            has_comment = any(w.get("comment") and "fight club" in w.get("comment", "").lower() for w in watches)
            assert has_comment, f"Fight Club should have review comment, got watches: {watches}"

    def test_zip_import_creates_watchlist_entries(self):
        """Zip import processes watchlist.csv and creates watchlist entries"""
        zip_path = "/tmp/letterboxd_test.zip"
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        wl_resp = self.session.get(f"{BASE_URL}/api/user/watchlist")
        assert wl_resp.status_code == 200
        watchlist = wl_resp.json() or []
        
        # watchlist.csv has: Eternal Sunshine, The Godfather
        assert len(watchlist) >= 2, f"Expected at least 2 watchlist items, got {len(watchlist)}"
        
        titles = [item.get("title", "").lower() for item in watchlist]
        assert any("eternal sunshine" in t for t in titles), "Eternal Sunshine should be in watchlist"
        assert any("godfather" in t for t in titles), "The Godfather should be in watchlist"

    def test_zip_import_sets_source_letterboxd_on_diary(self):
        """All imported diary entries have source='letterboxd' field"""
        zip_path = "/tmp/letterboxd_test.zip"
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        diary_resp = self.session.get(f"{BASE_URL}/api/user/watch-history")
        diary = diary_resp.json() or []
        
        for item in diary:
            # Either the item or its watches should have source="letterboxd"
            has_source = item.get("source") == "letterboxd" or \
                         any(w.get("source") == "letterboxd" for w in item.get("watches", []))
            assert has_source, f"Diary item {item.get('title')} should have source='letterboxd'"

    def test_zip_import_sets_source_letterboxd_on_watchlist(self):
        """All imported watchlist entries have source='letterboxd' field"""
        zip_path = "/tmp/letterboxd_test.zip"
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        wl_resp = self.session.get(f"{BASE_URL}/api/user/watchlist")
        watchlist = wl_resp.json() or []
        
        for item in watchlist:
            assert item.get("source") == "letterboxd", f"Watchlist item {item.get('title')} should have source='letterboxd'"

    def test_zip_import_idempotent_no_duplicates(self):
        """Re-importing the same ZIP skips already imported items (idempotent)"""
        zip_path = "/tmp/letterboxd_test.zip"
        
        # First import
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            resp1 = requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        assert resp1.status_code == 200
        stats1 = resp1.json().get("stats", {})
        diary_added_1 = stats1.get("diary_added", 0)
        watchlist_added_1 = stats1.get("watchlist_added", 0)
        
        # Second import (same file)
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            resp2 = requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        assert resp2.status_code == 200
        stats2 = resp2.json().get("stats", {})
        
        # Second import should have mostly skipped items
        diary_added_2 = stats2.get("diary_added", 0) + stats2.get("diary_updated", 0)
        skipped_2 = stats2.get("skipped", 0)
        
        # Most items should be skipped on second import
        print(f"First import: {stats1}")
        print(f"Second import: {stats2}")
        assert skipped_2 > 0, f"Second import should skip items, got skipped={skipped_2}"

    def test_zip_import_returns_stats(self):
        """Import returns detailed stats: diary_added, watchlist_added, skipped"""
        zip_path = "/tmp/letterboxd_test.zip"
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        assert "stats" in data, "Response should contain stats"
        stats = data["stats"]
        
        # Check required stat fields exist
        assert "diary_added" in stats, "Stats should have diary_added"
        assert "watchlist_added" in stats, "Stats should have watchlist_added"
        assert "skipped" in stats, "Stats should have skipped"
        assert "total_processed" in stats, "Stats should have total_processed"

    # ============ CSV IMPORT TESTS (Legacy) ============
    
    def test_csv_import_still_works(self):
        """POST /api/auth/import-letterboxd still accepts .csv files (legacy)"""
        # Create a simple CSV file
        csv_content = "Name,Year,Rating,WatchedDate\nInception,2010,5,2024-01-01\n"
        
        files = {'file': ('ratings.csv', csv_content.encode(), 'text/csv')}
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        assert resp.status_code == 200, f"CSV import failed: {resp.text}"
        data = resp.json()
        assert data.get("total", 0) >= 1 or "stats" in data, f"CSV import should return count or stats"

    def test_import_rejects_invalid_file_type(self):
        """Import rejects non-CSV and non-ZIP files"""
        files = {'file': ('test.txt', b'invalid content', 'text/plain')}
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        assert resp.status_code == 400, f"Should reject .txt files, got {resp.status_code}"

    def test_import_requires_authentication(self):
        """Import endpoint requires authentication"""
        zip_path = "/tmp/letterboxd_test.zip"
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            # No auth header
            resp = requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files)
        
        assert resp.status_code == 401, f"Should return 401 without auth, got {resp.status_code}"

    # ============ API RESPONSE TESTS ============
    
    def test_watch_history_returns_source_field(self):
        """GET /api/user/watch-history returns source field on letterboxd entries"""
        zip_path = "/tmp/letterboxd_test.zip"
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        diary_resp = self.session.get(f"{BASE_URL}/api/user/watch-history")
        diary = diary_resp.json() or []
        
        # At least one entry should have source field
        has_source = any(
            item.get("source") == "letterboxd" or 
            any(w.get("source") == "letterboxd" for w in item.get("watches", []))
            for item in diary
        )
        assert has_source, "At least one diary entry should have source='letterboxd'"

    def test_watchlist_returns_source_field(self):
        """GET /api/user/watchlist returns source field on letterboxd entries"""
        zip_path = "/tmp/letterboxd_test.zip"
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        wl_resp = self.session.get(f"{BASE_URL}/api/user/watchlist")
        watchlist = wl_resp.json() or []
        
        # All imported items should have source field
        assert len(watchlist) > 0, "Should have watchlist items"
        for item in watchlist:
            assert item.get("source") == "letterboxd", f"Watchlist item should have source='letterboxd'"


class TestLetterboxdDataEndpoint:
    """Tests for the /api/auth/letterboxd-data endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.timestamp = int(time.time() * 1000)
        self.email = f"lbdata_{self.timestamp}@example.com"
        self.password = "test1234"
        self.username = f"lbdata_{self.timestamp}"
        self.session = requests.Session()
        
        # Register user
        reg_resp = self.session.post(f"{BASE_URL}/api/auth/register", json={
            "email": self.email,
            "password": self.password,
            "username": self.username,
            "birth_year": 1990
        })
        assert reg_resp.status_code == 200
        self.token = reg_resp.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield

    def test_letterboxd_data_returns_not_connected_initially(self):
        """GET /api/auth/letterboxd-data returns connected=false for new user"""
        resp = self.session.get(f"{BASE_URL}/api/auth/letterboxd-data")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("connected") == False, "New user should not have letterboxd connected"

    def test_letterboxd_data_returns_connected_after_import(self):
        """GET /api/auth/letterboxd-data returns connected=true after import"""
        zip_path = "/tmp/letterboxd_test.zip"
        with open(zip_path, 'rb') as f:
            files = {'file': ('letterboxd-export.zip', f, 'application/zip')}
            headers = {"Authorization": f"Bearer {self.token}"}
            requests.post(f"{BASE_URL}/api/auth/import-letterboxd", files=files, headers=headers)
        
        resp = self.session.get(f"{BASE_URL}/api/auth/letterboxd-data")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("connected") == True, "Should be connected after import"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
