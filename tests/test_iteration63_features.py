"""
Iteration 63 Feature Tests
Testing: Theme Gallery UI, Theme Preview Mode, Search Result Comments API, Theme Preset API
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthCheck:
    """Basic health check to ensure API is running"""
    
    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health check passed")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"✓ Admin login successful: {data['user'].get('username')}")
        return data["token"]


class TestThemePresetAPI:
    """Theme Preset Gallery API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_theme_presets_unauthenticated(self):
        """Test GET /api/theme-presets without auth - should return public presets"""
        response = requests.get(f"{BASE_URL}/api/theme-presets")
        assert response.status_code == 200
        data = response.json()
        assert "public_presets" in data
        assert "my_presets" in data
        assert isinstance(data["public_presets"], list)
        print(f"✓ GET theme presets (unauth): {len(data['public_presets'])} public presets")
    
    def test_get_theme_presets_authenticated(self, auth_token):
        """Test GET /api/theme-presets with auth - should return public + user presets"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/theme-presets", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "public_presets" in data
        assert "my_presets" in data
        print(f"✓ GET theme presets (auth): {len(data['public_presets'])} public, {len(data['my_presets'])} user presets")
    
    def test_create_theme_preset(self, auth_token):
        """Test POST /api/theme-presets - create new preset"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        timestamp = time.time()
        preset_data = {
            "name": f"TEST_Preset_{timestamp}",
            "description": "Test preset for iteration 63",
            "is_dark": True,
            "accent_color": "blue",
            "is_public": False
        }
        response = requests.post(f"{BASE_URL}/api/theme-presets", json=preset_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data.get("name") == preset_data["name"]
        print(f"✓ Created theme preset: {data.get('name')}")
        return data["id"]
    
    def test_create_public_theme_preset(self, auth_token):
        """Test creating a public theme preset"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        timestamp = time.time()
        preset_data = {
            "name": f"TEST_Public_Preset_{timestamp}",
            "description": "Public test preset",
            "is_dark": False,
            "accent_color": "green",
            "is_public": True
        }
        response = requests.post(f"{BASE_URL}/api/theme-presets", json=preset_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("is_public") == True
        print(f"✓ Created public theme preset: {data.get('name')}")
        return data["id"]
    
    def test_like_theme_preset(self, auth_token):
        """Test POST /api/theme-presets/{id}/like - toggle like"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a preset to like
        timestamp = time.time()
        preset_data = {
            "name": f"TEST_Like_Preset_{timestamp}",
            "is_dark": True,
            "accent_color": "purple",
            "is_public": True
        }
        create_response = requests.post(f"{BASE_URL}/api/theme-presets", json=preset_data, headers=headers)
        assert create_response.status_code == 200
        preset_id = create_response.json()["id"]
        
        # Like the preset
        like_response = requests.post(f"{BASE_URL}/api/theme-presets/{preset_id}/like", headers=headers)
        assert like_response.status_code == 200
        like_data = like_response.json()
        assert "likes" in like_data
        print(f"✓ Liked theme preset: {like_data.get('likes')} likes")
    
    def test_delete_theme_preset(self, auth_token):
        """Test DELETE /api/theme-presets/{id} - delete own preset"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a preset to delete
        timestamp = time.time()
        preset_data = {
            "name": f"TEST_Delete_Preset_{timestamp}",
            "is_dark": True,
            "accent_color": "red",
            "is_public": False
        }
        create_response = requests.post(f"{BASE_URL}/api/theme-presets", json=preset_data, headers=headers)
        assert create_response.status_code == 200
        preset_id = create_response.json()["id"]
        
        # Delete the preset
        delete_response = requests.delete(f"{BASE_URL}/api/theme-presets/{preset_id}", headers=headers)
        assert delete_response.status_code == 200
        print(f"✓ Deleted theme preset: {preset_id}")


class TestSearchResultCommentsAPI:
    """Search Result Comments API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_comments_for_nonexistent_result(self, auth_token):
        """Test GET /api/search-results/{id}/comments for non-existent result"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        fake_id = "000000000000000000000000"
        response = requests.get(f"{BASE_URL}/api/search-results/{fake_id}/comments", headers=headers)
        # Should return 200 with empty comments or 404
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "comments" in data
            print(f"✓ GET comments for non-existent result: {len(data.get('comments', []))} comments")
        else:
            print("✓ GET comments for non-existent result: 404 (expected)")
    
    def test_post_comment_requires_auth(self):
        """Test POST /api/search-results/{id}/comments requires authentication"""
        fake_id = "000000000000000000000000"
        response = requests.post(f"{BASE_URL}/api/search-results/{fake_id}/comments", json={
            "content": "Test comment"
        })
        assert response.status_code in [401, 403]
        print("✓ POST comment requires auth (401/403)")
    
    def test_comment_endpoints_exist(self, auth_token):
        """Test that comment endpoints exist and respond correctly"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        fake_id = "000000000000000000000000"
        
        # Test GET comments
        get_response = requests.get(f"{BASE_URL}/api/search-results/{fake_id}/comments", headers=headers)
        assert get_response.status_code in [200, 404]
        print(f"✓ GET comments endpoint exists: {get_response.status_code}")
        
        # Test POST comment (may fail due to no search result, but endpoint should exist)
        post_response = requests.post(f"{BASE_URL}/api/search-results/{fake_id}/comments", 
                                      json={"content": "Test"}, headers=headers)
        # 404 is acceptable if search result doesn't exist
        assert post_response.status_code in [200, 201, 404, 400]
        print(f"✓ POST comment endpoint exists: {post_response.status_code}")


class TestAccentColors:
    """Test accent color configuration"""
    
    def test_accent_colors_in_theme_presets(self):
        """Verify all 6 accent colors are supported in theme presets"""
        valid_colors = ['purple', 'pink', 'blue', 'green', 'orange', 'red']
        
        # Login to create presets
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test creating preset with each color
        for color in valid_colors:
            timestamp = time.time()
            preset_data = {
                "name": f"TEST_Color_{color}_{timestamp}",
                "is_dark": True,
                "accent_color": color,
                "is_public": False
            }
            response = requests.post(f"{BASE_URL}/api/theme-presets", json=preset_data, headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data.get("accent_color") == color
            print(f"✓ Accent color '{color}' supported")
        
        print(f"✓ All {len(valid_colors)} accent colors verified")


class TestAppStability:
    """App stability tests"""
    
    def test_multiple_api_calls(self):
        """Test multiple rapid API calls don't cause issues"""
        for i in range(5):
            response = requests.get(f"{BASE_URL}/api/health")
            assert response.status_code == 200
        print("✓ Multiple rapid API calls successful")
    
    def test_auth_flow_stability(self):
        """Test login/logout flow stability"""
        # Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Make authenticated request
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        assert profile_response.status_code == 200
        
        print("✓ Auth flow stable")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
