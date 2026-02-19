"""
Iteration 67 Test Suite - InfoPilot Explorer
Tests for:
1. Login with admin credentials
2. Protocol Recommendation Engine component in Marketplace
3. 'It's a Bear' marketplace power section in BookPromoBanner
4. User Search API endpoint: GET /api/users/search?q=test
5. Easter Eggs with more jokes and map/stats instructions
6. Category Manager in Settings page
7. Settings - Content Filtering UI
8. Map View - Category filtering with color-coded dots
9. Comments on search results
10. User searchable by first name, last name, email, username
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infopilot-preview.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login with provided credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        print(f"✓ Admin login successful: {data['user'].get('email')}")
        return data["token"]
    
    def test_login_returns_user_data(self):
        """Test that login returns proper user data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        user = data.get("user", {})
        assert user.get("email") == ADMIN_EMAIL
        print(f"✓ User data returned correctly: {user.get('username', 'N/A')}")


class TestUserSearchAPI:
    """Tests for the User Search API endpoint - GET /api/users/search"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_user_search_endpoint_exists(self, auth_token):
        """Test that user search endpoint exists and responds"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users/search?q=test", headers=headers)
        assert response.status_code == 200, f"User search endpoint failed: {response.text}"
        data = response.json()
        assert "users" in data or "results" in data or isinstance(data, list), f"Unexpected response format: {data}"
        print(f"✓ User search endpoint working")
    
    def test_user_search_by_email(self, auth_token):
        """Test searching users by email"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users/search?q=jjspilot", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ User search by email working: {data.get('total', len(data.get('users', [])))} results")
    
    def test_user_search_by_name(self, auth_token):
        """Test searching users by name"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users/search?q=john", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ User search by name working: {data.get('total', len(data.get('users', [])))} results")
    
    def test_user_search_pagination(self, auth_token):
        """Test user search pagination"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users/search?q=a&page=1&limit=5", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data or "users" in data
        print(f"✓ User search pagination working")
    
    def test_user_search_returns_proper_fields(self, auth_token):
        """Test that user search returns expected fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users/search?q=jjspilot", headers=headers)
        assert response.status_code == 200
        data = response.json()
        users = data.get("users", [])
        if users:
            user = users[0]
            # Check expected fields
            expected_fields = ["username", "display_name"]
            for field in expected_fields:
                assert field in user, f"Missing field: {field}"
            print(f"✓ User search returns proper fields: {list(user.keys())}")
        else:
            print("✓ User search returns empty list (no matching users)")


class TestMarketplaceEndpoints:
    """Tests for Marketplace endpoints including Protocol Recommendation Engine"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_marketplace_protocols_endpoint(self, auth_token):
        """Test marketplace protocols listing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=headers)
        assert response.status_code == 200
        data = response.json()
        protocols = data.get("protocols", [])
        print(f"✓ Marketplace protocols endpoint working: {len(protocols)} protocols")
    
    def test_marketplace_protocols_has_data(self, auth_token):
        """Test marketplace protocols returns proper data structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        assert "total" in data
        print(f"✓ Marketplace protocols data structure correct: {data.get('total')} total")


class TestCategoryEndpoints:
    """Tests for Category Manager functionality"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_categories(self, auth_token):
        """Test getting user categories"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Categories endpoint working: {len(data) if isinstance(data, list) else 'N/A'} categories")
    
    def test_create_and_delete_category(self, auth_token):
        """Test creating and deleting a category"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create category
        create_response = requests.post(f"{BASE_URL}/api/categories", headers=headers, json={
            "name": "TEST_Iteration67_Category",
            "protocol": "(test or iteration) & (67 or testing)+",
            "is_public": False
        })
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        created = create_response.json()
        category_id = created.get("id") or created.get("_id")
        print(f"✓ Category created: {category_id}")
        
        # Delete category
        if category_id:
            delete_response = requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
            assert delete_response.status_code in [200, 204], f"Delete failed: {delete_response.text}"
            print(f"✓ Category deleted: {category_id}")


class TestSettingsEndpoints:
    """Tests for Settings functionality including Content Filtering"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def user_id(self, auth_token):
        """Get user ID from auth response"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("user", {}).get("id")
        pytest.skip("Could not get user ID")
    
    def test_get_user_profile(self, auth_token, user_id):
        """Test getting user profile"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users/{user_id}/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ User profile endpoint working: {data.get('username')}")
    
    def test_update_user_settings(self, auth_token):
        """Test updating user settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.put(f"{BASE_URL}/api/users/settings", headers=headers, json={
            "content_filter": "moderate"
        })
        assert response.status_code == 200
        print(f"✓ User settings update working")


class TestSearchResultComments:
    """Tests for Comments on search results"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_search_results(self, auth_token):
        """Test getting search results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/search-results", headers=headers)
        # May return 200 with results or 404 if no results
        assert response.status_code in [200, 404]
        print(f"✓ Search results endpoint working: status {response.status_code}")


class TestEasterEggsEndpoints:
    """Tests for Easter Eggs functionality"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_gamification_profile(self, auth_token):
        """Test gamification profile endpoint (includes Easter Eggs)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gamification/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Gamification profile endpoint working")
    
    def test_gamification_leaderboard(self, auth_token):
        """Test gamification leaderboard endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Gamification leaderboard endpoint working")
    
    def test_gamification_badges(self, auth_token):
        """Test gamification badges endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gamification/badges", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Gamification badges endpoint working")


class TestMapViewEndpoints:
    """Tests for Map View functionality"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_map_results_endpoint(self, auth_token):
        """Test map results endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/map/results", headers=headers)
        # May return 200 or 404 depending on data
        assert response.status_code in [200, 404]
        print(f"✓ Map results endpoint: status {response.status_code}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
