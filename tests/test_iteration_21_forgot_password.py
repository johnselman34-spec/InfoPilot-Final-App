"""
InfoPilot Explorer - Iteration 21 Tests
Testing Forgot Password Feature:
- POST /api/auth/forgot-password - Sends reset email
- GET /api/auth/verify-reset-token - Validates token
- POST /api/auth/reset-password - Resets password with valid token
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@infopilot.com"
ADMIN_PASSWORD = "admin123"
TEST_EMAIL = "testuser_new@example.com"
TEST_PASSWORD = "password123"


class TestForgotPasswordEndpoint:
    """Test POST /api/auth/forgot-password endpoint"""
    
    def test_forgot_password_existing_email(self):
        """Test forgot password with existing email - should return success message"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": ADMIN_EMAIL}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Should always return success to prevent email enumeration
        assert "reset link has been sent" in data["message"].lower() or "if an account exists" in data["message"].lower()
    
    def test_forgot_password_nonexistent_email(self):
        """Test forgot password with non-existent email - should still return success (prevent enumeration)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "nonexistent_user_12345@example.com"}
        )
        # Should return 200 to prevent email enumeration attacks
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_forgot_password_invalid_email_format(self):
        """Test forgot password with invalid email format"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "not-an-email"}
        )
        # May return 200 (to prevent enumeration) or 422 (validation error)
        assert response.status_code in [200, 422]
    
    def test_forgot_password_empty_email(self):
        """Test forgot password with empty email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": ""}
        )
        # Should return validation error
        assert response.status_code in [200, 422]


class TestVerifyResetToken:
    """Test GET /api/auth/verify-reset-token endpoint"""
    
    def test_verify_invalid_token(self):
        """Test verify with invalid token - should return 400"""
        response = requests.get(
            f"{BASE_URL}/api/auth/verify-reset-token",
            params={"token": "invalid_token_12345"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
    
    def test_verify_empty_token(self):
        """Test verify with empty token - should return 400 or 422"""
        response = requests.get(
            f"{BASE_URL}/api/auth/verify-reset-token",
            params={"token": ""}
        )
        assert response.status_code in [400, 422]
    
    def test_verify_no_token_param(self):
        """Test verify without token parameter - should return 422"""
        response = requests.get(f"{BASE_URL}/api/auth/verify-reset-token")
        assert response.status_code == 422


class TestResetPassword:
    """Test POST /api/auth/reset-password endpoint"""
    
    def test_reset_password_invalid_token(self):
        """Test reset password with invalid token - should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={
                "token": "invalid_token_12345",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
    
    def test_reset_password_short_password(self):
        """Test reset password with too short password - should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={
                "token": "some_token",
                "new_password": "12345"  # Less than 6 characters
            }
        )
        # Will fail with invalid token first, but if token was valid, would fail on password length
        assert response.status_code == 400
    
    def test_reset_password_missing_fields(self):
        """Test reset password with missing fields - should return 422"""
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": "some_token"}  # Missing new_password
        )
        assert response.status_code == 422


class TestForgotPasswordIntegration:
    """Integration tests for the full forgot password flow"""
    
    @pytest.fixture
    def test_user_token(self):
        """Login and get token for test user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_forgot_password_creates_reset_token(self):
        """Test that forgot password creates a reset token in database"""
        # Request password reset
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": TEST_EMAIL}
        )
        assert response.status_code == 200
        # Token is created in database - we can't verify directly without DB access
        # But the endpoint should return success
        data = response.json()
        assert "message" in data
    
    def test_login_still_works_after_forgot_password_request(self):
        """Test that user can still login after requesting password reset"""
        # Request password reset
        requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": TEST_EMAIL}
        )
        
        # User should still be able to login with current password
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data


class TestExistingAuthEndpoints:
    """Verify existing auth endpoints still work"""
    
    def test_login_endpoint(self):
        """Test login endpoint still works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrongpassword"}
        )
        assert response.status_code == 401
    
    def test_me_endpoint_with_auth(self):
        """Test /me endpoint with valid auth"""
        # First login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        token = login_response.json().get("token")
        
        # Then get user info
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
    
    def test_me_endpoint_without_auth(self):
        """Test /me endpoint without auth - should return 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


class TestHealthAndBasicEndpoints:
    """Test basic endpoints are still working"""
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
    
    def test_search_engines_endpoint(self):
        """Test search engines endpoint"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_categories_endpoint(self):
        """Test categories endpoint"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
