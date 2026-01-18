"""
InfoPilot Explorer - Iteration 22 Tests
Testing Easter Eggs toggle feature and related functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasicEndpoints:
    """Basic health and API tests"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API info"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["status"] == "operational"
        print(f"Root endpoint: {data['name']} - {data['status']}")
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"Health check: {data['status']}")


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"Login successful for: {data['user']['email']}")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("Invalid credentials correctly rejected")
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@infopilot.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_admin"] == True
        print(f"Admin login successful: {data['user']['email']}")
        return data["token"]


class TestEasterEggsEndpoints:
    """Easter Eggs related endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_random_easter_egg_endpoint(self, auth_token):
        """Test random easter egg endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/easter-eggs/random", headers=headers)
        # Easter eggs endpoint should return 200 or 404 if no eggs exist
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "egg" in data
            print(f"Easter egg retrieved: {data['egg'].get('joke', 'N/A')[:50]}...")
        else:
            print("No easter eggs available (404)")
    
    def test_catch_easter_egg_endpoint(self, auth_token):
        """Test catching an easter egg"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/laughter-points/catch", 
                                json={"egg_id": "random"},
                                headers=headers)
        # Should return 200 or 400/404 if egg doesn't exist
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"Catch response: {data.get('message', 'Success')}")
        else:
            print(f"Catch response status: {response.status_code}")


class TestChatEndpoints:
    """Chat room endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_chat_rooms(self, auth_token):
        """Test getting chat rooms"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/chat/rooms", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "rooms" in data
        print(f"Found {len(data['rooms'])} chat rooms")


class TestForgotPasswordEndpoints:
    """Forgot password endpoint tests"""
    
    def test_forgot_password_endpoint(self):
        """Test forgot password endpoint"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": "test@example.com"
        })
        # Should always return 200 to prevent email enumeration
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"Forgot password response: {data['message']}")
    
    def test_verify_reset_token_invalid(self):
        """Test verify reset token with invalid token"""
        response = requests.get(f"{BASE_URL}/api/auth/verify-reset-token?token=invalid_token")
        assert response.status_code == 400
        print("Invalid reset token correctly rejected")


class TestSearchEndpoints:
    """Search endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
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
        assert "categories" in data
        print(f"Found {len(data['categories'])} categories")


class TestUserEndpoints:
    """User endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_current_user(self, auth_token):
        """Test getting current user info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        print(f"Current user: {data['email']}")
    
    def test_update_theme(self, auth_token):
        """Test updating user theme"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.put(f"{BASE_URL}/api/users/theme", 
                               json={"mode": "dark", "preset": "cosmic"},
                               headers=headers)
        assert response.status_code == 200
        print("Theme updated successfully")


class TestAdminEndpoints:
    """Admin endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@infopilot.com",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_admin_stats(self, admin_token):
        """Test admin stats endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Admin stats retrieved: {list(data.keys())}")
    
    def test_admin_health_check(self, admin_token):
        """Test admin health check endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/health-check", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Admin health check: {data.get('status', 'N/A')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
