"""
Iteration 64 Feature Tests
Tests for:
1. Login flow with admin credentials
2. Ultimate Search page - Comments button on search results
3. Settings page - Content Filtering section (strict/moderate/off)
4. Map View page - Category filter section with checkboxes
5. Map View page - Color-coded dots based on categories
6. Map View page - Filtered results panel at bottom when categories selected
7. Easter Eggs - Protocol Script Recommendations and Protocol Pricing in jokes
8. Theme controls in sidebar - Gallery and Preview buttons
9. Edit Category Modal - Clean Category button functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestAuthFlow:
    """Test authentication flow"""
    
    def test_login_with_admin_credentials(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True, "User should be admin"
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 404], f"Expected 401/404, got {response.status_code}"


class TestContentFiltering:
    """Test Content Filtering settings"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_update_content_filter_strict(self):
        """Test setting content filter to strict"""
        response = requests.put(f"{BASE_URL}/api/users/settings", 
            headers=self.headers,
            json={"content_filter": "strict"}
        )
        assert response.status_code == 200, f"Failed to update settings: {response.text}"
        
    def test_update_content_filter_moderate(self):
        """Test setting content filter to moderate"""
        response = requests.put(f"{BASE_URL}/api/users/settings", 
            headers=self.headers,
            json={"content_filter": "moderate"}
        )
        assert response.status_code == 200, f"Failed to update settings: {response.text}"
        
    def test_update_content_filter_off(self):
        """Test setting content filter to off"""
        response = requests.put(f"{BASE_URL}/api/users/settings", 
            headers=self.headers,
            json={"content_filter": "off"}
        )
        assert response.status_code == 200, f"Failed to update settings: {response.text}"


class TestCategoryAPIs:
    """Test Category APIs including clean category"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_categories(self):
        """Test getting categories list"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        assert response.status_code == 200, f"Failed to get categories: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Categories should be a list"
        
    def test_get_category_results_count(self):
        """Test getting category results count"""
        # First get categories
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        assert response.status_code == 200
        categories = response.json()
        
        if len(categories) > 0:
            cat_id = categories[0]["id"]
            response = requests.get(f"{BASE_URL}/api/categories/{cat_id}/results-count", 
                headers=self.headers)
            assert response.status_code == 200, f"Failed to get results count: {response.text}"
            data = response.json()
            assert "total_results" in data
            assert "exclusive_results" in data
            assert "shared_results" in data
        else:
            pytest.skip("No categories to test")
            
    def test_clean_category_remove_mode(self):
        """Test clean category with remove mode"""
        # First get categories
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        assert response.status_code == 200
        categories = response.json()
        
        if len(categories) > 0:
            cat_id = categories[0]["id"]
            # Test remove mode (doesn't delete results, just unlinks)
            response = requests.post(f"{BASE_URL}/api/categories/{cat_id}/clean?mode=remove", 
                headers=self.headers)
            assert response.status_code == 200, f"Failed to clean category: {response.text}"
            data = response.json()
            assert data["success"] == True
            assert data["mode"] == "remove"
        else:
            pytest.skip("No categories to test")


class TestSearchResultComments:
    """Test Search Result Comments API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_search_results(self):
        """Test getting search results"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search?limit=10", headers=self.headers)
        assert response.status_code == 200, f"Failed to get search results: {response.text}"
        data = response.json()
        assert "results" in data
        
    def test_get_comments_for_result(self):
        """Test getting comments for a search result"""
        # First get search results
        response = requests.get(f"{BASE_URL}/api/ultimate-search?limit=10", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data.get("results", [])) > 0:
            result_id = data["results"][0]["id"]
            response = requests.get(f"{BASE_URL}/api/search-results/{result_id}/comments", 
                headers=self.headers)
            assert response.status_code == 200, f"Failed to get comments: {response.text}"
            comments_data = response.json()
            assert "comments" in comments_data
        else:
            pytest.skip("No search results to test comments on")


class TestThemePresets:
    """Test Theme Preset APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_theme_presets(self):
        """Test getting theme presets"""
        response = requests.get(f"{BASE_URL}/api/theme-presets", headers=self.headers)
        assert response.status_code == 200, f"Failed to get theme presets: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Theme presets should be a list"


class TestMapPageAPIs:
    """Test Map Page related APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_map_results(self):
        """Test getting results for map view"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search?limit=100", headers=self.headers)
        assert response.status_code == 200, f"Failed to get map results: {response.text}"
        data = response.json()
        assert "results" in data
        
    def test_categories_for_filtering(self):
        """Test getting categories for map filtering"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        assert response.status_code == 200, f"Failed to get categories: {response.text}"
        data = response.json()
        assert isinstance(data, list)


class TestEasterEggContent:
    """Test Easter Egg content includes Protocol Script Recommendations and Protocol Pricing"""
    
    def test_easter_egg_rewards_content(self):
        """Verify Easter Egg rewards include Protocol Script Recommendations and Protocol Pricing"""
        # This is a code review test - checking the FloatingEasterEggs.js content
        # The file should contain:
        # 1. Protocol Script Recommendations (type: 'protocol')
        # 2. Protocol Pricing suggestions (type: 'pricing')
        # 3. Jokes about Letters to Evelyn by John Selman
        
        # Read the file content
        import os
        file_path = "/app/frontend/src/components/Gamification/FloatingEasterEggs.js"
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for Protocol Script Recommendations
            assert "Protocol Script Recommendation" in content, "Missing Protocol Script Recommendations"
            assert "type: 'protocol'" in content, "Missing protocol type in EGG_REWARDS"
            
            # Check for Protocol Pricing
            assert "Protocol Pricing" in content, "Missing Protocol Pricing suggestions"
            assert "type: 'pricing'" in content, "Missing pricing type in EGG_REWARDS"
            
            # Check for Letters to Evelyn references
            assert "Letters to Evelyn" in content, "Missing Letters to Evelyn references"
            assert "John Selman" in content, "Missing John Selman references"
            
            # Check for extremely funny jokes
            assert "HYSTERICAL" in content or "EXTREMELY FUNNY" in content or "😂" in content, "Missing funny jokes"
        else:
            pytest.skip("FloatingEasterEggs.js file not found")


class TestUIComponents:
    """Test UI component data-testids exist in code"""
    
    def test_map_page_category_filter_testids(self):
        """Verify Map page has category filter test IDs"""
        file_path = "/app/frontend/src/pages/MapPage.js"
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for category filter section
            assert 'data-testid="category-filter-section"' in content, "Missing category-filter-section testid"
            assert 'data-testid="category-filtered-results"' in content, "Missing category-filtered-results testid"
            assert 'data-testid="clear-category-filter"' in content, "Missing clear-category-filter testid"
        else:
            pytest.skip("MapPage.js file not found")
            
    def test_settings_page_content_filter_testids(self):
        """Verify Settings page has content filter test IDs"""
        file_path = "/app/frontend/src/pages/SettingsPage.js"
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for content filter section
            assert 'data-testid="content-filter-section"' in content, "Missing content-filter-section testid"
            assert 'data-testid="content-filter-strict"' in content, "Missing content-filter-strict testid"
            assert 'data-testid="content-filter-moderate"' in content, "Missing content-filter-moderate testid"
            assert 'data-testid="content-filter-off"' in content, "Missing content-filter-off testid"
        else:
            pytest.skip("SettingsPage.js file not found")
            
    def test_search_results_comments_button_testid(self):
        """Verify Search Results have comments button test ID"""
        file_path = "/app/frontend/src/components/UltimateSearch/SearchResultsList.js"
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for comments button
            assert 'data-testid={`open-comments-' in content or 'data-testid="open-comments' in content, "Missing open-comments testid"
            assert "💬 Comments" in content, "Missing Comments button text"
        else:
            pytest.skip("SearchResultsList.js file not found")
            
    def test_category_modal_clean_button_testid(self):
        """Verify Category Modal has clean category button test ID"""
        file_path = "/app/frontend/src/components/UltimateSearch/CategoryModals.js"
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for clean category button
            assert 'data-testid="clean-category-btn"' in content, "Missing clean-category-btn testid"
            assert "🧹 Clean Category" in content, "Missing Clean Category button text"
        else:
            pytest.skip("CategoryModals.js file not found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
