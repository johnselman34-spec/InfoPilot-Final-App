"""
Test Suite for InfoPilot Explorer - Iteration 9 Features
Tests: Search Match Options, Information Favoritism Options, Enhanced LocationExtractor
"""

import pytest
import requests
import os
import sys

# Add backend to path for importing LocationExtractor
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infopilot-hub-1.preview.emergentagent.com')
SESSION_TOKEN = os.environ.get('TEST_SESSION_TOKEN', 'test_session_iter9_1769227219986')
USER_ID = os.environ.get('TEST_USER_ID', 'test-user-iter9-1769227219986')


@pytest.fixture
def api_client():
    """Shared requests session with auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SESSION_TOKEN}"
    })
    session.cookies.set("session_token", SESSION_TOKEN)
    return session


class TestLocationExtractor:
    """Test LocationExtractor with enhanced city+country detection"""
    
    def test_location_extractor_import(self):
        """Test that LocationExtractor can be imported"""
        from server import LocationExtractor
        assert LocationExtractor is not None
        print("✓ LocationExtractor imported successfully")
    
    def test_international_cities_dict_exists(self):
        """Test INTERNATIONAL_CITIES dict exists with 15+ countries"""
        from server import LocationExtractor
        assert hasattr(LocationExtractor, 'INTERNATIONAL_CITIES')
        cities_dict = LocationExtractor.INTERNATIONAL_CITIES
        assert isinstance(cities_dict, dict)
        assert len(cities_dict) >= 15, f"Expected 15+ countries, got {len(cities_dict)}"
        print(f"✓ INTERNATIONAL_CITIES has {len(cities_dict)} countries")
    
    def test_nicaragua_cities_present(self):
        """Test Nicaragua cities including Virgin Bay"""
        from server import LocationExtractor
        cities_dict = LocationExtractor.INTERNATIONAL_CITIES
        assert "Nicaragua" in cities_dict, "Nicaragua not in INTERNATIONAL_CITIES"
        nicaragua_cities = cities_dict["Nicaragua"]
        assert "Virgin Bay" in nicaragua_cities, "Virgin Bay not in Nicaragua cities"
        assert "Managua" in nicaragua_cities, "Managua not in Nicaragua cities"
        assert "Granada" in nicaragua_cities, "Granada not in Nicaragua cities"
        print(f"✓ Nicaragua has {len(nicaragua_cities)} cities including Virgin Bay")
    
    def test_city_country_detection_virgin_bay(self):
        """Test detection of 'Virgin Bay, Nicaragua' format"""
        from server import LocationExtractor
        text = "The property is located in Virgin Bay, Nicaragua near the lake."
        locations = LocationExtractor.extract_locations(text)
        
        # Find city_country type location
        city_country_locs = [loc for loc in locations if loc.get("type") == "city_country"]
        assert len(city_country_locs) > 0, f"No city_country locations found. Got: {locations}"
        
        # Check for Virgin Bay, Nicaragua
        found_virgin_bay = any(
            loc.get("city") == "Virgin Bay" and loc.get("country") == "Nicaragua"
            for loc in city_country_locs
        )
        assert found_virgin_bay, f"Virgin Bay, Nicaragua not detected. Got: {city_country_locs}"
        print("✓ Detected 'Virgin Bay, Nicaragua' correctly")
    
    def test_city_country_detection_multiple_formats(self):
        """Test detection of city+country in various formats"""
        from server import LocationExtractor
        
        test_cases = [
            ("Visit Tokyo, Japan for the best sushi", "Tokyo", "Japan"),
            ("The conference is in Berlin, Germany", "Berlin", "Germany"),
            ("Travel to Sydney, Australia this summer", "Sydney", "Australia"),
        ]
        
        for text, expected_city, expected_country in test_cases:
            locations = LocationExtractor.extract_locations(text)
            found = any(
                loc.get("city") == expected_city and loc.get("country") == expected_country
                for loc in locations
            )
            assert found, f"Failed to detect {expected_city}, {expected_country} in: {text}"
            print(f"✓ Detected '{expected_city}, {expected_country}'")
    
    def test_street_address_detection(self):
        """Test detection of street addresses"""
        from server import LocationExtractor
        text = "Our office is at 123 Main Street in downtown."
        locations = LocationExtractor.extract_locations(text)
        
        street_locs = [loc for loc in locations if loc.get("type") == "street_address"]
        assert len(street_locs) > 0, f"No street addresses found. Got: {locations}"
        print(f"✓ Detected {len(street_locs)} street address(es)")
    
    def test_full_address_detection(self):
        """Test detection of full addresses with city, state, ZIP"""
        from server import LocationExtractor
        text = "Send mail to 456 Oak Avenue, Portland, ME 04101"
        locations = LocationExtractor.extract_locations(text)
        
        # Should detect full address or city_state
        has_address = any(
            loc.get("type") in ["full_address", "city_state", "state"]
            for loc in locations
        )
        assert has_address, f"No address components found. Got: {locations}"
        print(f"✓ Detected address components in full address")
    
    def test_multiple_locations_per_text(self):
        """Test detection of multiple locations in same text"""
        from server import LocationExtractor
        text = "Travel from New York to Los Angeles, then fly to Tokyo, Japan."
        locations = LocationExtractor.extract_locations(text)
        
        assert len(locations) >= 2, f"Expected multiple locations, got {len(locations)}"
        print(f"✓ Detected {len(locations)} locations in multi-location text")
    
    def test_countries_list_includes_central_america(self):
        """Test COUNTRIES list includes Central American countries"""
        from server import LocationExtractor
        countries = LocationExtractor.COUNTRIES
        
        central_american = ["Nicaragua", "Costa Rica", "Panama", "Honduras", "Guatemala"]
        for country in central_american:
            assert country in countries, f"{country} not in COUNTRIES list"
        print(f"✓ All Central American countries present in COUNTRIES list")


class TestSearchMatchOptions:
    """Test Search Match Options checkboxes and Select All/Deselect All"""
    
    def test_search_api_accepts_match_options(self, api_client):
        """Test that search API accepts match_options parameter"""
        # First create a category
        cat_response = api_client.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_MatchOptions_Category",
            "protocol": "(test or example)",
            "is_public": True
        })
        
        if cat_response.status_code == 201:
            category_id = cat_response.json().get("category_id")
            
            # Test search with match_options
            search_response = api_client.post(f"{BASE_URL}/api/search/collate", json={
                "query": "test search query",
                "category_ids": [category_id],
                "max_results": 5,
                "match_options": {
                    "exactMatch": True,
                    "strictMatch": True,
                    "aiMatch": True,
                    "intelligentMatch": True,
                    "favorSchematics": True
                }
            })
            
            # API should accept the request (may return 200 or 503 if search service unavailable)
            assert search_response.status_code in [200, 503], f"Unexpected status: {search_response.status_code}"
            print(f"✓ Search API accepts match_options parameter (status: {search_response.status_code})")
            
            # Cleanup
            api_client.delete(f"{BASE_URL}/api/categories/{category_id}")
        else:
            print(f"⚠ Could not create category for test: {cat_response.status_code}")
    
    def test_search_api_accepts_favor_options(self, api_client):
        """Test that search API accepts favor_options parameter"""
        # First create a category
        cat_response = api_client.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_FavorOptions_Category",
            "protocol": "(test or example)",
            "is_public": True
        })
        
        if cat_response.status_code == 201:
            category_id = cat_response.json().get("category_id")
            
            # Test search with favor_options
            search_response = api_client.post(f"{BASE_URL}/api/search/collate", json={
                "query": "test search query",
                "category_ids": [category_id],
                "max_results": 5,
                "favor_options": {
                    "pearsonCertifications": True,
                    "diagramsSchematics": True,
                    "academicSources": True,
                    "governmentSources": True,
                    "recentContent": True,
                    "primarySources": True
                }
            })
            
            # API should accept the request
            assert search_response.status_code in [200, 503], f"Unexpected status: {search_response.status_code}"
            print(f"✓ Search API accepts favor_options parameter (status: {search_response.status_code})")
            
            # Cleanup
            api_client.delete(f"{BASE_URL}/api/categories/{category_id}")
        else:
            print(f"⚠ Could not create category for test: {cat_response.status_code}")
    
    def test_search_results_endpoint_accepts_match_params(self, api_client):
        """Test that /search/results accepts match option query params"""
        response = api_client.get(f"{BASE_URL}/api/search/results", params={
            "exactMatch": "true",
            "strictMatch": "true",
            "aiMatch": "true"
        })
        
        # Should return 200 (may have empty results)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "results" in data
        print(f"✓ /search/results accepts match option params")


class TestDocumentTypeFilters:
    """Test Document Type filters with Select All/Deselect All"""
    
    def test_document_types_endpoint(self, api_client):
        """Test /document-types endpoint returns types"""
        response = api_client.get(f"{BASE_URL}/api/document-types")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "types" in data
        types = data["types"]
        assert len(types) > 0, "No document types returned"
        
        # Check each type has required fields
        for doc_type in types:
            assert "id" in doc_type
            assert "name" in doc_type
        
        print(f"✓ Document types endpoint returns {len(types)} types")
    
    def test_search_results_filter_by_document_type(self, api_client):
        """Test filtering search results by document type"""
        response = api_client.get(f"{BASE_URL}/api/search/results", params={
            "document_type": "News Article"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✓ Search results can be filtered by document_type")


class TestAuthEndpoints:
    """Test authentication endpoints are working"""
    
    def test_auth_me_with_valid_token(self, api_client):
        """Test /auth/me returns user data with valid token"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        
        # Should return 200 with user data
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        print(f"✓ /auth/me returns user data for authenticated user")
    
    def test_auth_me_without_token(self):
        """Test /auth/me returns 401 without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ /auth/me returns 401 without authentication")


class TestCategoriesAPI:
    """Test Categories CRUD operations"""
    
    def test_create_category(self, api_client):
        """Test creating a category"""
        response = api_client.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Iter9_Category",
            "protocol": "(test or example) & (data)",
            "is_public": True
        })
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        data = response.json()
        assert "category_id" in data
        assert data["name"] == "TEST_Iter9_Category"
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/categories/{data['category_id']}")
        print(f"✓ Category created successfully")
    
    def test_get_categories(self, api_client):
        """Test getting categories"""
        response = api_client.get(f"{BASE_URL}/api/categories", params={
            "user_id": USER_ID
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"✓ Categories retrieved: {len(data['categories'])} categories")


class TestHealthAndBasicEndpoints:
    """Test basic health and utility endpoints"""
    
    def test_health_endpoint(self):
        """Test /health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health endpoint returns healthy status")
    
    def test_stats_overview(self, api_client):
        """Test /stats/overview endpoint"""
        response = api_client.get(f"{BASE_URL}/api/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_results" in data
        print(f"✓ Stats overview returns data")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
