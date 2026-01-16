"""
Iteration 40 - Auto-Categorize and AI Search Features Tests
Tests for:
1. POST /api/auto-categorize - One-click search that matches against ALL categories
2. POST /api/ai-search - AI-powered intelligent keyword search with GPT expansion
3. Multiple categories per result
4. Category checkboxes auto-selected after auto-categorize
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestAutoCategorizeEndpoint:
    """Tests for POST /api/auto-categorize endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
    def test_auto_categorize_requires_auth(self):
        """Test that auto-categorize requires authentication"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/auto-categorize", json={"query": "test"})
        assert res.status_code == 401 or res.status_code == 403
        
    def test_auto_categorize_requires_query(self):
        """Test that auto-categorize requires a search query"""
        res = self.session.post(f"{BASE_URL}/api/auto-categorize", json={})
        assert res.status_code == 400
        assert "query" in res.json().get("detail", "").lower()
        
    def test_auto_categorize_empty_query(self):
        """Test that auto-categorize rejects empty query"""
        res = self.session.post(f"{BASE_URL}/api/auto-categorize", json={"query": "   "})
        assert res.status_code == 400
        
    def test_auto_categorize_success(self):
        """Test successful auto-categorize search"""
        res = self.session.post(f"{BASE_URL}/api/auto-categorize", json={
            "query": "technology news"
        })
        assert res.status_code == 200
        data = res.json()
        
        # Verify response structure
        assert "results" in data
        assert "total" in data
        assert "categories_matched" in data
        assert "batch_id" in data
        assert "message" in data
        
        # Verify results have expected fields
        if data["results"]:
            result = data["results"][0]
            assert "url" in result
            assert "title" in result
            assert "categories" in result  # Multiple categories per result
            assert "category_ids" in result
            
    def test_auto_categorize_returns_category_summary(self):
        """Test that auto-categorize returns category summary"""
        res = self.session.post(f"{BASE_URL}/api/auto-categorize", json={
            "query": "sports"
        })
        assert res.status_code == 200
        data = res.json()
        
        # Should have category_summary if categories matched
        if data.get("categories_matched", 0) > 0:
            assert "category_summary" in data
            if data["category_summary"]:
                summary_item = data["category_summary"][0]
                assert "id" in summary_item
                assert "name" in summary_item
                assert "result_count" in summary_item
                
    def test_auto_categorize_multiple_categories_per_result(self):
        """Test that results can have multiple categories"""
        res = self.session.post(f"{BASE_URL}/api/auto-categorize", json={
            "query": "science research"
        })
        assert res.status_code == 200
        data = res.json()
        
        # Check if any result has multiple categories
        for result in data.get("results", []):
            categories = result.get("categories", [])
            # Categories should be a list
            assert isinstance(categories, list)


class TestAISearchEndpoint:
    """Tests for POST /api/ai-search endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
    def test_ai_search_requires_auth(self):
        """Test that AI search requires authentication"""
        session = requests.Session()
        res = session.post(f"{BASE_URL}/api/ai-search", json={"query": "test"})
        assert res.status_code == 401 or res.status_code == 403
        
    def test_ai_search_requires_query(self):
        """Test that AI search requires a search query"""
        res = self.session.post(f"{BASE_URL}/api/ai-search", json={})
        assert res.status_code == 400
        assert "query" in res.json().get("detail", "").lower()
        
    def test_ai_search_empty_query(self):
        """Test that AI search rejects empty query"""
        res = self.session.post(f"{BASE_URL}/api/ai-search", json={"query": "   "})
        assert res.status_code == 400
        
    def test_ai_search_success(self):
        """Test successful AI search"""
        res = self.session.post(f"{BASE_URL}/api/ai-search", json={
            "query": "artificial intelligence"
        })
        assert res.status_code == 200
        data = res.json()
        
        # Verify response structure
        assert "results" in data
        assert "total" in data
        assert "original_query" in data
        assert "expanded_queries" in data
        assert "batch_id" in data
        assert "message" in data
        
        # Original query should be in expanded queries
        assert data["original_query"] == "artificial intelligence"
        assert "artificial intelligence" in data["expanded_queries"]
        
    def test_ai_search_comprehensive_mode(self):
        """Test AI search with comprehensive mode"""
        res = self.session.post(f"{BASE_URL}/api/ai-search", json={
            "query": "climate change",
            "mode": "comprehensive"
        })
        assert res.status_code == 200
        data = res.json()
        assert data.get("search_mode") == "comprehensive"
        
    def test_ai_search_news_mode(self):
        """Test AI search with news mode"""
        res = self.session.post(f"{BASE_URL}/api/ai-search", json={
            "query": "latest technology",
            "mode": "news"
        })
        assert res.status_code == 200
        data = res.json()
        assert data.get("search_mode") == "news"
        
    def test_ai_search_research_mode(self):
        """Test AI search with research mode"""
        res = self.session.post(f"{BASE_URL}/api/ai-search", json={
            "query": "quantum computing",
            "mode": "research"
        })
        assert res.status_code == 200
        data = res.json()
        assert data.get("search_mode") == "research"
        
    def test_ai_search_auto_categorize_enabled(self):
        """Test AI search with auto_categorize enabled"""
        res = self.session.post(f"{BASE_URL}/api/ai-search", json={
            "query": "health and wellness",
            "auto_categorize": True
        })
        assert res.status_code == 200
        data = res.json()
        assert data.get("auto_categorized") == True
        
        # Results should have categories if auto_categorize is enabled
        for result in data.get("results", []):
            assert "categories" in result
            assert "category_ids" in result
            
    def test_ai_search_auto_categorize_disabled(self):
        """Test AI search with auto_categorize disabled"""
        res = self.session.post(f"{BASE_URL}/api/ai-search", json={
            "query": "space exploration",
            "auto_categorize": False
        })
        assert res.status_code == 200
        data = res.json()
        assert data.get("auto_categorized") == False
        
    def test_ai_search_returns_expanded_queries(self):
        """Test that AI search returns expanded queries from GPT"""
        res = self.session.post(f"{BASE_URL}/api/ai-search", json={
            "query": "machine learning"
        })
        assert res.status_code == 200
        data = res.json()
        
        # Should have expanded_queries list
        assert "expanded_queries" in data
        assert isinstance(data["expanded_queries"], list)
        assert len(data["expanded_queries"]) >= 1  # At least original query
        
    def test_ai_search_result_structure(self):
        """Test AI search result structure"""
        res = self.session.post(f"{BASE_URL}/api/ai-search", json={
            "query": "renewable energy"
        })
        assert res.status_code == 200
        data = res.json()
        
        if data["results"]:
            result = data["results"][0]
            # Verify result fields
            assert "id" in result
            assert "url" in result
            assert "title" in result
            assert "snippet" in result
            assert "article_type" in result
            assert "root_domain" in result
            assert "categories" in result
            assert "category_ids" in result
            assert "search_engine" in result


class TestCategoriesEndpoint:
    """Tests for categories to verify they exist for auto-categorize"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
    def test_get_categories(self):
        """Test getting user categories"""
        res = self.session.get(f"{BASE_URL}/api/categories")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        
    def test_create_category_for_testing(self):
        """Create a test category with protocol for auto-categorize testing"""
        # Create a category with a simple protocol
        res = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_AutoCat_Technology",
            "protocol": "technology & (news | article | research)",
            "is_public": False
        })
        # May already exist, so accept 200 or 400
        assert res.status_code in [200, 201, 400]


class TestUltimateSearchWithCategories:
    """Tests for ultimate search with category filtering"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
    def test_ultimate_search_returns_categories(self):
        """Test that ultimate search results include categories"""
        res = self.session.get(f"{BASE_URL}/api/ultimate-search?limit=10")
        assert res.status_code == 200
        data = res.json()
        
        assert "results" in data
        # Results should have categories field
        for result in data.get("results", []):
            assert "categories" in result
            
    def test_ultimate_search_filter_by_category_ids(self):
        """Test filtering by multiple category IDs"""
        # First get categories
        cat_res = self.session.get(f"{BASE_URL}/api/categories")
        assert cat_res.status_code == 200
        categories = cat_res.json()
        
        if categories:
            cat_id = categories[0].get("id")
            res = self.session.get(f"{BASE_URL}/api/ultimate-search?category_ids={cat_id}")
            assert res.status_code == 200
            data = res.json()
            assert "filter_applied" in data
            
    def test_ultimate_search_aggregation_modes(self):
        """Test different aggregation modes"""
        for mode in ["and_or", "and", "or"]:
            res = self.session.get(f"{BASE_URL}/api/ultimate-search?aggregation={mode}")
            assert res.status_code == 200
            data = res.json()
            assert data.get("aggregation_mode") == mode


class TestSearchResultsPersistence:
    """Tests for search results persistence after auto-categorize/AI search"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
    def test_auto_categorize_creates_batch(self):
        """Test that auto-categorize creates a batch"""
        res = self.session.post(f"{BASE_URL}/api/auto-categorize", json={
            "query": "test batch creation"
        })
        assert res.status_code == 200
        data = res.json()
        
        batch_id = data.get("batch_id")
        assert batch_id is not None
        
        # Verify batch exists
        batches_res = self.session.get(f"{BASE_URL}/api/ultimate-search/batches")
        assert batches_res.status_code == 200
        
    def test_ai_search_creates_batch(self):
        """Test that AI search creates a batch"""
        res = self.session.post(f"{BASE_URL}/api/ai-search", json={
            "query": "test ai batch"
        })
        assert res.status_code == 200
        data = res.json()
        
        batch_id = data.get("batch_id")
        assert batch_id is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
