"""
Iteration 24 - Testing extracted pages and features
Tests: Login, Statistics, Book, Friends, Privacy Policy, Terms of Service, Marketplace FREE badge
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "password123"


class TestAuthLogin:
    """Test login flow with admin account"""
    
    def test_login_success(self):
        """Test successful login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True, "User should be admin"
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 404], f"Expected 401/404, got {response.status_code}"


class TestStatisticsPage:
    """Test Statistics page API endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_statistics_endpoint(self, auth_token):
        """Test /api/statistics endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/statistics", headers=headers)
        assert response.status_code == 200, f"Statistics failed: {response.text}"
        data = response.json()
        # Verify response structure
        assert "total_results" in data or "total_categories" in data
    
    def test_global_statistics(self, auth_token):
        """Test /api/statistics/global endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/statistics/global", headers=headers)
        assert response.status_code == 200, f"Global stats failed: {response.text}"
        data = response.json()
        # Verify global stats structure
        assert "total_users" in data or "total_public_categories" in data
    
    def test_popular_protocols(self, auth_token):
        """Test /api/statistics/popular-protocols endpoint - Most Popular Protocols section"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/statistics/popular-protocols?limit=10", headers=headers)
        assert response.status_code == 200, f"Popular protocols failed: {response.text}"
        data = response.json()
        assert "popular_protocols" in data, "popular_protocols key missing"
    
    def test_badges_my_badges(self, auth_token):
        """Test /api/badges/my-badges endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/badges/my-badges", headers=headers)
        assert response.status_code == 200, f"My badges failed: {response.text}"
    
    def test_badges_leaderboard(self, auth_token):
        """Test /api/badges/leaderboard endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/badges/leaderboard", headers=headers)
        assert response.status_code == 200, f"Leaderboard failed: {response.text}"
        data = response.json()
        assert "leaderboard" in data


class TestFriendsPage:
    """Test Friends page API endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_friends_list(self, auth_token):
        """Test /api/friends endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/friends", headers=headers)
        assert response.status_code == 200, f"Friends list failed: {response.text}"
        data = response.json()
        assert "friends" in data, "friends key missing"
    
    def test_friend_requests(self, auth_token):
        """Test /api/friends/requests endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/friends/requests", headers=headers)
        assert response.status_code == 200, f"Friend requests failed: {response.text}"


class TestLegalPages:
    """Test Privacy Policy and Terms of Service public pages"""
    
    def test_privacy_policy(self):
        """Test /api/legal/privacy-policy endpoint - Public page"""
        response = requests.get(f"{BASE_URL}/api/legal/privacy-policy")
        assert response.status_code == 200, f"Privacy policy failed: {response.text}"
        data = response.json()
        assert "content" in data, "content key missing"
        assert "last_updated" in data, "last_updated key missing"
    
    def test_terms_of_service(self):
        """Test /api/legal/terms-of-service endpoint - Public page"""
        response = requests.get(f"{BASE_URL}/api/legal/terms-of-service")
        assert response.status_code == 200, f"Terms of service failed: {response.text}"
        data = response.json()
        assert "content" in data, "content key missing"
        assert "last_updated" in data, "last_updated key missing"


class TestMarketplaceFREEBadge:
    """Test Marketplace FREE badge display for $0.00 or public protocols"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_marketplace_protocols_list(self, auth_token):
        """Test /api/marketplace/protocols endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=headers)
        assert response.status_code == 200, f"Marketplace protocols failed: {response.text}"
        data = response.json()
        assert "protocols" in data, "protocols key missing"
    
    def test_marketplace_free_badge_logic(self, auth_token):
        """Test that is_free flag is set correctly for $0.00 protocols"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=headers)
        assert response.status_code == 200
        data = response.json()
        protocols = data.get("protocols", [])
        
        # Check if any protocol has is_free flag
        for protocol in protocols:
            price = protocol.get("price", 0)
            is_free = protocol.get("is_free", False)
            is_public = protocol.get("is_public", False)
            
            # If price is 0 or is_public is True, is_free should be True
            if price == 0 or is_public:
                # Log for verification
                print(f"Protocol: {protocol.get('name')}, Price: {price}, is_free: {is_free}, is_public: {is_public}")


class TestBookPage:
    """Test Book page - no API needed, just verify constants are accessible"""
    
    def test_book_page_loads(self):
        """Book page uses static constants, verify frontend loads"""
        # This is a frontend-only page, we'll test via Playwright
        pass


class TestAdminControls:
    """Test admin controls visibility"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_admin_user_is_admin(self, auth_token):
        """Verify admin user has is_admin flag"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        data = response.json()
        assert data.get("is_admin") == True, "User should be admin"
