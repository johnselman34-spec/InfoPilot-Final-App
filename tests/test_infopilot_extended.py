"""
InfoPilot Extended API Tests - Iteration 2
Tests for: Edge cases, error handling, and additional features
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://explorer-social.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "john@infojet.com"
TEST_PASSWORD = "password123"


class TestEdgeCases:
    """Edge case and error handling tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_nonexistent_category(self, auth_token):
        """Test getting a category that doesn't exist"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/categories/{fake_id}",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 404
    
    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
    
    def test_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        response = requests.get(f"{BASE_URL}/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_12345"})
        assert response.status_code == 401


class TestSearchFunctionality:
    """Search functionality tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_protocol_validation(self, auth_token):
        """Test protocol validation endpoint"""
        response = requests.post(f"{BASE_URL}/api/protocol/validate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"protocol_string": "(test or example) & (keyword)"})
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data


class TestUltimateSearchFeatures:
    """Ultimate Search page feature tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_photos(self, auth_token):
        """Test getting photos for Ultimate Search page"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/photos",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "photos" in data
        assert "max_allowed" in data  # Fixed: API returns max_allowed not max_photos


class TestSafetyFeatures:
    """Safety and security feature tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_safe_browsing_check_url(self, auth_token):
        """Test Safe Browsing URL check (requires auth)"""
        response = requests.post(f"{BASE_URL}/api/safety/check",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"urls": ["https://google.com"]})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or "safe" in data or "unsafe_urls" in data


class TestCategoryTree:
    """Category tree structure tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_category_tree(self, auth_token):
        """Test getting hierarchical category tree"""
        response = requests.get(f"{BASE_URL}/api/categories/tree",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
    
    def test_get_categories_with_counts(self, auth_token):
        """Test getting categories with result counts"""
        response = requests.get(f"{BASE_URL}/api/categories/with-counts",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
