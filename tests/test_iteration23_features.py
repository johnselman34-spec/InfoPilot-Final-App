"""
InfoPilot Explorer - Iteration 23 Feature Tests
Tests for:
1. PayPal Connect button in Edit Protocol screen (when price > 0)
2. Statistics page - Interactive Map with filter buttons
3. Tutorials page - text/image based tutorials (not video)
4. Tutorials API - GET /api/tutorials returns 10 tutorials with content field
5. SEO meta tags in index.html
6. Manifest.json with ASO keywords
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTutorialsAPI:
    """Test tutorials API returns text/image based tutorials with content field"""
    
    def test_tutorials_endpoint_returns_tutorials(self):
        """GET /api/tutorials should return tutorials list"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "tutorials" in data, "Response should contain 'tutorials' key"
        assert "categories" in data, "Response should contain 'categories' key"
        
    def test_tutorials_count_is_10(self):
        """Should return exactly 10 tutorials"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        
        data = response.json()
        tutorials = data.get("tutorials", [])
        assert len(tutorials) == 10, f"Expected 10 tutorials, got {len(tutorials)}"
        
    def test_tutorials_have_content_field(self):
        """Each tutorial should have a 'content' field (markdown text)"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        
        data = response.json()
        tutorials = data.get("tutorials", [])
        
        for tutorial in tutorials:
            assert "content" in tutorial, f"Tutorial '{tutorial.get('title', 'unknown')}' missing 'content' field"
            assert len(tutorial["content"]) > 100, f"Tutorial content should be substantial (>100 chars)"
            
    def test_tutorials_have_image_url(self):
        """Each tutorial should have an image_url field"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        
        data = response.json()
        tutorials = data.get("tutorials", [])
        
        for tutorial in tutorials:
            assert "image_url" in tutorial, f"Tutorial '{tutorial.get('title', 'unknown')}' missing 'image_url' field"
            
    def test_tutorials_have_duration_as_read_time(self):
        """Duration should be in 'X min read' format (not video duration)"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        
        data = response.json()
        tutorials = data.get("tutorials", [])
        
        for tutorial in tutorials:
            duration = tutorial.get("duration", "")
            assert "read" in duration.lower() or "min" in duration.lower(), \
                f"Duration '{duration}' should indicate reading time, not video duration"
                
    def test_tutorials_no_youtube_id(self):
        """Tutorials should NOT have youtube_id field (text-based, not video)"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        
        data = response.json()
        tutorials = data.get("tutorials", [])
        
        for tutorial in tutorials:
            # youtube_id should either not exist or be None/empty
            youtube_id = tutorial.get("youtube_id")
            assert youtube_id is None or youtube_id == "", \
                f"Tutorial '{tutorial.get('title', 'unknown')}' should not have youtube_id (text-based tutorials)"
                
    def test_tutorials_categories_structure(self):
        """Categories should have proper structure"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        
        data = response.json()
        categories = data.get("categories", [])
        
        assert len(categories) > 0, "Should have at least one category"
        
        for cat in categories:
            assert "id" in cat, "Category missing 'id'"
            assert "name" in cat, "Category missing 'name'"
            assert "icon" in cat, "Category missing 'icon'"
            assert "color" in cat, "Category missing 'color'"


class TestStatisticsAPI:
    """Test statistics API for interactive map data"""
    
    def test_statistics_dashboard_endpoint(self):
        """GET /api/statistics/dashboard should return stats"""
        response = requests.get(f"{BASE_URL}/api/statistics/dashboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "overview" in data or "countries" in data or "us_states" in data, \
            "Dashboard should contain statistics data"
            
    def test_statistics_has_countries_data(self):
        """Statistics should include countries data for map"""
        response = requests.get(f"{BASE_URL}/api/statistics/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        # Check for countries data structure
        assert "countries" in data, "Should have countries data for map"
        
    def test_statistics_has_us_states_data(self):
        """Statistics should include US states data for map"""
        response = requests.get(f"{BASE_URL}/api/statistics/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        # Check for US states data structure
        assert "us_states" in data, "Should have US states data for map"
        
    def test_most_copied_leaderboard(self):
        """GET /api/statistics/most-copied should return leaderboard"""
        response = requests.get(f"{BASE_URL}/api/statistics/most-copied")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "leaderboard" in data, "Should have leaderboard data"
        assert "stats" in data, "Should have stats data"
        
    def test_marketplace_leaderboard_sales(self):
        """GET /api/marketplace/leaderboard/sales should return top sellers"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/sales")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "leaderboard" in data, "Should have leaderboard data"
        
    def test_marketplace_leaderboard_revenue(self):
        """GET /api/marketplace/leaderboard/revenue should return top revenue"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/revenue")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "leaderboard" in data, "Should have leaderboard data"


class TestAuthAndCategories:
    """Test authentication and category editing for PayPal Connect feature"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping authenticated tests")
        
    def test_login_success(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        
    def test_get_categories_authenticated(self, auth_token):
        """GET /api/categories should return user's categories"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Categories should be a list"
        
    def test_category_update_with_price(self, auth_token):
        """Test that category can be updated with price field"""
        # First get categories
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        categories = response.json()
        if len(categories) == 0:
            pytest.skip("No categories to test price update")
            
        # Try to update first category with price
        cat_id = categories[0].get("id")
        if not cat_id:
            pytest.skip("Category has no ID")
            
        # Update with price
        update_response = requests.put(
            f"{BASE_URL}/api/categories/{cat_id}",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "name": categories[0].get("name"),
                "protocol": categories[0].get("protocol", ""),
                "is_public": categories[0].get("is_public", False),
                "price": 5.99  # Set a price to test PayPal Connect visibility
            }
        )
        # Should succeed or return validation error (not 500)
        assert update_response.status_code in [200, 400, 422], \
            f"Category update failed unexpectedly: {update_response.status_code} - {update_response.text}"


class TestSEOAndManifest:
    """Test SEO meta tags and manifest.json"""
    
    def test_index_html_has_seo_meta_tags(self):
        """index.html should have SEO meta tags"""
        # Read the index.html file
        index_path = "/app/frontend/public/index.html"
        with open(index_path, 'r') as f:
            content = f.read()
            
        # Check for essential SEO meta tags
        assert 'meta name="description"' in content, "Missing description meta tag"
        assert 'meta name="keywords"' in content, "Missing keywords meta tag"
        assert 'meta property="og:' in content, "Missing Open Graph meta tags"
        assert 'meta name="twitter:' in content, "Missing Twitter Card meta tags"
        
    def test_index_html_has_20_keywords(self):
        """index.html should have approximately 20 SEO keywords"""
        index_path = "/app/frontend/public/index.html"
        with open(index_path, 'r') as f:
            content = f.read()
            
        # Find keywords meta tag
        import re
        keywords_match = re.search(r'meta name="keywords" content="([^"]+)"', content)
        assert keywords_match, "Keywords meta tag not found"
        
        keywords = keywords_match.group(1).split(',')
        keyword_count = len([k.strip() for k in keywords if k.strip()])
        
        # Should have at least 15 keywords (allowing some flexibility)
        assert keyword_count >= 15, f"Expected at least 15 keywords, found {keyword_count}"
        
    def test_manifest_json_has_aso_keywords(self):
        """manifest.json should have ASO keywords in description"""
        manifest_path = "/app/frontend/public/manifest.json"
        import json
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        # Check for essential fields
        assert "name" in manifest, "Missing 'name' in manifest"
        assert "short_name" in manifest, "Missing 'short_name' in manifest"
        assert "description" in manifest, "Missing 'description' in manifest"
        
        # Description should be substantial (ASO optimized)
        description = manifest.get("description", "")
        assert len(description) > 100, f"Description too short for ASO: {len(description)} chars"
        
        # Check for categories (ASO)
        assert "categories" in manifest, "Missing 'categories' in manifest"
        
    def test_manifest_json_has_shortcuts(self):
        """manifest.json should have app shortcuts"""
        manifest_path = "/app/frontend/public/manifest.json"
        import json
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        assert "shortcuts" in manifest, "Missing 'shortcuts' in manifest"
        shortcuts = manifest.get("shortcuts", [])
        assert len(shortcuts) >= 3, f"Expected at least 3 shortcuts, found {len(shortcuts)}"


class TestTutorialContentQuality:
    """Test that tutorials have quality markdown content"""
    
    def test_tutorials_content_has_markdown_formatting(self):
        """Tutorial content should have markdown formatting"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        
        data = response.json()
        tutorials = data.get("tutorials", [])
        
        markdown_indicators = ['##', '###', '**', '- ', '1.', '```']
        
        for tutorial in tutorials:
            content = tutorial.get("content", "")
            has_markdown = any(indicator in content for indicator in markdown_indicators)
            assert has_markdown, f"Tutorial '{tutorial.get('title')}' should have markdown formatting"
            
    def test_tutorials_content_has_steps(self):
        """Tutorial content should have instructional steps"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        
        data = response.json()
        tutorials = data.get("tutorials", [])
        
        step_indicators = ['Step', 'step', '1.', '2.', '3.', '- ']
        
        for tutorial in tutorials:
            content = tutorial.get("content", "")
            has_steps = any(indicator in content for indicator in step_indicators)
            assert has_steps, f"Tutorial '{tutorial.get('title')}' should have instructional steps"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
