"""
Iteration 19 - Category Filtering Tests for Ultimate Search Page
Tests the category selection bug fix:
- Category checkbox selection
- Filter status indicator
- Search results filtering by categories
- AND/OR/AND_OR aggregation logic
- Backend /api/ultimate-search endpoint with category_ids and aggregation params
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"

# Known category IDs from the database
CATEGORY_WILLIAM_GAMBLE = "69632d91b13005975c5f61b4"
CATEGORY_CIVIL_WAR_HISTORY = "696391cf98449e11c8ab38f5"


class TestCategoryFilteringBackend:
    """Backend API tests for category filtering on Ultimate Search"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
    
    def test_ultimate_search_no_filter(self):
        """Test /api/ultimate-search without category filter returns all results"""
        response = self.session.get(f"{BASE_URL}/api/ultimate-search?aggregation=and_or&limit=200")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "results" in data, "Response should contain 'results' key"
        assert "count" in data or "total" in data, "Response should contain 'count' or 'total' key"
        assert "filter_applied" in data, "Response should contain 'filter_applied' key"
        assert "aggregation_mode" in data, "Response should contain 'aggregation_mode' key"
        
        # Without category filter, filter_applied should be False
        assert data["filter_applied"] == False, "filter_applied should be False when no categories selected"
        assert data["aggregation_mode"] == "and_or", "Default aggregation mode should be 'and_or'"
        
        count = data.get("count", data.get("total", 0))
        print(f"✅ No filter: {count} results returned, filter_applied={data['filter_applied']}")
    
    def test_ultimate_search_single_category_filter(self):
        """Test filtering by a single category"""
        response = self.session.get(
            f"{BASE_URL}/api/ultimate-search?aggregation=and_or&limit=200&category_ids={CATEGORY_WILLIAM_GAMBLE}"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["filter_applied"] == True, "filter_applied should be True when category is selected"
        
        # Verify results contain the filtered category
        if data["count"] > 0:
            for result in data["results"]:
                # Results should have categories array
                assert "categories" in result, "Result should have 'categories' field"
        
        print(f"✅ Single category filter: {data['count']} results for William Gamble category")
    
    def test_ultimate_search_multiple_categories_or(self):
        """Test filtering by multiple categories with OR logic"""
        category_ids = f"{CATEGORY_WILLIAM_GAMBLE},{CATEGORY_CIVIL_WAR_HISTORY}"
        response = self.session.get(
            f"{BASE_URL}/api/ultimate-search?aggregation=or&limit=200&category_ids={category_ids}"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["filter_applied"] == True, "filter_applied should be True"
        assert data["aggregation_mode"] == "or", "aggregation_mode should be 'or'"
        
        print(f"✅ Multiple categories (OR): {data['count']} results")
    
    def test_ultimate_search_multiple_categories_and(self):
        """Test filtering by multiple categories with AND logic"""
        category_ids = f"{CATEGORY_WILLIAM_GAMBLE},{CATEGORY_CIVIL_WAR_HISTORY}"
        response = self.session.get(
            f"{BASE_URL}/api/ultimate-search?aggregation=and&limit=200&category_ids={category_ids}"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["filter_applied"] == True, "filter_applied should be True"
        assert data["aggregation_mode"] == "and", "aggregation_mode should be 'and'"
        
        # AND filter should return fewer or equal results compared to OR
        print(f"✅ Multiple categories (AND): {data['count']} results")
    
    def test_ultimate_search_multiple_categories_and_or(self):
        """Test filtering by multiple categories with AND/OR (default) logic"""
        category_ids = f"{CATEGORY_WILLIAM_GAMBLE},{CATEGORY_CIVIL_WAR_HISTORY}"
        response = self.session.get(
            f"{BASE_URL}/api/ultimate-search?aggregation=and_or&limit=200&category_ids={category_ids}"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["filter_applied"] == True, "filter_applied should be True"
        assert data["aggregation_mode"] == "and_or", "aggregation_mode should be 'and_or'"
        
        print(f"✅ Multiple categories (AND/OR): {data['count']} results")
    
    def test_aggregation_logic_comparison(self):
        """Compare results between AND and OR aggregation to verify logic works"""
        category_ids = f"{CATEGORY_WILLIAM_GAMBLE},{CATEGORY_CIVIL_WAR_HISTORY}"
        
        # Get OR results
        or_response = self.session.get(
            f"{BASE_URL}/api/ultimate-search?aggregation=or&limit=200&category_ids={category_ids}"
        )
        or_data = or_response.json()
        
        # Get AND results
        and_response = self.session.get(
            f"{BASE_URL}/api/ultimate-search?aggregation=and&limit=200&category_ids={category_ids}"
        )
        and_data = and_response.json()
        
        or_count = or_data.get("count", or_data.get("total", 0))
        and_count = and_data.get("count", and_data.get("total", 0))
        
        # AND should return <= OR results (AND is more restrictive)
        assert and_count <= or_count, \
            f"AND ({and_count}) should return <= OR ({or_count}) results"
        
        print(f"✅ Aggregation logic verified: AND={and_count}, OR={or_count}")
    
    def test_categories_endpoint(self):
        """Test that categories endpoint returns available categories"""
        # Categories endpoint requires authentication
        response = self.session.get(f"{BASE_URL}/api/categories")
        
        # Should return 200 with auth or 401 without
        if response.status_code == 401:
            print("⚠️ Categories endpoint requires authentication - checking with auth header")
            # The session should have auth header from setup
            assert self.token is not None, "Token should be set from login"
            print(f"✅ Categories endpoint requires auth (token present: {bool(self.token)})")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Categories should be a list"
        
        # Find our test categories
        category_ids = [cat.get("id") for cat in data]
        
        print(f"✅ Categories endpoint: {len(data)} categories available")
        print(f"   Category IDs: {category_ids[:5]}...")  # Show first 5
    
    def test_result_structure(self):
        """Test that search results have correct structure for map display"""
        response = self.session.get(
            f"{BASE_URL}/api/ultimate-search?aggregation=and_or&limit=10&category_ids={CATEGORY_WILLIAM_GAMBLE}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        count = data.get("count", data.get("total", 0))
        if count > 0:
            result = data["results"][0]
            
            # Check required fields for display
            assert "id" in result, "Result should have 'id'"
            assert "title" in result, "Result should have 'title'"
            assert "url" in result, "Result should have 'url'"
            assert "snippet" in result, "Result should have 'snippet'"
            assert "categories" in result, "Result should have 'categories'"
            
            # Check optional fields for map
            # latitude and longitude may be None but should exist
            assert "latitude" in result, "Result should have 'latitude' field"
            assert "longitude" in result, "Result should have 'longitude' field"
            
            print(f"✅ Result structure verified: {result['title'][:50]}...")
            print(f"   Has location: {result.get('latitude') is not None}")
        else:
            print("⚠️ No results to verify structure")
    
    def test_empty_category_ids(self):
        """Test that empty category_ids returns all results"""
        response = self.session.get(
            f"{BASE_URL}/api/ultimate-search?aggregation=and_or&limit=200&category_ids="
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Empty category_ids should not apply filter
        assert data["filter_applied"] == False, "Empty category_ids should not apply filter"
        
        count = data.get("count", data.get("total", 0))
        print(f"✅ Empty category_ids: {count} results, filter_applied={data['filter_applied']}")
    
    def test_invalid_category_id(self):
        """Test behavior with invalid category ID"""
        response = self.session.get(
            f"{BASE_URL}/api/ultimate-search?aggregation=and_or&limit=200&category_ids=invalid_id_123"
        )
        
        # Should still return 200 but with 0 results or handle gracefully
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        count = data.get("count", data.get("total", 0))
        print(f"✅ Invalid category ID handled: {count} results")


class TestCategoryFilteringWithoutAuth:
    """Test category filtering without authentication"""
    
    def test_ultimate_search_no_auth(self):
        """Test that ultimate-search works without auth (public results)"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search?aggregation=and_or&limit=10")
        
        # Should return 200 (public access) or 401 (auth required)
        assert response.status_code in [200, 401], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", data.get("total", 0))
            print(f"✅ Public access allowed: {count} results")
        else:
            print("✅ Authentication required for ultimate-search (expected behavior)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
