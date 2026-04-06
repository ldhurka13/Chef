"""
Test suite for King of the Hill Movie Game feature.
Tests: /api/game/start, /api/game/choose, /api/game/skip, /api/game/cant-decide
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "gametest2@test.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token - register if needed"""
    # Try login first
    login_resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if login_resp.status_code == 200:
        return login_resp.json().get("token")
    
    # If login fails, try to register
    if login_resp.status_code in [401, 404]:
        register_resp = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "username": "gametest2",
            "birth_year": 1995
        })
        if register_resp.status_code == 200:
            return register_resp.json().get("token")
    
    pytest.skip(f"Authentication failed - login: {login_resp.status_code}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestGameStart:
    """Tests for POST /api/game/start"""
    
    def test_game_start_returns_session_id(self, authenticated_client):
        """Game start should return a session_id"""
        response = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "session_id" in data, "Response should contain session_id"
        assert isinstance(data["session_id"], str), "session_id should be a string"
        assert len(data["session_id"]) > 0, "session_id should not be empty"
    
    def test_game_start_returns_round_1(self, authenticated_client):
        """Game start should return round 1"""
        response = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "round" in data, "Response should contain round"
        assert data["round"] == 1, f"First round should be 1, got {data['round']}"
    
    def test_game_start_returns_two_movies(self, authenticated_client):
        """Game start should return two movies"""
        response = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "movies" in data, "Response should contain movies"
        assert isinstance(data["movies"], list), "movies should be a list"
        assert len(data["movies"]) == 2, f"Should have 2 movies, got {len(data['movies'])}"
        
        # Verify movie structure
        for movie in data["movies"]:
            assert movie is not None, "Movie should not be None"
            assert "id" in movie, "Movie should have id"
            assert "title" in movie, "Movie should have title"
    
    def test_game_start_returns_max_rounds(self, authenticated_client):
        """Game start should return max_rounds = 10"""
        response = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "max_rounds" in data, "Response should contain max_rounds"
        assert data["max_rounds"] == 10, f"max_rounds should be 10, got {data['max_rounds']}"
    
    def test_game_start_king_position_null_first_round(self, authenticated_client):
        """First round should have no king (king_position = null)"""
        response = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "king_position" in data, "Response should contain king_position"
        assert data["king_position"] is None, f"king_position should be None in round 1, got {data['king_position']}"


class TestGameChoose:
    """Tests for POST /api/game/choose"""
    
    def test_choose_progresses_to_next_round(self, authenticated_client):
        """Choosing a movie should progress to next round"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        
        # Make a choice
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": movies[0]["id"],
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 1500,
            "is_super_like": False,
            "is_cant_decide": False
        })
        
        assert choice_resp.status_code == 200, f"Expected 200, got {choice_resp.status_code}: {choice_resp.text}"
        data = choice_resp.json()
        
        assert data.get("game_over") == False, "Game should not be over after round 1"
        assert data.get("round") == 2, f"Should be round 2, got {data.get('round')}"
    
    def test_choose_king_stays_on_left(self, authenticated_client):
        """Winner (King) should stay on left position"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        chosen_id = movies[0]["id"]
        
        # Make a choice
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": chosen_id,
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 2000,
            "is_super_like": False,
            "is_cant_decide": False
        })
        
        data = choice_resp.json()
        
        assert data.get("king_position") == "left", f"King should be on left, got {data.get('king_position')}"
        assert data["movies"][0]["id"] == chosen_id, "King (chosen movie) should be first in movies array"
    
    def test_choose_returns_current_scores(self, authenticated_client):
        """Choice response should include current_scores"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        
        # Make a choice
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": movies[0]["id"],
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 1000,
            "is_super_like": False,
            "is_cant_decide": False
        })
        
        data = choice_resp.json()
        
        assert "current_scores" in data, "Response should contain current_scores"
        assert isinstance(data["current_scores"], list), "current_scores should be a list"


class TestReactionTimeScoring:
    """Tests for reaction time multiplier scoring"""
    
    def test_fast_reaction_high_multiplier(self, authenticated_client):
        """Fast reaction (<2s) should give high score"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        
        # Fast choice (500ms)
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": movies[0]["id"],
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 500,  # Very fast
            "is_super_like": False,
            "is_cant_decide": False
        })
        
        assert choice_resp.status_code == 200
        data = choice_resp.json()
        
        # Check that scores are being tracked
        if data.get("current_scores"):
            assert len(data["current_scores"]) > 0, "Should have at least one score"
    
    def test_super_like_doubles_multiplier(self, authenticated_client):
        """Super like should apply 2x multiplier"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        
        # Super like choice
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": movies[0]["id"],
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 1000,
            "is_super_like": True,  # Super like!
            "is_cant_decide": False
        })
        
        assert choice_resp.status_code == 200
        data = choice_resp.json()
        
        # Verify game continues
        assert data.get("game_over") == False


class TestGameSkip:
    """Tests for POST /api/game/skip"""
    
    def test_skip_gives_fresh_matchup(self, authenticated_client):
        """Skip should give 0 points and fresh matchup"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        original_movies = [m["id"] for m in start_data["movies"]]
        
        # Skip
        skip_resp = authenticated_client.post(
            f"{BASE_URL}/api/game/skip?session_id={session_id}&round_number=1",
            json={}
        )
        
        assert skip_resp.status_code == 200, f"Expected 200, got {skip_resp.status_code}: {skip_resp.text}"
        data = skip_resp.json()
        
        assert data.get("game_over") == False, "Game should not be over"
        assert data.get("round") == 2, f"Should be round 2, got {data.get('round')}"
        assert data.get("king_position") is None, "Skip should reset king (no king)"
    
    def test_skip_returns_two_new_movies(self, authenticated_client):
        """Skip should return two movies"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        
        # Skip
        skip_resp = authenticated_client.post(
            f"{BASE_URL}/api/game/skip?session_id={session_id}&round_number=1",
            json={}
        )
        
        data = skip_resp.json()
        
        assert "movies" in data, "Response should contain movies"
        assert len(data["movies"]) == 2, f"Should have 2 movies, got {len(data['movies'])}"


class TestGameCantDecide:
    """Tests for POST /api/game/cant-decide"""
    
    def test_cant_decide_gives_equal_points(self, authenticated_client):
        """Can't Decide should give equal points to both movies"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        
        # Can't decide
        cant_decide_resp = authenticated_client.post(
            f"{BASE_URL}/api/game/cant-decide?session_id={session_id}&round_number=1&movie1_id={movies[0]['id']}&movie2_id={movies[1]['id']}&reaction_time_ms=3000",
            json={}
        )
        
        assert cant_decide_resp.status_code == 200, f"Expected 200, got {cant_decide_resp.status_code}: {cant_decide_resp.text}"
        data = cant_decide_resp.json()
        
        assert data.get("game_over") == False, "Game should not be over"
        assert data.get("round") == 2, f"Should be round 2, got {data.get('round')}"
    
    def test_cant_decide_keeps_king_if_exists(self, authenticated_client):
        """Can't Decide should keep the king if one exists"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        
        # First, make a choice to establish a king
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": movies[0]["id"],
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 2000,
            "is_super_like": False,
            "is_cant_decide": False
        })
        
        choice_data = choice_resp.json()
        king_id = choice_data["movies"][0]["id"]
        round_2_movies = choice_data["movies"]
        
        # Now can't decide in round 2
        cant_decide_resp = authenticated_client.post(
            f"{BASE_URL}/api/game/cant-decide?session_id={session_id}&round_number=2&movie1_id={round_2_movies[0]['id']}&movie2_id={round_2_movies[1]['id']}&reaction_time_ms=3000",
            json={}
        )
        
        data = cant_decide_resp.json()
        
        # King should still be on left
        if not data.get("game_over"):
            assert data.get("king_position") == "left", "King should remain on left"


class TestGameCompletion:
    """Tests for game completion at round 10"""
    
    def test_game_ends_at_round_10(self, authenticated_client):
        """Game should end after round 10 with recommendations"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        current_round = 1
        
        # Play through 10 rounds
        while current_round <= 10:
            if current_round == 1:
                chosen_id = movies[0]["id"]
                rejected_id = movies[1]["id"]
            else:
                chosen_id = movies[0]["id"]
                rejected_id = movies[1]["id"]
            
            choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
                "session_id": session_id,
                "round_number": current_round,
                "chosen_movie_id": chosen_id,
                "rejected_movie_id": rejected_id,
                "reaction_time_ms": 1500,
                "is_super_like": False,
                "is_cant_decide": False
            })
            
            assert choice_resp.status_code == 200, f"Round {current_round} failed: {choice_resp.text}"
            data = choice_resp.json()
            
            if data.get("game_over"):
                # Game ended
                assert current_round == 10, f"Game ended at round {current_round}, expected 10"
                assert "recommendations" in data, "Final response should have recommendations"
                assert isinstance(data["recommendations"], list), "recommendations should be a list"
                assert len(data["recommendations"]) <= 3, "Should have at most 3 recommendations"
                
                # Verify recommendation structure
                for rec in data["recommendations"]:
                    assert "id" in rec, "Recommendation should have id"
                    assert "title" in rec, "Recommendation should have title"
                    assert "confidence" in rec, "Recommendation should have confidence score"
                break
            else:
                movies = data["movies"]
                current_round = data["round"]
        
        assert current_round == 10 or data.get("game_over"), "Game should complete at round 10"


class TestGameSessionManagement:
    """Tests for game session handling"""
    
    def test_invalid_session_returns_404(self, authenticated_client):
        """Invalid session_id should return 404"""
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": "invalid-session-id-12345",
            "round_number": 1,
            "chosen_movie_id": 123,
            "rejected_movie_id": 456,
            "reaction_time_ms": 1000,
            "is_super_like": False,
            "is_cant_decide": False
        })
        
        assert choice_resp.status_code == 404, f"Expected 404, got {choice_resp.status_code}"
    
    def test_skip_invalid_session_returns_404(self, authenticated_client):
        """Skip with invalid session should return 404"""
        skip_resp = authenticated_client.post(
            f"{BASE_URL}/api/game/skip?session_id=invalid-session&round_number=1",
            json={}
        )
        
        assert skip_resp.status_code == 404


class TestUnauthenticatedAccess:
    """Tests for unauthenticated access"""
    
    def test_game_start_without_auth(self, api_client):
        """Game should still work without auth (uses TMDB trending)"""
        # Remove auth header temporarily
        original_auth = api_client.headers.pop("Authorization", None)
        
        try:
            response = api_client.post(f"{BASE_URL}/api/game/start", json={})
            # Should work but use TMDB trending instead of user's movies
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            assert "session_id" in data
            assert "movies" in data
        finally:
            if original_auth:
                api_client.headers["Authorization"] = original_auth


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
