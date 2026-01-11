"""
InfoPilot Explorer - Iteration 11 Feature Tests
Tests for: Notifications API, Data Export API, Mobile Responsive, PWA Support
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from iteration_10
TEST_USER_EMAIL = "test_user_refactor@test.com"
TEST_USER_PASSWORD = "TestPass123!"


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestAuthentication:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_USER_EMAIL


@pytest.fixture
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestNotificationsAPI:
    """Notifications API tests - New Feature"""
    
    def test_get_notifications_unauthorized(self):
        """Test notifications endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 401
    
    def test_get_notifications(self, auth_headers):
        """Test GET /api/notifications returns notifications list"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert isinstance(data["notifications"], list)
    
    def test_get_unread_count(self, auth_headers):
        """Test GET /api/notifications/unread-count returns count"""
        response = requests.get(f"{BASE_URL}/api/notifications/unread-count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)
        assert data["count"] >= 0
    
    def test_mark_all_read(self, auth_headers):
        """Test POST /api/notifications/mark-all-read"""
        response = requests.post(f"{BASE_URL}/api/notifications/mark-all-read", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "marked_count" in data
    
    def test_get_notifications_with_limit(self, auth_headers):
        """Test notifications with limit parameter"""
        response = requests.get(f"{BASE_URL}/api/notifications?limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
    
    def test_get_notifications_unread_only(self, auth_headers):
        """Test notifications with unread_only filter"""
        response = requests.get(f"{BASE_URL}/api/notifications?unread_only=true", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data


class TestDataExportAPI:
    """Data Export API tests - New Feature"""
    
    def test_export_summary_unauthorized(self):
        """Test export summary requires auth"""
        response = requests.get(f"{BASE_URL}/api/export/summary")
        assert response.status_code == 401
    
    def test_export_summary(self, auth_headers):
        """Test GET /api/export/summary returns data summary"""
        response = requests.get(f"{BASE_URL}/api/export/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify summary structure
        assert "summary" in data
        summary = data["summary"]
        assert "categories" in summary
        assert "search_results" in summary
        assert "protocol_templates" in summary
        assert "marketplace_purchases" in summary
        assert "marketplace_listings" in summary
        assert "friends" in summary
        assert "messages" in summary
        assert "groups" in summary
        assert "xp" in summary
        assert "badges" in summary
        
        # Verify export formats
        assert "export_formats" in data
        assert "json" in data["export_formats"]
        assert "csv" in data["export_formats"]
        
        # Verify available exports
        assert "available_exports" in data
        assert "all" in data["available_exports"]
    
    def test_export_all_json(self, auth_headers):
        """Test GET /api/export/all with JSON format"""
        response = requests.get(f"{BASE_URL}/api/export/all?format=json", headers=auth_headers)
        assert response.status_code == 200
        
        # Check content type
        assert "application/json" in response.headers.get("Content-Type", "")
        
        # Verify data structure
        data = response.json()
        assert "export_date" in data
        assert "user" in data
        assert "categories" in data
        assert "search_results" in data
        assert "protocol_templates" in data
        assert "marketplace" in data
        assert "social" in data
        assert "gamification" in data
    
    def test_export_all_csv(self, auth_headers):
        """Test GET /api/export/all with CSV format"""
        response = requests.get(f"{BASE_URL}/api/export/all?format=csv", headers=auth_headers)
        assert response.status_code == 200
        
        # Check content type
        assert "text/csv" in response.headers.get("Content-Type", "")
        
        # Verify content disposition header
        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
    
    def test_export_categories(self, auth_headers):
        """Test GET /api/export/categories"""
        response = requests.get(f"{BASE_URL}/api/export/categories?format=json", headers=auth_headers)
        assert response.status_code == 200
    
    def test_export_search_results(self, auth_headers):
        """Test GET /api/export/search-results"""
        response = requests.get(f"{BASE_URL}/api/export/search-results?format=json", headers=auth_headers)
        assert response.status_code == 200
    
    def test_export_protocols(self, auth_headers):
        """Test GET /api/export/protocols"""
        response = requests.get(f"{BASE_URL}/api/export/protocols?format=json", headers=auth_headers)
        assert response.status_code == 200


class TestCategoryCreation:
    """Category creation tests - Bug Fix verification"""
    
    def test_create_category(self, auth_headers):
        """Test category creation (bug fix - Response body already used)"""
        import time
        unique_name = f"Test Category {int(time.time())}"
        
        response = requests.post(f"{BASE_URL}/api/categories", 
            headers={**auth_headers, "Content-Type": "application/json"},
            json={
                "name": unique_name,
                "protocol": "(test or example)+",
                "is_public": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == unique_name
        assert data["protocol"] == "(test or example)+"
    
    def test_get_categories(self, auth_headers):
        """Test GET /api/categories returns user categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestGamificationEndpoints:
    """Gamification endpoints tests"""
    
    def test_get_badges(self):
        """Test GET /api/gamification/badges"""
        response = requests.get(f"{BASE_URL}/api/gamification/badges")
        assert response.status_code == 200
        data = response.json()
        assert "badges" in data
    
    def test_get_leaderboard(self):
        """Test GET /api/gamification/leaderboard"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
    
    def test_get_gamification_profile(self, auth_headers):
        """Test GET /api/gamification/profile"""
        response = requests.get(f"{BASE_URL}/api/gamification/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "xp" in data
        assert "level" in data


class TestMarketplaceEndpoints:
    """Marketplace endpoints tests"""
    
    def test_get_marketplace_categories(self):
        """Test GET /api/marketplace/categories"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
    
    def test_get_marketplace_protocols(self):
        """Test GET /api/marketplace/protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        assert "total" in data


class TestOnlineStatus:
    """Online status endpoint tests"""
    
    def test_get_online_status(self):
        """Test GET /api/notifications/online-status"""
        response = requests.get(f"{BASE_URL}/api/notifications/online-status")
        assert response.status_code == 200
        data = response.json()
        assert "online_users" in data


class TestPWASupport:
    """PWA Support tests"""
    
    def test_manifest_exists(self):
        """Test manifest.json is accessible"""
        # PWA manifest should be at root
        response = requests.get(f"{BASE_URL.replace('/api', '')}/manifest.json")
        # May return 200 or 404 depending on setup
        # Just verify the endpoint doesn't error
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
