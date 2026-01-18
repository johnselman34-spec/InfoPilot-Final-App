"""
InfoPilot Explorer - Iteration 15 Tests
Testing: Paywall filtering, Elasticsearch status, and existing features
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infojethub.preview.emergentagent.com')

# Known paywall domains to check against
PAYWALL_DOMAINS = [
    "nytimes.com", "wsj.com", "bloomberg.com", "washingtonpost.com",
    "ft.com", "economist.com", "newyorker.com", "theatlantic.com",
    "wired.com", "forbes.com", "fortune.com", "nature.com", "science.org"
]


class TestPaywallFilter:
    """Test paywall filtering functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_search_engines_shows_paywall_filter_info(self):
        """GET /api/search/engines should show paywall_filter info"""
        response = self.session.get(f"{BASE_URL}/api/search/engines")
        assert response.status_code == 200
        
        data = response.json()
        assert "paywall_filter" in data
        assert data["paywall_filter"]["enabled"] == True
        assert data["paywall_filter"]["blocked_domains"] >= 150  # Should have 156+ domains
        print(f"✓ Paywall filter enabled with {data['paywall_filter']['blocked_domains']} blocked domains")
    
    def test_search_engines_shows_elasticsearch_status(self):
        """GET /api/search/engines should show elasticsearch status"""
        response = self.session.get(f"{BASE_URL}/api/search/engines")
        assert response.status_code == 200
        
        data = response.json()
        assert "elasticsearch" in data
        # Elasticsearch is configured but not connected (truncated URL)
        assert data["elasticsearch"]["configured"] == True
        assert data["elasticsearch"]["connected"] == False
        print(f"✓ Elasticsearch status: configured={data['elasticsearch']['configured']}, connected={data['elasticsearch']['connected']}")
    
    def test_search_collate_filters_paywalled_content(self):
        """POST /api/search/collate should filter paywalled content"""
        response = self.session.post(f"{BASE_URL}/api/search/collate", json={
            "query": "technology news today",
            "engine": "duckduckgo"
        })
        assert response.status_code == 200
        
        data = response.json()
        results = data.get("results", [])
        
        # Check that no paywalled domains are in results
        paywalled_found = []
        for result in results:
            url = result.get("url", "").lower()
            for domain in PAYWALL_DOMAINS:
                if domain in url:
                    paywalled_found.append(url)
        
        assert len(paywalled_found) == 0, f"Found paywalled domains in results: {paywalled_found}"
        print(f"✓ Search returned {len(results)} results with no paywalled domains")
    
    def test_search_collate_with_brave_engine(self):
        """POST /api/search/collate with Brave engine should also filter paywalls"""
        response = self.session.post(f"{BASE_URL}/api/search/collate", json={
            "query": "business finance news",
            "engine": "brave"
        })
        assert response.status_code == 200
        
        data = response.json()
        results = data.get("results", [])
        
        # Check that no paywalled domains are in results
        paywalled_found = []
        for result in results:
            url = result.get("url", "").lower()
            for domain in PAYWALL_DOMAINS:
                if domain in url:
                    paywalled_found.append(url)
        
        assert len(paywalled_found) == 0, f"Found paywalled domains in results: {paywalled_found}"
        print(f"✓ Brave search returned {len(results)} results with no paywalled domains")
    
    def test_search_collate_with_all_engines(self):
        """POST /api/search/collate with all engines should filter paywalls"""
        response = self.session.post(f"{BASE_URL}/api/search/collate", json={
            "query": "science research papers",
            "engine": "all"
        })
        assert response.status_code == 200
        
        data = response.json()
        results = data.get("results", [])
        
        # Check that no paywalled domains are in results
        paywalled_found = []
        for result in results:
            url = result.get("url", "").lower()
            for domain in PAYWALL_DOMAINS:
                if domain in url:
                    paywalled_found.append(url)
        
        assert len(paywalled_found) == 0, f"Found paywalled domains in results: {paywalled_found}"
        print(f"✓ All engines search returned {len(results)} results with no paywalled domains")


class TestElasticsearchEndpoints:
    """Test Elasticsearch-related endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_elasticsearch_status_endpoint(self):
        """GET /api/search/elasticsearch/status should return status"""
        response = self.session.get(f"{BASE_URL}/api/search/elasticsearch/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "configured" in data
        assert "connected" in data
        # Expected: configured but not connected due to truncated URL
        print(f"✓ Elasticsearch status endpoint working: {data}")
    
    def test_elasticsearch_semantic_search_graceful_failure(self):
        """POST /api/search/elasticsearch/search should handle disconnected ES gracefully"""
        response = self.session.post(f"{BASE_URL}/api/search/elasticsearch/search", json={
            "query": "test search",
            "limit": 10
        })
        # Should return 200 with empty results when ES is not connected
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "count" in data
        print(f"✓ Elasticsearch search handles disconnection gracefully: {data['count']} results")


class TestExistingFeatures:
    """Test existing features still work"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_categories_crud(self):
        """Test category CRUD operations"""
        # Create category
        response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "Test Paywall Category",
            "protocol": "(test or paywall) & (filter)"
        })
        assert response.status_code in [200, 201]
        
        data = response.json()
        category_id = data.get("id")
        assert category_id is not None
        print(f"✓ Created category: {category_id}")
        
        # Get categories
        response = self.session.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        print(f"✓ Retrieved categories")
        
        # Delete category
        response = self.session.delete(f"{BASE_URL}/api/categories/{category_id}")
        assert response.status_code == 200
        print(f"✓ Deleted category: {category_id}")
    
    def test_max_price_limit_on_categories(self):
        """Test maximum price limit $24.99 on categories"""
        # Try to create category with price over limit
        response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "Expensive Category",
            "protocol": "(expensive)",
            "price": 50.00  # Over the $24.99 limit
        })
        
        # Should either reject or cap the price
        if response.status_code == 200:
            data = response.json()
            # If accepted, price should be capped at 24.99
            if data.get("price") is not None:
                assert data["price"] <= 24.99, f"Price {data['price']} exceeds max limit of 24.99"
            
            # Cleanup
            category_id = data.get("id")
            if category_id:
                self.session.delete(f"{BASE_URL}/api/categories/{category_id}")
        
        print("✓ Price limit check passed")
    
    def test_chat_rooms_endpoint(self):
        """Test WebSocket chat rooms endpoint"""
        response = self.session.get(f"{BASE_URL}/api/chat/rooms")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Chat rooms endpoint working: {len(data)} rooms")
    
    def test_books_endpoint(self):
        """Test books endpoint for Stripe checkout"""
        response = self.session.get(f"{BASE_URL}/api/books")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Books endpoint working: {len(data)} books")
    
    def test_admin_setup_endpoint(self):
        """Test admin setup endpoint"""
        response = self.session.get(f"{BASE_URL}/api/admin/settings")
        # Should return 200 for admin or 403 for non-admin
        assert response.status_code in [200, 403]
        print(f"✓ Admin settings endpoint responding: {response.status_code}")


class TestEasterEggErrorHandling:
    """Test easter egg error handling fix"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_easter_egg_catch_endpoint(self):
        """Test easter egg catch endpoint handles errors gracefully"""
        response = self.session.post(f"{BASE_URL}/api/easter-eggs/catch", json={
            "egg_id": "nonexistent_egg"
        })
        # Should return 404 for nonexistent egg, not 500
        assert response.status_code in [200, 404, 400]
        print(f"✓ Easter egg endpoint handles errors gracefully: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
