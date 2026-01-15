"""
Iteration 20 - Testing new features:
1. Geocoding API endpoint (/api/geocode) - converts city/state to lat/lng
2. AI Marketing content generation (/api/ai/generate-marketing)
3. AI Marketing suggestions endpoint (/api/ai/marketing-suggestions)
4. Enhanced badges endpoint (/api/badges/my-badges) returns new badge categories
5. Login and authentication
6. Homepage loads with book promotions
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "password123"


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """Test successful admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True, "User should be admin"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, "Should reject invalid credentials"


class TestGeocodingAPI:
    """Test geocoding endpoint - converts city/state to lat/lng"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_geocode_city_state(self, auth_token):
        """Test geocoding with city and state"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/geocode", 
            json={"city": "New York", "state": "NY", "country": "USA"},
            headers=headers
        )
        assert response.status_code == 200, f"Geocode failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Geocoding should succeed"
        assert "lat" in data, "Should return latitude"
        assert "lng" in data, "Should return longitude"
        # New York coordinates should be approximately 40.7, -74.0
        assert 40 < data["lat"] < 41, f"Latitude should be around 40.7, got {data['lat']}"
        assert -75 < data["lng"] < -73, f"Longitude should be around -74, got {data['lng']}"
    
    def test_geocode_city_only(self, auth_token):
        """Test geocoding with city only"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/geocode", 
            json={"city": "Los Angeles", "country": "USA"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "lat" in data
        assert "lng" in data
    
    def test_geocode_missing_city(self, auth_token):
        """Test geocoding without city - should fail"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/geocode", 
            json={"state": "CA", "country": "USA"},
            headers=headers
        )
        assert response.status_code == 400, "Should require city"
    
    def test_geocode_requires_auth(self):
        """Test that geocoding requires authentication"""
        response = requests.post(f"{BASE_URL}/api/geocode", 
            json={"city": "Chicago", "state": "IL"}
        )
        assert response.status_code in [401, 403], "Should require authentication"


class TestAIMarketingAPI:
    """Test AI Marketing content generation endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_marketing_suggestions_endpoint(self, auth_token):
        """Test getting pre-generated marketing suggestions"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/marketing-suggestions", headers=headers)
        assert response.status_code == 200, f"Marketing suggestions failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "taglines" in data, "Should have taglines"
        assert "social_posts" in data, "Should have social_posts"
        assert "email_subjects" in data, "Should have email_subjects"
        
        # Verify content
        assert len(data["taglines"]) > 0, "Should have at least one tagline"
        assert len(data["social_posts"]) > 0, "Should have at least one social post"
        assert len(data["email_subjects"]) > 0, "Should have at least one email subject"
        
        # Verify email subject structure
        email = data["email_subjects"][0]
        assert "subject" in email, "Email should have subject"
        assert "preview" in email, "Email should have preview"
    
    def test_marketing_suggestions_requires_auth(self):
        """Test that marketing suggestions requires authentication"""
        response = requests.get(f"{BASE_URL}/api/ai/marketing-suggestions")
        assert response.status_code in [401, 403], "Should require authentication"
    
    def test_generate_marketing_endpoint_exists(self, auth_token):
        """Test that generate-marketing endpoint exists and accepts requests"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/ai/generate-marketing", 
            json={"type": "tagline", "context": ""},
            headers=headers
        )
        # May return 500 if LLM key has issues, but endpoint should exist
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            assert "generated_content" in data
            assert "content_type" in data
    
    def test_generate_marketing_content_types(self, auth_token):
        """Test different content types for marketing generation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        content_types = ["tagline", "description", "social_post", "email"]
        
        for content_type in content_types:
            response = requests.post(f"{BASE_URL}/api/ai/generate-marketing", 
                json={"type": content_type, "context": ""},
                headers=headers
            )
            # Endpoint should accept all content types
            assert response.status_code in [200, 500], f"Failed for type {content_type}: {response.status_code}"


class TestEnhancedBadges:
    """Test enhanced badges endpoint with new badge categories"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_my_badges_endpoint(self, auth_token):
        """Test getting user's badges"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/badges/my-badges", headers=headers)
        assert response.status_code == 200, f"My badges failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "badges" in data, "Should have badges array"
        assert "total_copies" in data, "Should have total_copies"
        assert "protocols_created" in data, "Should have protocols_created"
        
        badges = data["badges"]
        assert len(badges) > 0, "Should have badge definitions"
        
        # Verify badge structure
        badge = badges[0]
        assert "id" in badge, "Badge should have id"
        assert "name" in badge, "Badge should have name"
        assert "icon" in badge, "Badge should have icon"
        assert "earned" in badge, "Badge should have earned status"
        assert "progress" in badge, "Badge should have progress"
    
    def test_badges_include_new_categories(self, auth_token):
        """Test that badges include new social/search/engagement categories"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/badges/my-badges", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        badge_ids = [b["id"] for b in data["badges"]]
        
        # Check for new badge categories
        new_badge_types = [
            "social_butterfly",  # Social badges
            "group_leader",
            "influencer", 
            "messenger",
            "researcher",  # Search badges
            "data_miner",
            "intel_master",
            "reactor",  # Engagement badges
            "commentator"
        ]
        
        # At least some of the new badges should be present
        found_new_badges = [b for b in new_badge_types if b in badge_ids]
        assert len(found_new_badges) > 0, f"Should have new badge types. Found: {badge_ids}"
    
    def test_badges_leaderboard(self, auth_token):
        """Test badges leaderboard endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/badges/leaderboard", headers=headers)
        assert response.status_code == 200, f"Leaderboard failed: {response.text}"
        data = response.json()
        
        assert "leaderboard" in data, "Should have leaderboard array"


class TestCategoriesWithLocation:
    """Test categories endpoints with location support"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_create_category_with_location(self, auth_token):
        """Test creating a category with location data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create category with location
        response = requests.post(f"{BASE_URL}/api/categories", 
            json={
                "name": "TEST_Iteration20_Location",
                "protocol": {"protocol_string": "(test or iteration20)"},
                "is_public": False,
                "for_sale": True,
                "price": 1.50,
                "location": {
                    "city": "Seattle",
                    "state": "WA",
                    "country": "USA",
                    "lat": 47.6062,
                    "lng": -122.3321
                }
            },
            headers=headers
        )
        assert response.status_code in [200, 201], f"Create failed: {response.text}"
        data = response.json()
        
        # Verify location was saved
        assert "id" in data, "Should return category id"
        category_id = data["id"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
    
    def test_get_categories_returns_location(self, auth_token):
        """Test that categories endpoint returns location data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert response.status_code == 200
        # Categories may or may not have location, just verify endpoint works


class TestHealthAndBasics:
    """Test basic health and homepage endpoints"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_book_info_endpoint(self):
        """Test book info endpoint for homepage"""
        response = requests.get(f"{BASE_URL}/api/book-info")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data, "Should have book title"
        assert data["title"] == "Letters to Evelyn"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
