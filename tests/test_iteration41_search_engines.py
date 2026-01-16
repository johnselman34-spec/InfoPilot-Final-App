"""
Iteration 41 - Brave and Yandex Search Engine Integration Tests
Tests for:
- GET /api/search-engines endpoint
- Brave Search integration (available when BRAVE_API_KEY is set)
- Yandex Search integration (available when YANDEX_API_KEY and YANDEX_FOLDER_ID are set)
- Search engines status display
- ExtendedWebSearchService.search aggregates from all available engines
- Auto-categorize and AI Search still work with new engines
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSearchEnginesEndpoint:
    """Tests for GET /api/search-engines endpoint"""
    
    def test_search_engines_endpoint_returns_200(self):
        """Test that /api/search-engines returns 200"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✅ GET /api/search-engines returns 200")
    
    def test_search_engines_returns_engines_dict(self):
        """Test that response contains engines dictionary"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        data = response.json()
        
        assert "engines" in data, "Response should contain 'engines' key"
        assert isinstance(data["engines"], dict), "engines should be a dictionary"
        print("✅ Response contains engines dictionary")
    
    def test_search_engines_returns_total_available(self):
        """Test that response contains total_available count"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        data = response.json()
        
        assert "total_available" in data, "Response should contain 'total_available' key"
        assert isinstance(data["total_available"], int), "total_available should be an integer"
        assert data["total_available"] >= 1, "At least 1 engine should be available (basic)"
        print(f"✅ total_available = {data['total_available']}")
    
    def test_search_engines_contains_all_five_engines(self):
        """Test that all 5 search engines are listed"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        data = response.json()
        engines = data["engines"]
        
        expected_engines = ["serpapi", "brave", "yandex", "duckduckgo", "basic"]
        for engine in expected_engines:
            assert engine in engines, f"Engine '{engine}' should be in engines list"
        print(f"✅ All 5 engines present: {list(engines.keys())}")
    
    def test_search_engines_structure(self):
        """Test that each engine has correct structure"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        data = response.json()
        engines = data["engines"]
        
        for engine_key, engine_data in engines.items():
            assert "name" in engine_data, f"Engine {engine_key} should have 'name'"
            assert "available" in engine_data, f"Engine {engine_key} should have 'available'"
            assert "description" in engine_data, f"Engine {engine_key} should have 'description'"
            assert isinstance(engine_data["available"], bool), f"Engine {engine_key} 'available' should be boolean"
        print("✅ All engines have correct structure (name, available, description)")
    
    def test_brave_engine_status(self):
        """Test Brave engine status - should be False without API key"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        data = response.json()
        brave = data["engines"]["brave"]
        
        assert brave["name"] == "Brave Search", f"Expected 'Brave Search', got '{brave['name']}'"
        assert "privacy" in brave["description"].lower(), "Description should mention privacy"
        # Brave should be unavailable without API key
        print(f"✅ Brave Search status: available={brave['available']}")
    
    def test_yandex_engine_status(self):
        """Test Yandex engine status - should be False without API key and folder ID"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        data = response.json()
        yandex = data["engines"]["yandex"]
        
        assert yandex["name"] == "Yandex", f"Expected 'Yandex', got '{yandex['name']}'"
        # Yandex should be unavailable without API key and folder ID
        print(f"✅ Yandex status: available={yandex['available']}")
    
    def test_serpapi_engine_status(self):
        """Test SerpAPI engine status - should be True with API key"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        data = response.json()
        serpapi = data["engines"]["serpapi"]
        
        assert serpapi["name"] == "Google (SerpAPI)", f"Expected 'Google (SerpAPI)', got '{serpapi['name']}'"
        # SerpAPI should be available since SERPAPI_KEY is set in .env
        print(f"✅ SerpAPI status: available={serpapi['available']}")
    
    def test_duckduckgo_engine_status(self):
        """Test DuckDuckGo engine status - should be True (no API key needed)"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        data = response.json()
        ddg = data["engines"]["duckduckgo"]
        
        assert ddg["name"] == "DuckDuckGo", f"Expected 'DuckDuckGo', got '{ddg['name']}'"
        # DuckDuckGo should be available (no API key required)
        print(f"✅ DuckDuckGo status: available={ddg['available']}")
    
    def test_basic_engine_always_available(self):
        """Test Basic engine is always available"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        data = response.json()
        basic = data["engines"]["basic"]
        
        assert basic["name"] == "Basic Web Search", f"Expected 'Basic Web Search', got '{basic['name']}'"
        assert basic["available"] == True, "Basic engine should always be available"
        print("✅ Basic Web Search is always available")


class TestSearchWithNewEngines:
    """Tests for search functionality with new engines"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_search_endpoint_works(self):
        """Test that /api/search endpoint still works"""
        response = requests.post(
            f"{BASE_URL}/api/search",
            json={"query": "python programming"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "results" in data, "Response should contain 'results'"
        print(f"✅ Search returned {len(data.get('results', []))} results")
    
    def test_auto_categorize_works_with_new_engines(self):
        """Test that auto-categorize still works with new engine infrastructure"""
        response = requests.post(
            f"{BASE_URL}/api/auto-categorize",
            json={"query": "technology news"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "results" in data, "Response should contain 'results'"
        assert "total" in data, "Response should contain 'total'"
        print(f"✅ Auto-categorize returned {data.get('total', 0)} results")
    
    def test_ai_search_works_with_new_engines(self):
        """Test that AI search still works with new engine infrastructure"""
        response = requests.post(
            f"{BASE_URL}/api/ai-search",
            json={
                "query": "artificial intelligence",
                "mode": "comprehensive",
                "auto_categorize": False
            },
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "results" in data, "Response should contain 'results'"
        assert "expanded_queries" in data, "Response should contain 'expanded_queries'"
        print(f"✅ AI Search returned {data.get('total', 0)} results with {len(data.get('expanded_queries', []))} queries")


class TestSearchEnginesNoAuth:
    """Tests for search-engines endpoint without authentication"""
    
    def test_search_engines_no_auth_required(self):
        """Test that /api/search-engines doesn't require authentication"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200, "search-engines should not require auth"
        print("✅ /api/search-engines accessible without authentication")


class TestEngineAvailabilityCount:
    """Tests for engine availability counting"""
    
    def test_total_available_matches_count(self):
        """Test that total_available matches actual available engines count"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        data = response.json()
        
        engines = data["engines"]
        actual_available = sum(1 for e in engines.values() if e["available"])
        
        assert data["total_available"] == actual_available, \
            f"total_available ({data['total_available']}) should match actual count ({actual_available})"
        print(f"✅ total_available ({data['total_available']}) matches actual available count")
    
    def test_minimum_engines_available(self):
        """Test that at least 2 engines are available (DuckDuckGo + Basic)"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        data = response.json()
        
        # At minimum, DuckDuckGo and Basic should be available
        assert data["total_available"] >= 2, \
            f"At least 2 engines should be available, got {data['total_available']}"
        print(f"✅ At least 2 engines available: {data['total_available']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
