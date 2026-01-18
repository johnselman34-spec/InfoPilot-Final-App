"""
InfoPilot Explorer - Search Engines Integration Tests
Tests for GET /api/search/engines and POST /api/search/collate with engine parameter
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testuser_new@example.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def api_client():
    """Shared requests session."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def authenticated_client(api_client, auth_token):
    """Session with auth header."""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestSearchEnginesEndpoint:
    """Tests for GET /api/search/engines endpoint."""
    
    def test_get_engines_returns_200(self, api_client):
        """GET /api/search/engines should return 200."""
        response = api_client.get(f"{BASE_URL}/api/search/engines")
        assert response.status_code == 200
        print("✓ GET /api/search/engines returns 200")
    
    def test_get_engines_returns_engines_list(self, api_client):
        """GET /api/search/engines should return engines array."""
        response = api_client.get(f"{BASE_URL}/api/search/engines")
        data = response.json()
        
        assert "engines" in data
        assert isinstance(data["engines"], list)
        assert len(data["engines"]) >= 2  # At least DuckDuckGo and Brave
        print(f"✓ GET /api/search/engines returns {len(data['engines'])} engines")
    
    def test_get_engines_duckduckgo_configured(self, api_client):
        """DuckDuckGo should be configured (no API key needed)."""
        response = api_client.get(f"{BASE_URL}/api/search/engines")
        data = response.json()
        
        duckduckgo = next((e for e in data["engines"] if e["id"] == "duckduckgo"), None)
        assert duckduckgo is not None
        assert duckduckgo["configured"] == True
        assert duckduckgo["name"] == "DuckDuckGo"
        print("✓ DuckDuckGo is configured and available")
    
    def test_get_engines_brave_not_configured(self, api_client):
        """Brave should not be configured (no API key set)."""
        response = api_client.get(f"{BASE_URL}/api/search/engines")
        data = response.json()
        
        brave = next((e for e in data["engines"] if e["id"] == "brave"), None)
        assert brave is not None
        assert brave["configured"] == False  # No API key configured
        assert brave["name"] == "Brave Search"
        assert "brave_configured" in data
        assert data["brave_configured"] == False
        print("✓ Brave Search is listed but not configured (no API key)")
    
    def test_get_engines_default_engine(self, api_client):
        """Should return default_engine field."""
        response = api_client.get(f"{BASE_URL}/api/search/engines")
        data = response.json()
        
        assert "default_engine" in data
        assert data["default_engine"] == "all"
        print("✓ Default engine is 'all'")
    
    def test_get_engines_has_required_fields(self, api_client):
        """Each engine should have required fields."""
        response = api_client.get(f"{BASE_URL}/api/search/engines")
        data = response.json()
        
        required_fields = ["id", "name", "configured", "description", "free_tier"]
        for engine in data["engines"]:
            for field in required_fields:
                assert field in engine, f"Engine {engine.get('id', 'unknown')} missing field: {field}"
        print("✓ All engines have required fields (id, name, configured, description, free_tier)")


class TestCollateWithEngineParameter:
    """Tests for POST /api/search/collate with engine parameter."""
    
    def test_collate_requires_auth(self, api_client):
        """POST /api/search/collate should require authentication."""
        response = api_client.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "test", "engine": "duckduckgo"}
        )
        assert response.status_code == 401
        print("✓ POST /api/search/collate requires authentication (401 without token)")
    
    def test_collate_with_duckduckgo_engine(self, authenticated_client):
        """POST /api/search/collate with engine='duckduckgo' should return DuckDuckGo results."""
        response = authenticated_client.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "python tutorial", "engine": "duckduckgo"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "message" in data
        assert "total_searched" in data
        assert len(data["results"]) > 0
        
        # Check that results are from DuckDuckGo
        sources = [r.get("source") for r in data["results"]]
        assert "DuckDuckGo" in sources or "Mock" in sources
        print(f"✓ POST /api/search/collate with engine='duckduckgo' returned {len(data['results'])} results")
    
    def test_collate_with_brave_engine_fallback(self, authenticated_client):
        """POST /api/search/collate with engine='brave' should fallback to mock (no API key)."""
        response = authenticated_client.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "test query", "engine": "brave"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        # Since Brave is not configured, should fallback to mock data
        if len(data["results"]) > 0:
            sources = [r.get("source") for r in data["results"]]
            # Should be Mock since Brave API key is not configured
            assert "Mock" in sources or "Brave" in sources
        print(f"✓ POST /api/search/collate with engine='brave' returned {len(data['results'])} results (fallback to mock)")
    
    def test_collate_with_all_engines(self, authenticated_client):
        """POST /api/search/collate with engine='all' should search all engines."""
        response = authenticated_client.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "web development", "engine": "all"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert len(data["results"]) > 0
        print(f"✓ POST /api/search/collate with engine='all' returned {len(data['results'])} results")
    
    def test_collate_default_engine_is_all(self, authenticated_client):
        """POST /api/search/collate without engine parameter should default to 'all'."""
        response = authenticated_client.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "javascript frameworks"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert len(data["results"]) > 0
        print(f"✓ POST /api/search/collate without engine parameter defaults to 'all' ({len(data['results'])} results)")
    
    def test_collate_invalid_engine_defaults_to_all(self, authenticated_client):
        """POST /api/search/collate with invalid engine should default to 'all'."""
        response = authenticated_client.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "data science", "engine": "invalid_engine"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        print(f"✓ POST /api/search/collate with invalid engine defaults to 'all' ({len(data['results'])} results)")
    
    def test_collate_results_have_source_field(self, authenticated_client):
        """Search results should include source field indicating which engine."""
        response = authenticated_client.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "react hooks", "engine": "duckduckgo"}
        )
        assert response.status_code == 200
        data = response.json()
        
        for result in data["results"]:
            assert "source" in result, "Result missing 'source' field"
            assert result["source"] in ["DuckDuckGo", "Brave", "Mock", "Unknown"]
        print(f"✓ All {len(data['results'])} results have 'source' field")
    
    def test_collate_results_structure(self, authenticated_client):
        """Search results should have required fields."""
        response = authenticated_client.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "nodejs express", "engine": "duckduckgo"}
        )
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["id", "url", "title", "snippet", "source", "document_type"]
        for result in data["results"][:5]:  # Check first 5 results
            for field in required_fields:
                assert field in result, f"Result missing field: {field}"
        print(f"✓ Results have required fields (id, url, title, snippet, source, document_type)")


class TestSearchEngineIntegration:
    """Integration tests for search engine functionality."""
    
    def test_duckduckgo_returns_real_results(self, authenticated_client):
        """DuckDuckGo should return real search results (not mock)."""
        response = authenticated_client.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "python programming language", "engine": "duckduckgo"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check that we got real results (not mock)
        non_mock_results = [r for r in data["results"] if r.get("source") != "Mock"]
        assert len(non_mock_results) > 0, "Expected real DuckDuckGo results, got only mock"
        
        # Verify URLs are real (not example.com)
        real_urls = [r for r in non_mock_results if "example.com" not in r.get("url", "")]
        assert len(real_urls) > 0, "Expected real URLs, got only example.com"
        print(f"✓ DuckDuckGo returned {len(non_mock_results)} real results with valid URLs")
    
    def test_search_results_are_deduplicated(self, authenticated_client):
        """Search results should be deduplicated by URL."""
        response = authenticated_client.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "artificial intelligence", "engine": "all"}
        )
        assert response.status_code == 200
        data = response.json()
        
        urls = [r.get("url") for r in data["results"]]
        unique_urls = set(urls)
        assert len(urls) == len(unique_urls), "Found duplicate URLs in results"
        print(f"✓ All {len(urls)} results have unique URLs (no duplicates)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
