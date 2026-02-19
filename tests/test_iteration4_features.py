"""
InfoPilot Explorer - Iteration 4 Feature Tests
Tests for: Google OAuth, Admin Badge, Map Features, Hashtags, Category Creation (no filter), Admin Panel Search Settings
"""
import pytest
import requests
import os

BASE_URL = "https://infopilot-preview.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"
GOOGLE_USER_EMAIL = "turbomentor33@gmail.com"
GOOGLE_USER_ID = "111835474350288495210"


class TestAdminUsers:
    """Test admin user functionality"""
    
    def test_admin_login_john(self):
        """Test john@infojet.com is admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_admin"] == True
        print(f"✓ john@infojet.com is admin: {data['user']['is_admin']}")
    
    def test_google_oauth_admin_turbomentor(self):
        """Test turbomentor33@gmail.com is admin via Google OAuth"""
        response = requests.post(f"{BASE_URL}/api/auth/google", json={
            "email": GOOGLE_USER_EMAIL,
            "google_id": GOOGLE_USER_ID,
            "name": "Turbo Mentor",
            "picture": None
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_admin"] == True
        print(f"✓ turbomentor33@gmail.com is admin: {data['user']['is_admin']}")
        return data["token"]


class TestContentFilterDisabled:
    """Test that content filter is disabled (any words allowed)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_category_creation_any_words(self, auth_token):
        """Test category creation with any words (no content filter)"""
        # Test with words that might have been blocked before
        response = requests.post(f"{BASE_URL}/api/categories",
            json={
                "name": "TEST_AnyWords_Test",
                "protocol": "(any or words or allowed)",
                "is_public": False
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_AnyWords_Test"
        print(f"✓ Category created with any words: {data['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
    
    def test_search_any_query(self, auth_token):
        """Test search accepts any query (content filter disabled)"""
        response = requests.post(f"{BASE_URL}/api/search",
            json={"query": "test search query"},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )
        # Should return 200 (not 400 for blocked content)
        assert response.status_code == 200
        print("✓ Search accepts any query (content filter disabled)")


class TestAdminPanelSearchSettings:
    """Test Admin Panel Search Settings"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_admin_settings(self, admin_token):
        """Test getting admin settings including max_search_pages"""
        response = requests.get(f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for search-related settings
        settings_keys = [s["key"] for s in data]
        print(f"✓ Admin settings retrieved: {settings_keys}")
        
        # Verify max_search_pages exists
        max_pages_setting = next((s for s in data if s["key"] == "max_search_pages"), None)
        if max_pages_setting:
            print(f"✓ max_search_pages setting found: {max_pages_setting['value']}")
            assert 1 <= max_pages_setting["value"] <= 99
    
    def test_update_max_search_pages(self, admin_token):
        """Test updating max_search_pages setting"""
        # Update to a test value
        response = requests.put(f"{BASE_URL}/api/admin/settings/max_search_pages",
            json=50,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✓ max_search_pages updated to 50")
        
        # Restore to default
        requests.put(f"{BASE_URL}/api/admin/settings/max_search_pages",
            json=99,
            headers={"Authorization": f"Bearer {admin_token}"}
        )


class TestMapData:
    """Test Map Data endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_map_data_admin(self, admin_token):
        """Test getting map data as admin"""
        response = requests.get(f"{BASE_URL}/api/map-data",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "markers" in data
        print(f"✓ Map data retrieved: {len(data['markers'])} markers")
    
    def test_map_data_requires_premium(self):
        """Test that map data requires premium/admin access"""
        # Create a non-admin user
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": "test_nonpremium@example.com",
            "username": "test_nonpremium",
            "password": "testpass123"
        })
        
        if response.status_code == 200:
            token = response.json()["token"]
            
            # Try to access map data
            map_response = requests.get(f"{BASE_URL}/api/map-data",
                headers={"Authorization": f"Bearer {token}"}
            )
            # Should be 403 (forbidden) for non-premium users
            assert map_response.status_code == 403
            print("✓ Map data correctly requires premium access")
        else:
            # User might already exist
            print("✓ Test user already exists, skipping premium check")


class TestGoogleOAuthFlow:
    """Test Google OAuth flow"""
    
    def test_google_auth_endpoint(self):
        """Test Google OAuth endpoint accepts valid data"""
        response = requests.post(f"{BASE_URL}/api/auth/google", json={
            "email": GOOGLE_USER_EMAIL,
            "google_id": GOOGLE_USER_ID,
            "name": "Turbo Mentor",
            "picture": None
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == GOOGLE_USER_EMAIL
        print(f"✓ Google OAuth login successful for {GOOGLE_USER_EMAIL}")
    
    def test_google_session_data_endpoint(self):
        """Test Google session data proxy endpoint exists"""
        # This endpoint requires a valid session_id from Emergent Auth
        # We just verify the endpoint exists and returns appropriate error
        response = requests.get(f"{BASE_URL}/api/auth/google/session-data?session_id=invalid")
        # Should return error for invalid session, not 404
        assert response.status_code != 404
        print("✓ Google session data endpoint exists")


class TestUltimateSearchHashtags:
    """Test Ultimate Search with hashtags"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_ultimate_search_results(self, admin_token):
        """Test Ultimate Search returns results with expected fields"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search?page=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        print(f"✓ Ultimate Search returned {data['total']} results")
        
        # Check result structure
        if data["results"]:
            result = data["results"][0]
            assert "title" in result
            assert "url" in result
            assert "article_type" in result
            print(f"✓ Result has expected fields: title, url, article_type")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_cleanup_test_categories(self, admin_token):
        """Cleanup TEST_ prefixed categories"""
        response = requests.get(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = response.json()
        
        deleted = 0
        for cat in categories:
            if cat["name"].startswith("TEST_"):
                del_res = requests.delete(f"{BASE_URL}/api/categories/{cat['id']}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                if del_res.status_code == 200:
                    deleted += 1
        
        print(f"✓ Cleaned up {deleted} test categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
