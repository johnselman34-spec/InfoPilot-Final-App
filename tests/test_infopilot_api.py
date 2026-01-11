"""
InfoPilot Explorer API Tests
Tests for: Auth, Categories, Search, Social, Map, Settings endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "password123"

class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        assert "is_paid" in data["user"]
        assert "is_admin" in data["user"]
        print(f"Login successful - User: {data['user']['username']}, Premium: {data['user']['is_paid']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"Invalid login correctly rejected: {data['detail']}")
    
    def test_get_me_authenticated(self):
        """Test /auth/me endpoint with valid token"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_response.json()["token"]
        
        # Get user info
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert "friends_count" in data
        print(f"Auth/me successful - Friends count: {data.get('friends_count', 0)}")
    
    def test_get_me_unauthenticated(self):
        """Test /auth/me endpoint without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("Unauthenticated /auth/me correctly rejected")


class TestCategoriesEndpoints:
    """Category CRUD endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_categories(self, auth_token):
        """Test getting user categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Categories retrieved: {len(data)} categories found")
        for cat in data[:3]:  # Print first 3
            print(f"  - {cat['name']}: {cat['protocol'][:50]}...")
    
    def test_create_category(self, auth_token):
        """Test creating a new category"""
        response = requests.post(f"{BASE_URL}/api/categories", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "TEST_Category_API",
                "protocol": "(test or api) & (python)",
                "is_public": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Category_API"
        assert "id" in data
        print(f"Category created: {data['name']} (ID: {data['id']})")
        
        # Cleanup - delete the test category
        delete_response = requests.delete(
            f"{BASE_URL}/api/categories/{data['id']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert delete_response.status_code == 200
        print("Test category cleaned up")
    
    def test_create_category_invalid_protocol(self, auth_token):
        """Test creating category with invalid protocol format"""
        response = requests.post(f"{BASE_URL}/api/categories", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "TEST_Invalid",
                "protocol": "invalid protocol format",
                "is_public": False
            }
        )
        assert response.status_code == 400
        print("Invalid protocol correctly rejected")


class TestSearchEndpoints:
    """Search and collate endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["token"]
    
    def test_search_query(self, auth_token):
        """Test web search with SerpAPI"""
        response = requests.post(f"{BASE_URL}/api/search",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"query": "artificial intelligence"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        print(f"Search returned {data['total']} results")
        if data['results']:
            print(f"  First result: {data['results'][0]['title'][:60]}...")
    
    def test_search_blocked_content(self, auth_token):
        """Test search with blocked content"""
        response = requests.post(f"{BASE_URL}/api/search",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"query": "child safety"}  # Contains blocked word
        )
        assert response.status_code == 400
        print("Blocked content search correctly rejected")
    
    def test_ultimate_search_stats(self, auth_token):
        """Test ultimate search stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_results" in data
        assert "article_type_breakdown" in data
        print(f"Stats: {data['total_results']} total results")
    
    def test_ultimate_search_results(self, auth_token):
        """Test ultimate search results endpoint"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search?page=1&aggregation=and_or",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert "page" in data
        print(f"Ultimate search: {data['total']} results, page {data['page']}")


class TestMapEndpoints:
    """Map data endpoint tests (premium feature)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["token"]
    
    def test_map_data_premium_user(self, auth_token):
        """Test map data endpoint for premium user"""
        response = requests.get(f"{BASE_URL}/api/map-data",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Premium user should get 200
        assert response.status_code == 200
        data = response.json()
        assert "markers" in data
        print(f"Map data: {len(data['markers'])} markers found")


class TestSocialEndpoints:
    """Social features endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_social_feed(self, auth_token):
        """Test social feed endpoint"""
        response = requests.get(f"{BASE_URL}/api/feed",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Feed returns a list directly
        assert isinstance(data, list)
        print(f"Social feed: {len(data)} posts")
    
    def test_get_friends(self, auth_token):
        """Test friends list endpoint"""
        response = requests.get(f"{BASE_URL}/api/friends",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "friends" in data
        print(f"Friends: {len(data['friends'])} friends")
    
    def test_get_posts(self, auth_token):
        """Test posts endpoint"""
        response = requests.get(f"{BASE_URL}/api/posts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Posts returns a list directly
        assert isinstance(data, list)
        print(f"Posts: {len(data)} posts found")


class TestPaymentEndpoints:
    """Payment endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_payment_link(self, auth_token):
        """Test payment link endpoint"""
        response = requests.get(f"{BASE_URL}/api/payment/link",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "payment_url" in data
        assert "price" in data
        print(f"Payment link: {data['payment_url'][:50]}... Price: ${data['price']}")


class TestSettingsEndpoints:
    """Settings endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["token"]
    
    def test_update_settings(self, auth_token):
        """Test updating user settings"""
        response = requests.put(f"{BASE_URL}/api/users/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "ultimate_search_public": False,
                "friends_visible": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Settings updated: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
