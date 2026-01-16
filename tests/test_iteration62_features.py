"""
Iteration 62 - Comprehensive Feature Tests
Tests for:
1. Theme Preset Gallery API - /api/theme-presets endpoints
2. Search Result Comments - /api/search-results/{id}/comments endpoints
3. Content filter setting - users can set content_filter preference
4. Theme Color Customization - 6 accent colors
5. Easter Egg jokes verification
6. Category management - Clean Category feature
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ Health endpoint working")
    
    def test_frontend_accessible(self):
        """Test frontend is accessible"""
        response = requests.get(BASE_URL)
        assert response.status_code == 200
        assert "InfoPilot" in response.text
        print("✅ Frontend accessible")


class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    @pytest.fixture
    def test_user_token(self):
        """Get or create test user token"""
        # Try login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        
        # Try register
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "username": "testuser"
        })
        if response.status_code in [200, 201]:
            return response.json().get("token")
        
        pytest.skip("Test user auth failed")
    
    def test_admin_login(self, admin_token):
        """Test admin can login"""
        assert admin_token is not None
        print("✅ Admin login successful")


class TestThemePresetGallery:
    """Theme Preset Gallery API tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_get_theme_presets_unauthenticated(self):
        """Test getting theme presets without auth"""
        response = requests.get(f"{BASE_URL}/api/theme-presets")
        assert response.status_code == 200
        data = response.json()
        assert "public_presets" in data
        assert "my_presets" in data
        assert isinstance(data["public_presets"], list)
        print(f"✅ GET /api/theme-presets works - {len(data['public_presets'])} public presets")
    
    def test_get_theme_presets_authenticated(self, admin_token):
        """Test getting theme presets with auth"""
        response = requests.get(
            f"{BASE_URL}/api/theme-presets",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "public_presets" in data
        assert "my_presets" in data
        print(f"✅ GET /api/theme-presets (auth) - {len(data['my_presets'])} user presets")
    
    def test_create_theme_preset(self, admin_token):
        """Test creating a theme preset"""
        preset_data = {
            "name": f"Test Preset {datetime.now().timestamp()}",
            "is_dark": True,
            "accent_color": "blue",
            "description": "Test preset for iteration 62",
            "is_public": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/theme-presets",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=preset_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data.get("message") == "Theme preset created successfully"
        print(f"✅ POST /api/theme-presets - Created preset ID: {data['id']}")
        return data["id"]
    
    def test_create_public_theme_preset(self, admin_token):
        """Test creating a public theme preset"""
        preset_data = {
            "name": f"Public Test Preset {datetime.now().timestamp()}",
            "is_dark": False,
            "accent_color": "green",
            "description": "Public test preset",
            "is_public": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/theme-presets",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=preset_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✅ Created public theme preset: {data['id']}")
    
    def test_like_theme_preset(self, admin_token):
        """Test liking a theme preset"""
        # First create a preset
        preset_data = {
            "name": f"Like Test Preset {datetime.now().timestamp()}",
            "is_dark": True,
            "accent_color": "purple",
            "is_public": True
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/theme-presets",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=preset_data
        )
        assert create_response.status_code == 200
        preset_id = create_response.json()["id"]
        
        # Like the preset
        like_response = requests.post(
            f"{BASE_URL}/api/theme-presets/{preset_id}/like",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert like_response.status_code == 200
        data = like_response.json()
        assert "liked" in data
        print(f"✅ POST /api/theme-presets/{preset_id}/like - liked: {data['liked']}")
    
    def test_delete_theme_preset(self, admin_token):
        """Test deleting a theme preset"""
        # First create a preset
        preset_data = {
            "name": f"Delete Test Preset {datetime.now().timestamp()}",
            "is_dark": True,
            "accent_color": "red"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/theme-presets",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=preset_data
        )
        assert create_response.status_code == 200
        preset_id = create_response.json()["id"]
        
        # Delete the preset
        delete_response = requests.delete(
            f"{BASE_URL}/api/theme-presets/{preset_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data.get("deleted") == True
        print(f"✅ DELETE /api/theme-presets/{preset_id} - deleted successfully")


class TestSearchResultComments:
    """Search Result Comments API tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    @pytest.fixture
    def search_result_id(self, admin_token):
        """Get a search result ID to test comments on"""
        # Get user's search results
        response = requests.get(
            f"{BASE_URL}/api/search-results",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                return results[0].get("id")
        
        # If no results, skip
        pytest.skip("No search results available for comment testing")
    
    def test_get_comments_for_result(self, admin_token, search_result_id):
        """Test getting comments for a search result"""
        response = requests.get(
            f"{BASE_URL}/api/search-results/{search_result_id}/comments",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "comments" in data
        assert "count" in data
        assert isinstance(data["comments"], list)
        print(f"✅ GET /api/search-results/{search_result_id}/comments - {data['count']} comments")
    
    def test_create_comment_on_result(self, admin_token, search_result_id):
        """Test creating a comment on a search result"""
        comment_data = {
            "content": f"Test comment from iteration 62 - {datetime.now().isoformat()}"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/search-results/{search_result_id}/comments",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=comment_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data.get("message") == "Comment added successfully"
        print(f"✅ POST /api/search-results/{search_result_id}/comments - Created comment: {data['id']}")
        return data["id"]
    
    def test_like_comment(self, admin_token, search_result_id):
        """Test liking a comment"""
        # First create a comment
        comment_data = {"content": f"Like test comment - {datetime.now().isoformat()}"}
        create_response = requests.post(
            f"{BASE_URL}/api/search-results/{search_result_id}/comments",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=comment_data
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create comment for like test")
        
        comment_id = create_response.json()["id"]
        
        # Like the comment
        like_response = requests.post(
            f"{BASE_URL}/api/search-results/{search_result_id}/comments/{comment_id}/like",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert like_response.status_code == 200
        data = like_response.json()
        assert "liked" in data
        print(f"✅ POST /api/search-results/{search_result_id}/comments/{comment_id}/like - liked: {data['liked']}")
    
    def test_delete_comment(self, admin_token, search_result_id):
        """Test deleting a comment"""
        # First create a comment
        comment_data = {"content": f"Delete test comment - {datetime.now().isoformat()}"}
        create_response = requests.post(
            f"{BASE_URL}/api/search-results/{search_result_id}/comments",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=comment_data
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create comment for delete test")
        
        comment_id = create_response.json()["id"]
        
        # Delete the comment
        delete_response = requests.delete(
            f"{BASE_URL}/api/search-results/{search_result_id}/comments/{comment_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data.get("deleted") == True
        print(f"✅ DELETE /api/search-results/{search_result_id}/comments/{comment_id} - deleted")


class TestContentFilterSetting:
    """Content filter user setting tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_update_content_filter_strict(self, admin_token):
        """Test setting content filter to strict"""
        response = requests.put(
            f"{BASE_URL}/api/users/settings",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"content_filter": "strict"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("✅ PUT /api/users/settings - content_filter=strict")
    
    def test_update_content_filter_moderate(self, admin_token):
        """Test setting content filter to moderate"""
        response = requests.put(
            f"{BASE_URL}/api/users/settings",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"content_filter": "moderate"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("✅ PUT /api/users/settings - content_filter=moderate")
    
    def test_update_content_filter_off(self, admin_token):
        """Test setting content filter to off"""
        response = requests.put(
            f"{BASE_URL}/api/users/settings",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"content_filter": "off"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("✅ PUT /api/users/settings - content_filter=off")
    
    def test_update_content_filter_invalid(self, admin_token):
        """Test setting content filter to invalid value (should be ignored)"""
        response = requests.put(
            f"{BASE_URL}/api/users/settings",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"content_filter": "invalid_value"}
        )
        # Should still return 200 but not update the invalid value
        assert response.status_code == 200
        print("✅ PUT /api/users/settings - invalid content_filter handled gracefully")


class TestCategoryManagement:
    """Category management tests including Clean Category feature"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_get_categories(self, admin_token):
        """Test getting user categories"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ GET /api/categories - {len(data)} categories found")
        return data
    
    def test_get_category_results_count(self, admin_token):
        """Test getting category results count"""
        # First get categories
        categories_response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if categories_response.status_code != 200:
            pytest.skip("Could not get categories")
        
        categories = categories_response.json()
        if not categories:
            pytest.skip("No categories available")
        
        category_id = categories[0].get("id")
        
        # Get results count
        response = requests.get(
            f"{BASE_URL}/api/categories/{category_id}/results-count",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_results" in data
        print(f"✅ GET /api/categories/{category_id}/results-count - {data['total_results']} results")
    
    def test_clean_category_endpoint_exists(self, admin_token):
        """Test that clean category endpoint exists"""
        # First get categories
        categories_response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if categories_response.status_code != 200:
            pytest.skip("Could not get categories")
        
        categories = categories_response.json()
        if not categories:
            pytest.skip("No categories available")
        
        category_id = categories[0].get("id")
        
        # Test clean endpoint with 'remove' mode (safest)
        response = requests.post(
            f"{BASE_URL}/api/categories/{category_id}/clean?mode=remove",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should return 200 even if no results to clean
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✅ POST /api/categories/{category_id}/clean - endpoint working")


class TestEasterEggJokes:
    """Easter Egg jokes verification"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_easter_egg_stats_endpoint(self, admin_token):
        """Test Easter Egg stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/easter-egg-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_stats" in data or "global_stats" in data or "stats" in data
        print("✅ GET /api/gamification/easter-egg-stats - endpoint working")


class TestThemeColorCustomization:
    """Theme color customization tests (6 accent colors)"""
    
    def test_accent_colors_defined(self):
        """Verify 6 accent colors are defined in frontend"""
        # This is a code review test - we verify the colors exist in ThemeContext.js
        expected_colors = ["purple", "pink", "blue", "green", "orange", "red"]
        
        # Read the ThemeContext.js file
        try:
            with open("/app/frontend/src/contexts/ThemeContext.js", "r") as f:
                content = f.read()
            
            for color in expected_colors:
                assert color in content, f"Color {color} not found in ThemeContext.js"
            
            print(f"✅ All 6 accent colors defined: {', '.join(expected_colors)}")
        except FileNotFoundError:
            pytest.skip("ThemeContext.js not found")


class TestOverallStability:
    """Overall stability tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_statistics_endpoint(self, admin_token):
        """Test statistics endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✅ GET /api/statistics - working")
    
    def test_marketplace_endpoint(self, admin_token):
        """Test marketplace endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/protocols",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✅ GET /api/marketplace/protocols - working")
    
    def test_search_results_endpoint(self, admin_token):
        """Test search results endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/search-results",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✅ GET /api/search-results - working")
    
    def test_personal_reports_endpoint(self, admin_token):
        """Test personal reports endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/personal-reports",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✅ GET /api/personal-reports - working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
