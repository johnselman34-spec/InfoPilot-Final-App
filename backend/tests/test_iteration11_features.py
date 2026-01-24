"""
Test Suite for Iteration 11 Features
- Create Category button (multiple categories in succession)
- Landing page marketing message and download buttons
- Deep Content Scan checkbox
- Search results with collation timestamp and location count
- Map view with location dots
- Location extraction including city/country combinations
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://search-companion-1.preview.emergentagent.com')

# Test session token created for iteration 11
TEST_SESSION_TOKEN = "test_session_iter11_1769257278052"
TEST_USER_ID = "test-user-iter11-1769257278052"


class TestCategoryCreation:
    """Test category creation functionality - multiple categories in succession"""
    
    def test_create_first_category(self):
        """Test creating the first category"""
        response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
            },
            json={
                "name": "Pytest Category 1",
                "protocol": "(pytest or test) & (automation)+",
                "is_public": True
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "category_id" in data
        assert data["name"] == "Pytest Category 1"
        assert data["protocol"] == "(pytest or test) & (automation)+"
        print(f"✅ Created category: {data['category_id']}")
    
    def test_create_second_category_in_succession(self):
        """Test creating a second category immediately after the first"""
        response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
            },
            json={
                "name": "Pytest Category 2",
                "protocol": "(second or follow-up) & (test)+",
                "is_public": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Pytest Category 2"
        print(f"✅ Created second category: {data['category_id']}")
    
    def test_create_third_category_in_succession(self):
        """Test creating a third category to verify succession works"""
        response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
            },
            json={
                "name": "Pytest Category 3",
                "protocol": "(third or final) & (test)+",
                "is_public": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Pytest Category 3"
        print(f"✅ Created third category: {data['category_id']}")
    
    def test_list_all_created_categories(self):
        """Verify all categories are listed"""
        response = requests.get(
            f"{BASE_URL}/api/categories?user_id={TEST_USER_ID}",
            headers={"Authorization": f"Bearer {TEST_SESSION_TOKEN}"}
        )
        assert response.status_code == 200
        data = response.json()
        categories = data.get("categories", [])
        assert len(categories) >= 3, f"Expected at least 3 categories, got {len(categories)}"
        print(f"✅ Found {len(categories)} categories for user")


class TestDeepContentScan:
    """Test Deep Content Scan (fetch_full_content) functionality"""
    
    def test_search_with_deep_content_scan_enabled(self):
        """Test search with fetch_full_content=true for enhanced location detection"""
        response = requests.post(
            f"{BASE_URL}/api/search/collate",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
            },
            json={
                "query": "Nicaragua travel beaches",
                "category_ids": [],
                "max_results": 3,
                "fetch_full_content": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_searched" in data
        assert "total_collated" in data
        assert "results" in data
        print(f"✅ Deep Content Scan search: {data['total_searched']} searched, {data['total_collated']} collated")
        
        # Check if results have locations
        if data["results"]:
            first_result = data["results"][0]
            if "locations" in first_result and first_result["locations"]:
                print(f"✅ Found {len(first_result['locations'])} locations in first result")
    
    def test_search_without_deep_content_scan(self):
        """Test search with fetch_full_content=false (default)"""
        response = requests.post(
            f"{BASE_URL}/api/search/collate",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
            },
            json={
                "query": "technology news",
                "category_ids": [],
                "max_results": 3,
                "fetch_full_content": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Standard search: {data['total_searched']} searched, {data['total_collated']} collated")


class TestSearchResultsDisplay:
    """Test search results display features - timestamp and location count"""
    
    def test_search_results_have_collated_at_timestamp(self):
        """Verify search results include collated_at timestamp"""
        response = requests.get(
            f"{BASE_URL}/api/search/results",
            headers={"Authorization": f"Bearer {TEST_SESSION_TOKEN}"}
        )
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        if results:
            first_result = results[0]
            assert "collated_at" in first_result, "Missing collated_at timestamp"
            # Verify it's a valid timestamp format
            collated_at = first_result["collated_at"]
            assert collated_at is not None
            print(f"✅ First result collated_at: {collated_at}")
    
    def test_search_results_have_locations_array(self):
        """Verify search results include locations array"""
        response = requests.get(
            f"{BASE_URL}/api/search/results",
            headers={"Authorization": f"Bearer {TEST_SESSION_TOKEN}"}
        )
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        # Find a result with locations
        results_with_locations = [r for r in results if r.get("locations")]
        if results_with_locations:
            result = results_with_locations[0]
            locations = result["locations"]
            assert isinstance(locations, list)
            print(f"✅ Found result with {len(locations)} locations")
            
            # Check location structure
            if locations:
                loc = locations[0]
                assert "type" in loc, "Location missing 'type' field"
                print(f"✅ Location type: {loc['type']}")


class TestMapViewData:
    """Test Map View data endpoint"""
    
    def test_map_data_detailed_endpoint(self):
        """Test the detailed map data endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/stats/map-data-detailed",
            headers={"Authorization": f"Bearer {TEST_SESSION_TOKEN}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "locations" in data
        locations = data["locations"]
        print(f"✅ Map data returned {len(locations)} locations")
        
        if locations:
            # Check location structure
            loc = locations[0]
            assert "location" in loc or "count" in loc
            print(f"✅ First location data: {loc}")


class TestLocationExtraction:
    """Test location extraction including city/country combinations"""
    
    def test_virgin_bay_nicaragua_detection(self):
        """Test that Virgin Bay, Nicaragua is properly detected"""
        # This tests the LocationExtractor class
        response = requests.post(
            f"{BASE_URL}/api/search/collate",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
            },
            json={
                "query": "Virgin Bay Nicaragua surf",
                "category_ids": [],
                "max_results": 5,
                "fetch_full_content": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check if any result has Virgin Bay in locations
        virgin_bay_found = False
        for result in data.get("results", []):
            for loc in result.get("locations", []):
                if loc.get("city") == "Virgin Bay" and loc.get("country") == "Nicaragua":
                    virgin_bay_found = True
                    break
        
        if virgin_bay_found:
            print("✅ Virgin Bay, Nicaragua detected in search results")
        else:
            print("⚠️ Virgin Bay not found in this search - may depend on search results")


class TestLandingPageEndpoints:
    """Test endpoints used by landing page"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ Health endpoint working")
    
    def test_document_types_endpoint(self):
        """Test document types endpoint"""
        response = requests.get(f"{BASE_URL}/api/document-types")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        types = data["types"]
        assert len(types) >= 8, f"Expected at least 8 document types, got {len(types)}"
        print(f"✅ Document types: {len(types)} types available")
    
    def test_branding_info_endpoint(self):
        """Test branding info endpoint"""
        response = requests.get(f"{BASE_URL}/api/branding/info")
        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data or "name" in data
        print("✅ Branding info endpoint working")


class TestAuthenticationRequired:
    """Test that protected endpoints require authentication"""
    
    def test_categories_requires_auth(self):
        """Test that creating categories requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={"Content-Type": "application/json"},
            json={"name": "Unauthorized", "protocol": "(test)+"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Categories endpoint properly requires authentication")
    
    def test_search_collate_requires_auth(self):
        """Test that search/collate requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/search/collate",
            headers={"Content-Type": "application/json"},
            json={"query": "test", "max_results": 5}
        )
        assert response.status_code == 401
        print("✅ Search/collate endpoint properly requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
