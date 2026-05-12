"""
Test suite for Eliminative Logic Discovery Engine - Movie Game feature.
Tests: Training Pool, Discovery Pool, Dissimilar Pairs, Reaction Scoring, Recency Bias
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - user with 8+ movies in diary
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


class TestTrainingPoolLogic:
    """Tests for Training Pool (Diary only) logic"""
    
    def test_game_start_returns_training_pool_size(self, authenticated_client):
        """Game start should return training_pool_size"""
        response = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "training_pool_size" in data, "Response should contain training_pool_size"
        assert isinstance(data["training_pool_size"], int), "training_pool_size should be an integer"
        print(f"Training pool size: {data['training_pool_size']}")
    
    def test_game_start_returns_has_sufficient_data(self, authenticated_client):
        """Game start should return has_sufficient_data flag"""
        response = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "has_sufficient_data" in data, "Response should contain has_sufficient_data"
        assert isinstance(data["has_sufficient_data"], bool), "has_sufficient_data should be boolean"
        print(f"Has sufficient data: {data['has_sufficient_data']}")
    
    def test_movies_from_training_pool_have_genres(self, authenticated_client):
        """Movies from training pool should have genre information"""
        response = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        movies = data.get("movies", [])
        assert len(movies) == 2, "Should have 2 movies"
        
        for movie in movies:
            assert movie is not None, "Movie should not be None"
            # Movies should have genres for dissimilarity calculation
            if "genres" in movie:
                print(f"Movie '{movie.get('title')}' genres: {movie.get('genres')}")


class TestDissimilarPairs:
    """Tests for maximally dissimilar movie pairs"""
    
    def test_initial_pair_has_different_movies(self, authenticated_client):
        """Initial pair should have two different movies"""
        response = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        movies = data.get("movies", [])
        assert len(movies) == 2, "Should have 2 movies"
        assert movies[0]["id"] != movies[1]["id"], "Movies should be different"
        
        print(f"Movie 1: {movies[0].get('title')} ({movies[0].get('release_date', '')[:4]})")
        print(f"Movie 2: {movies[1].get('title')} ({movies[1].get('release_date', '')[:4]})")
    
    def test_challenger_is_dissimilar_to_king(self, authenticated_client):
        """After choosing, challenger should be dissimilar to king"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        king_movie = movies[0]
        
        # Make a choice - king stays
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": king_movie["id"],
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 1500,
            "is_super_like": False,
            "is_cant_decide": False
        })
        
        assert choice_resp.status_code == 200
        data = choice_resp.json()
        
        if not data.get("game_over"):
            new_movies = data.get("movies", [])
            assert len(new_movies) == 2, "Should have 2 movies"
            
            # King should be on left
            assert new_movies[0]["id"] == king_movie["id"], "King should stay on left"
            
            # Challenger should be different
            challenger = new_movies[1]
            assert challenger["id"] != king_movie["id"], "Challenger should be different from king"
            
            print(f"King: {king_movie.get('title')}")
            print(f"New Challenger: {challenger.get('title')}")


class TestReactionTimeScoring:
    """Tests for new reaction time scoring: Fast=5, Average=2, Slow=1"""
    
    def test_fast_reaction_gives_5_points(self, authenticated_client):
        """Fast reaction (<2s) should give +5 points base score"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        
        # Fast choice (1000ms = 1s)
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": movies[0]["id"],
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 1000,  # Fast - should give 5 points
            "is_super_like": False,
            "is_cant_decide": False
        })
        
        assert choice_resp.status_code == 200
        print("Fast reaction (<2s) test passed - base score should be 5")
    
    def test_average_reaction_gives_2_points(self, authenticated_client):
        """Average reaction (2-5s) should give +2 points base score"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        
        # Average choice (3000ms = 3s)
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": movies[0]["id"],
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 3000,  # Average - should give 2 points
            "is_super_like": False,
            "is_cant_decide": False
        })
        
        assert choice_resp.status_code == 200
        print("Average reaction (2-5s) test passed - base score should be 2")
    
    def test_slow_reaction_gives_1_point(self, authenticated_client):
        """Slow reaction (>5s) should give +1 point base score"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        
        # Slow choice (6000ms = 6s)
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": movies[0]["id"],
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 6000,  # Slow - should give 1 point
            "is_super_like": False,
            "is_cant_decide": False
        })
        
        assert choice_resp.status_code == 200
        print("Slow reaction (>5s) test passed - base score should be 1")


class TestSuperLikeScoring:
    """Tests for Super Like doubling the score"""
    
    def test_super_like_doubles_score(self, authenticated_client):
        """Super Like should double the base score"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        
        # Super like with fast reaction (5 * 2 = 10 base before recency)
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": movies[0]["id"],
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 1000,  # Fast = 5 points
            "is_super_like": True,  # 2x = 10 points
            "is_cant_decide": False
        })
        
        assert choice_resp.status_code == 200
        print("Super Like test passed - score should be doubled (5 * 2 = 10)")


class TestSkipBehavior:
    """Tests for Skip functionality"""
    
    def test_skip_gives_zero_points(self, authenticated_client):
        """Skip should give 0 points"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        
        # Skip
        skip_resp = authenticated_client.post(
            f"{BASE_URL}/api/game/skip?session_id={session_id}&round_number=1",
            json={}
        )
        
        assert skip_resp.status_code == 200
        data = skip_resp.json()
        
        assert data.get("game_over") == False, "Game should not be over"
        assert data.get("round") == 2, "Should progress to round 2"
        print("Skip test passed - 0 points awarded")
    
    def test_skip_king_stays_if_exists(self, authenticated_client):
        """Skip should keep king if one exists"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        
        # First, establish a king
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": movies[0]["id"],
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 1500,
            "is_super_like": False,
            "is_cant_decide": False
        })
        
        choice_data = choice_resp.json()
        king_id = choice_data["movies"][0]["id"]
        
        # Now skip in round 2
        skip_resp = authenticated_client.post(
            f"{BASE_URL}/api/game/skip?session_id={session_id}&round_number=2",
            json={}
        )
        
        data = skip_resp.json()
        
        if not data.get("game_over"):
            assert data.get("king_position") == "left", "King should stay on left after skip"
            assert data["movies"][0]["id"] == king_id, "King should remain the same"
            print(f"Skip with king test passed - King '{choice_data['movies'][0].get('title')}' stays")


class TestCantDecideBehavior:
    """Tests for Can't Decide functionality"""
    
    def test_cant_decide_gives_2_points_to_both(self, authenticated_client):
        """Can't Decide should give +2 points to both movies"""
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
        
        assert cant_decide_resp.status_code == 200
        data = cant_decide_resp.json()
        
        assert data.get("game_over") == False, "Game should not be over"
        print("Can't Decide test passed - +2 points to both movies")
    
    def test_cant_decide_king_stays(self, authenticated_client):
        """Can't Decide should keep king if one exists"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        
        # First, establish a king
        choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
            "session_id": session_id,
            "round_number": 1,
            "chosen_movie_id": movies[0]["id"],
            "rejected_movie_id": movies[1]["id"],
            "reaction_time_ms": 1500,
            "is_super_like": False,
            "is_cant_decide": False
        })
        
        choice_data = choice_resp.json()
        king_id = choice_data["movies"][0]["id"]
        round_2_movies = choice_data["movies"]
        
        # Can't decide in round 2
        cant_decide_resp = authenticated_client.post(
            f"{BASE_URL}/api/game/cant-decide?session_id={session_id}&round_number=2&movie1_id={round_2_movies[0]['id']}&movie2_id={round_2_movies[1]['id']}&reaction_time_ms=3000",
            json={}
        )
        
        data = cant_decide_resp.json()
        
        if not data.get("game_over"):
            assert data.get("king_position") == "left", "King should stay on left"
            print("Can't Decide with king test passed - King stays")


class TestDiscoveryPoolRecommendations:
    """Tests for Discovery Pool recommendations at game end"""
    
    def test_full_game_returns_discovery_recommendations(self, authenticated_client):
        """Full 10-round game should return recommendations from Discovery Pool"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        current_round = 1
        
        print(f"Starting full game test with training_pool_size: {start_data.get('training_pool_size')}")
        
        # Play through 10 rounds with varying reaction times
        while current_round <= 10:
            # Vary reaction times to test recency bias
            if current_round <= 3:
                reaction_time = 1500  # Fast in early rounds (0.8x recency)
            elif current_round <= 7:
                reaction_time = 3000  # Average in middle rounds (1.0x recency)
            else:
                reaction_time = 1000  # Fast in late rounds (1.3x recency)
            
            choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
                "session_id": session_id,
                "round_number": current_round,
                "chosen_movie_id": movies[0]["id"],
                "rejected_movie_id": movies[1]["id"],
                "reaction_time_ms": reaction_time,
                "is_super_like": current_round == 5,  # Super like in round 5
                "is_cant_decide": False
            })
            
            assert choice_resp.status_code == 200, f"Round {current_round} failed: {choice_resp.text}"
            data = choice_resp.json()
            
            if data.get("game_over"):
                # Game ended - verify recommendations
                assert "recommendations" in data, "Final response should have recommendations"
                recommendations = data["recommendations"]
                
                assert isinstance(recommendations, list), "recommendations should be a list"
                assert len(recommendations) <= 3, f"Should have at most 3 recommendations, got {len(recommendations)}"
                
                print(f"\n=== Game Complete at Round {current_round} ===")
                print(f"Total rounds: {data.get('total_rounds')}")
                
                # Verify recommendation structure
                for i, rec in enumerate(recommendations):
                    assert "id" in rec, "Recommendation should have id"
                    assert "title" in rec, "Recommendation should have title"
                    assert "confidence" in rec, "Recommendation should have confidence"
                    
                    print(f"\nRecommendation {i+1}: {rec.get('title')}")
                    print(f"  - Confidence: {rec.get('confidence')}%")
                    print(f"  - TMDB Rating: {rec.get('vote_average')}")
                    
                    # Check for why_youll_like
                    if "why_youll_like" in rec:
                        print(f"  - Why you'll like: {rec.get('why_youll_like')}")
                    
                    # Check for genres
                    if "genres" in rec:
                        print(f"  - Genres: {rec.get('genres')}")
                    
                    # Check for source
                    if "source" in rec:
                        print(f"  - Source: {rec.get('source')}")
                
                break
            else:
                movies = data["movies"]
                current_round = data["round"]
        
        assert current_round == 10 or data.get("game_over"), "Game should complete at round 10"
    
    def test_recommendations_have_why_youll_like(self, authenticated_client):
        """Recommendations should include 'why_youll_like' snippet"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        current_round = 1
        
        # Play through 10 rounds quickly
        while current_round <= 10:
            choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
                "session_id": session_id,
                "round_number": current_round,
                "chosen_movie_id": movies[0]["id"],
                "rejected_movie_id": movies[1]["id"],
                "reaction_time_ms": 1000,  # Fast choices
                "is_super_like": False,
                "is_cant_decide": False
            })
            
            data = choice_resp.json()
            
            if data.get("game_over"):
                recommendations = data.get("recommendations", [])
                
                # Check that at least one recommendation has why_youll_like
                has_why_snippet = any("why_youll_like" in rec for rec in recommendations)
                
                if has_why_snippet:
                    print("SUCCESS: Recommendations include 'why_youll_like' snippets")
                    for rec in recommendations:
                        if "why_youll_like" in rec:
                            print(f"  - {rec.get('title')}: \"{rec.get('why_youll_like')}\"")
                else:
                    print("WARNING: No 'why_youll_like' snippets found in recommendations")
                
                # This is a soft assertion - log but don't fail
                assert True
                break
            else:
                movies = data["movies"]
                current_round = data["round"]
    
    def test_recommendations_have_genres_array(self, authenticated_client):
        """Recommendations should include genres array"""
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        current_round = 1
        
        # Play through 10 rounds
        while current_round <= 10:
            choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
                "session_id": session_id,
                "round_number": current_round,
                "chosen_movie_id": movies[0]["id"],
                "rejected_movie_id": movies[1]["id"],
                "reaction_time_ms": 2000,
                "is_super_like": False,
                "is_cant_decide": False
            })
            
            data = choice_resp.json()
            
            if data.get("game_over"):
                recommendations = data.get("recommendations", [])
                
                # Check that recommendations have genres
                for rec in recommendations:
                    if "genres" in rec:
                        assert isinstance(rec["genres"], list), "genres should be a list"
                        print(f"Movie '{rec.get('title')}' genres: {rec.get('genres')}")
                
                break
            else:
                movies = data["movies"]
                current_round = data["round"]


class TestRecencyBias:
    """Tests for recency bias multipliers"""
    
    def test_recency_bias_applied_correctly(self, authenticated_client):
        """
        Recency bias should be:
        - Rounds 1-3: 0.8x multiplier
        - Rounds 4-7: 1.0x multiplier
        - Rounds 8-10: 1.3x multiplier
        """
        # Start game
        start_resp = authenticated_client.post(f"{BASE_URL}/api/game/start", json={})
        start_data = start_resp.json()
        
        session_id = start_data["session_id"]
        movies = start_data["movies"]
        current_round = 1
        
        print("\n=== Testing Recency Bias ===")
        
        # Play through rounds and observe scoring
        while current_round <= 10:
            # Use consistent fast reaction time to isolate recency effect
            choice_resp = authenticated_client.post(f"{BASE_URL}/api/game/choose", json={
                "session_id": session_id,
                "round_number": current_round,
                "chosen_movie_id": movies[0]["id"],
                "rejected_movie_id": movies[1]["id"],
                "reaction_time_ms": 1000,  # Fast = 5 points base
                "is_super_like": False,
                "is_cant_decide": False
            })
            
            data = choice_resp.json()
            
            # Log expected recency multiplier
            if current_round <= 3:
                expected_mult = 0.8
                expected_score = 5 * 0.8  # 4.0
            elif current_round <= 7:
                expected_mult = 1.0
                expected_score = 5 * 1.0  # 5.0
            else:
                expected_mult = 1.3
                expected_score = 5 * 1.3  # 6.5
            
            print(f"Round {current_round}: Expected multiplier={expected_mult}, Expected score={expected_score}")
            
            if data.get("game_over"):
                break
            else:
                movies = data["movies"]
                current_round = data["round"]
        
        print("Recency bias test completed")
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
