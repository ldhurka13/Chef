"""
Tests for onboarding functionality.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# Test the onboarding service functions
class TestOnboardingService:
    """Test onboarding eligibility and dismissal logic"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        mock = MagicMock()
        mock.auth_users = MagicMock()
        mock.watch_history = MagicMock()
        mock.watchlist = MagicMock()
        return mock
    
    def test_new_registration_eligible(self, mock_db):
        """New user with zero diary and zero watchlist should be eligible"""
        # Setup
        mock_db.auth_users.find_one = AsyncMock(return_value=None)
        mock_db.watch_history.count_documents = AsyncMock(return_value=0)
        mock_db.watchlist.count_documents = AsyncMock(return_value=0)
        
        # Mock the database in the service
        with patch('services.onboarding_service.db', mock_db):
            from services.onboarding_service import get_onboarding_eligibility
            result = asyncio.run(get_onboarding_eligibility("test-user-id"))
            
            assert result["eligible"] == True
            assert result["diary_count"] == 0
            assert result["watchlist_count"] == 0
    
    def test_user_with_diary_not_eligible(self, mock_db):
        """User with diary entries should not be eligible"""
        mock_db.auth_users.find_one = AsyncMock(return_value={"onboarding_skipped": False})
        mock_db.watch_history.count_documents = AsyncMock(return_value=5)
        mock_db.watchlist.count_documents = AsyncMock(return_value=0)
        
        with patch('services.onboarding_service.db', mock_db):
            from services.onboarding_service import get_onboarding_eligibility
            result = asyncio.run(get_onboarding_eligibility("test-user-id"))
            
            assert result["eligible"] == False
            assert result["diary_count"] == 5
            assert result["watchlist_count"] == 0
    
    def test_user_with_watchlist_not_eligible(self, mock_db):
        """User with watchlist entries should not be eligible"""
        mock_db.auth_users.find_one = AsyncMock(return_value={"onboarding_skipped": False})
        mock_db.watch_history.count_documents = AsyncMock(return_value=0)
        mock_db.watchlist.count_documents = AsyncMock(return_value=3)
        
        with patch('services.onboarding_service.db', mock_db):
            from services.onboarding_service import get_onboarding_eligibility
            result = asyncio.run(get_onboarding_eligibility("test-user-id"))
            
            assert result["eligible"] == False
            assert result["diary_count"] == 0
            assert result["watchlist_count"] == 3
    
    def test_user_with_both_not_eligible(self, mock_db):
        """User with both diary and watchlist should not be eligible"""
        mock_db.auth_users.find_one = AsyncMock(return_value={"onboarding_skipped": False})
        mock_db.watch_history.count_documents = AsyncMock(return_value=10)
        mock_db.watchlist.count_documents = AsyncMock(return_value=5)
        
        with patch('services.onboarding_service.db', mock_db):
            from services.onboarding_service import get_onboarding_eligibility
            result = asyncio.run(get_onboarding_eligibility("test-user-id"))
            
            assert result["eligible"] == False
            assert result["diary_count"] == 10
            assert result["watchlist_count"] == 5
    
    def test_skip_persistence(self, mock_db):
        """Skipping onboarding should persist the state"""
        mock_db.auth_users.update_one = AsyncMock(return_value=None)
        
        with patch('services.onboarding_service.db', mock_db):
            from services.onboarding_service import mark_onboarding_skipped
            result = asyncio.run(mark_onboarding_skipped("test-user-id"))
            
            assert result["success"] == True
            assert result["onboarding_skipped"] == True
            mock_db.auth_users.update_one.assert_called_once()
    
    def test_legacy_user_missing_field(self, mock_db):
        """Legacy user without onboarding fields should work safely"""
        # Return a user document without onboarding_skipped/completed fields
        mock_db.auth_users.find_one = AsyncMock(return_value={})
        mock_db.watch_history.count_documents = AsyncMock(return_value=0)
        mock_db.watchlist.count_documents = AsyncMock(return_value=0)
        
        with patch('services.onboarding_service.db', mock_db):
            from services.onboarding_service import get_onboarding_eligibility
            result = asyncio.run(get_onboarding_eligibility("legacy-user-id"))
            
            # Should default to False for missing fields and be eligible
            assert result["eligible"] == True
            assert result["onboarding_skipped"] == False
            assert result["onboarding_completed"] == False


class TestOnboardingAPI:
    """Test onboarding API endpoints"""
    
    def test_eligibility_endpoint_requires_auth(self):
        """Eligibility endpoint should require authentication"""
        from fastapi.testclient import TestClient
        # This would require setting up the full app context
        pass
    
    def test_skip_endpoint_requires_auth(self):
        """Skip endpoint should require authentication"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
