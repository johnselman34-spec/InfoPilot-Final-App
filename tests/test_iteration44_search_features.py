"""
Iteration 44 - Test new search features:
1. GET /api/search-engines - should show 5 engines with Bing integration
2. POST /api/auto-categorize - auto categorization feature
3. POST /api/ai-search - AI intelligent search across multiple engines
4. POST /api/database-search - database text search within collated results
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infopilot-explorer-3.preview.emergentagent.com')

class TestSearchEngines:
    """Test search engines endpoint"""
    
    def test_get_search_engines(self):
        """GET /api/search-engines - should return 5 engines"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200
        
        data = response.json()
        assert "engines" in data
        assert "total_available" in data
        
        # Should have 5 engines
        engines = data["engines"]
        assert len(engines) == 5
        
        # Check all expected engines are present
        expected_engines = ["serpapi", "bing", "brave", "duckduckgo", "basic"]
        for engine in expected_engines:
            assert engine in engines, f"Missing engine: {engine}"
            assert "name" in engines[engine]
            assert "available" in engines[engine]
            assert "description" in engines[engine]
        
        # Bing should show as unavailable (no API key)
        assert engines["bing"]["available"] == False
        assert engines["bing"]["name"] == "Bing"
        
        # Basic should always be available
        assert engines["basic"]["available"] == True
        
        print(f"✓ Search engines endpoint returns {len(engines)} engines, {data['total_available']} available")


class TestAuthentication:
    """Test authentication for protected endpoints"""
    
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
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print("✓ Admin login successful")


class TestAutoCategorize:
    """Test auto-categorize endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_auto_categorize_requires_auth(self):
        """POST /api/auto-categorize requires authentication"""
        response = requests.post(f"{BASE_URL}/api/auto-categorize", json={
            "query": "test query"
        })
        assert response.status_code == 401
        print("✓ Auto-categorize requires authentication")
    
    def test_auto_categorize_requires_query(self, auth_token):
        """POST /api/auto-categorize requires query parameter"""
        response = requests.post(
            f"{BASE_URL}/api/auto-categorize",
            json={"query": ""},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400
        print("✓ Auto-categorize validates empty query")
    
    def test_auto_categorize_success(self, auth_token):
        """POST /api/auto-categorize with valid query"""
        response = requests.post(
            f"{BASE_URL}/api/auto-categorize",
            json={"query": "technology news"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should return 200 or 400 if no categories exist
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert "total" in data
            assert "categories_matched" in data
            print(f"✓ Auto-categorize returned {data['total']} results across {data['categories_matched']} categories")
        else:
            data = response.json()
            print(f"✓ Auto-categorize returned expected error: {data.get('detail', 'No categories')}")


class TestAISearch:
    """Test AI intelligent search endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_ai_search_requires_auth(self):
        """POST /api/ai-search requires authentication"""
        response = requests.post(f"{BASE_URL}/api/ai-search", json={
            "query": "test query"
        })
        assert response.status_code == 401
        print("✓ AI search requires authentication")
    
    def test_ai_search_requires_query(self, auth_token):
        """POST /api/ai-search requires query parameter"""
        response = requests.post(
            f"{BASE_URL}/api/ai-search",
            json={"query": ""},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400
        print("✓ AI search validates empty query")
    
    def test_ai_search_modes(self, auth_token):
        """POST /api/ai-search supports different modes"""
        modes = ["comprehensive", "news", "research"]
        
        for mode in modes:
            response = requests.post(
                f"{BASE_URL}/api/ai-search",
                json={
                    "query": "artificial intelligence",
                    "mode": mode,
                    "auto_categorize": False
                },
                headers={"Authorization": f"Bearer {auth_token}"},
                timeout=60
            )
            assert response.status_code == 200, f"AI search failed for mode: {mode}"
            data = response.json()
            assert "results" in data
            assert "search_mode" in data
            assert data["search_mode"] == mode
            print(f"✓ AI search mode '{mode}' returned {data['total']} results")


class TestDatabaseSearch:
    """Test database text search endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_database_search_requires_auth(self):
        """POST /api/database-search requires authentication"""
        response = requests.post(f"{BASE_URL}/api/database-search", json={
            "query": "test query"
        })
        assert response.status_code == 401
        print("✓ Database search requires authentication")
    
    def test_database_search_requires_query(self, auth_token):
        """POST /api/database-search requires query parameter"""
        response = requests.post(
            f"{BASE_URL}/api/database-search",
            json={"query": ""},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400
        print("✓ Database search validates empty query")
    
    def test_database_search_modes(self, auth_token):
        """POST /api/database-search supports different modes"""
        modes = ["smart", "exact", "fuzzy"]
        
        for mode in modes:
            response = requests.post(
                f"{BASE_URL}/api/database-search",
                json={
                    "query": "test",
                    "mode": mode,
                    "limit": 10
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200, f"Database search failed for mode: {mode}"
            data = response.json()
            assert "results" in data
            assert "total" in data
            assert "mode" in data
            assert data["mode"] == mode
            print(f"✓ Database search mode '{mode}' returned {data['total']} results")
    
    def test_database_search_with_filters(self, auth_token):
        """POST /api/database-search with category and article type filters"""
        response = requests.post(
            f"{BASE_URL}/api/database-search",
            json={
                "query": "news",
                "mode": "smart",
                "article_types": ["News Article"],
                "limit": 50
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "filters" in data
        print(f"✓ Database search with filters returned {data['total']} results")


class TestHealthAndBasicEndpoints:
    """Test basic health and status endpoints"""
    
    def test_health_endpoint(self):
        """GET /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint returns healthy status")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
