"""
Test suite for Iteration 9 features:
- Quote Gallery (75+ quotes)
- Protocol Debugger
- Weekly/Monthly Leaderboards
- Share Badge functionality
- Analytics Dashboard (admin only)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_ADMIN_EMAIL = "john@infojet.com"
TEST_ADMIN_PASSWORD = "password123"


class TestQuoteGallery:
    """Test Quote Gallery API - 75+ quotes from manuscript"""
    
    def test_quote_gallery_returns_quotes(self):
        """Test that quote gallery returns quotes"""
        response = requests.get(f"{BASE_URL}/api/quotes/gallery")
        assert response.status_code == 200
        
        data = response.json()
        assert "quotes" in data
        assert "total" in data
        assert "categories" in data
        
    def test_quote_gallery_has_75_plus_quotes(self):
        """Test that quote gallery has at least 75 quotes"""
        response = requests.get(f"{BASE_URL}/api/quotes/gallery")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] >= 75, f"Expected 75+ quotes, got {data['total']}"
        
    def test_quote_gallery_has_all_categories(self):
        """Test that quote gallery has all expected categories"""
        response = requests.get(f"{BASE_URL}/api/quotes/gallery")
        assert response.status_code == 200
        
        data = response.json()
        category_ids = [cat["id"] for cat in data["categories"]]
        
        expected_categories = ["hilarious", "profound", "dad_joke", "chapter_teaser", "wild_element", "marketing"]
        for cat in expected_categories:
            assert cat in category_ids, f"Missing category: {cat}"
            
    def test_quote_structure(self):
        """Test that quotes have correct structure"""
        response = requests.get(f"{BASE_URL}/api/quotes/gallery")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["quotes"]) > 0
        
        quote = data["quotes"][0]
        assert "quote" in quote
        assert "context" in quote
        assert "category" in quote


class TestProtocolDebugger:
    """Test Protocol Debugger API"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
        
    def test_protocol_debug_basic(self, auth_token):
        """Test basic protocol debugging"""
        response = requests.post(
            f"{BASE_URL}/api/protocol/debug",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"protocol": "(climate or weather)"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] == True
        assert "groups" in data
        assert len(data["groups"]) == 1
        
    def test_protocol_debug_with_test_text(self, auth_token):
        """Test protocol debugging with test text"""
        response = requests.post(
            f"{BASE_URL}/api/protocol/debug",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "protocol": "(climate or weather) & (news)+",
                "test_text": "Climate news about weather patterns"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] == True
        assert "test_result" in data
        assert data["test_result"] == True
        assert "match_details" in data
        
    def test_protocol_debug_complex(self, auth_token):
        """Test complex protocol debugging"""
        response = requests.post(
            f"{BASE_URL}/api/protocol/debug",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "protocol": "(George Bush or President Bush) & (aviation or pilot)+ & (scandal)^",
                "test_text": "President Bush was a pilot in the aviation industry"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] == True
        assert "test_result" in data
        # Should match because: has "President Bush", has "pilot" and "aviation", no "scandal"
        assert data["test_result"] == True


class TestLeaderboards:
    """Test Weekly and Monthly Leaderboard APIs"""
    
    def test_weekly_leaderboard(self):
        """Test weekly leaderboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard/weekly")
        assert response.status_code == 200
        
        data = response.json()
        assert data["period"] == "weekly"
        assert "start_date" in data
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
        
    def test_monthly_leaderboard(self):
        """Test monthly leaderboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard/monthly")
        assert response.status_code == 200
        
        data = response.json()
        assert data["period"] == "monthly"
        assert "start_date" in data
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
        
    def test_all_time_leaderboard(self):
        """Test all-time leaderboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)


class TestShareBadge:
    """Test Share Badge functionality"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
        
    def test_share_badge_success(self, auth_token):
        """Test sharing a badge the user has"""
        response = requests.post(
            f"{BASE_URL}/api/gamification/share-badge",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"badge_id": "pioneer"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "badge" in data
        assert "username" in data
        assert "share_text" in data
        assert "share_urls" in data
        assert "twitter" in data["share_urls"]
        assert "facebook" in data["share_urls"]
        
    def test_share_badge_not_found(self, auth_token):
        """Test sharing a badge the user doesn't have"""
        response = requests.post(
            f"{BASE_URL}/api/gamification/share-badge",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"badge_id": "nonexistent_badge"}
        )
        assert response.status_code == 404


class TestAnalyticsDashboard:
    """Test Analytics Dashboard API (admin only)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
        
    def test_analytics_dashboard_admin(self, admin_token):
        """Test analytics dashboard for admin user"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "users" in data
        assert "searches" in data
        assert "protocols" in data
        assert "marketplace" in data
        assert "engagement" in data
        assert "popular_search_terms" in data
        assert "generated_at" in data
        
        # Verify user stats structure
        assert "total" in data["users"]
        assert "new_today" in data["users"]
        assert "new_this_week" in data["users"]
        
        # Verify search stats structure
        assert "total" in data["searches"]
        assert "today" in data["searches"]
        assert "this_week" in data["searches"]
        
    def test_analytics_search_trends(self, admin_token):
        """Test analytics search trends endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/search-trends?days=7",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "period_days" in data
        assert "trends" in data
        assert data["period_days"] == 7


class TestGamificationProfile:
    """Test Gamification Profile API"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
        
    def test_gamification_profile(self, auth_token):
        """Test gamification profile endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/profile",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "username" in data
        assert "badges" in data
        assert "level" in data
        assert "stats" in data
        assert "rank" in data
        
        # Verify level structure
        assert "level" in data["level"]
        assert "current_xp" in data["level"]
        assert "xp_for_next_level" in data["level"]
        assert "total_xp" in data["level"]
        assert "progress_percent" in data["level"]
        
        # Verify stats structure
        assert "searches" in data["stats"]
        assert "protocols_created" in data["stats"]
        assert "login_streak" in data["stats"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
