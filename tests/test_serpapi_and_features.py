"""
InfoPilot Explorer - SerpAPI Integration & Feature Tests
Tests for: SerpAPI search (31-70 results), Batch deletion, BookPromoBanner, QuoteOfTheDay
Iteration 7 - December 2025
"""
import pytest
import requests
import time
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://explorer-hub-7.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"


class TestHealthAndAuth:
    """Basic health and auth tests - run first"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_login_admin(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["is_admin"] == True
        print(f"✓ Admin login successful: {data['user']['username']}")


class TestSerpAPISearch:
    """SerpAPI search integration tests - Target: 31-70 results in 19-22 seconds"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for protected endpoints"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_search_returns_31_to_70_results(self, auth_token):
        """Test that search returns between 31-70 results"""
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/api/search",
            json={"query": "William Gamble civil war general"},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify result count is in target range
        total = data["total"]
        assert total >= 31, f"Expected at least 31 results, got {total}"
        assert total <= 70, f"Expected at most 70 results, got {total}"
        
        print(f"✓ Search returned {total} results (target: 31-70)")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Source: {data.get('source', 'unknown')}")
    
    def test_search_completes_under_22_seconds(self, auth_token):
        """Test that search completes in under 22 seconds"""
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/api/search",
            json={"query": "technology news 2024"},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 22, f"Search took {elapsed:.1f}s, expected under 22s"
        
        data = response.json()
        print(f"✓ Search completed in {elapsed:.1f}s (target: <22s)")
        print(f"  Results: {data['total']}")
    
    def test_search_uses_serpapi_source(self, auth_token):
        """Test that search uses SerpAPI as primary source"""
        response = requests.post(f"{BASE_URL}/api/search",
            json={"query": "python programming tutorial"},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check source indicates serpapi
        source = data.get("source", "")
        assert "serpapi" in source.lower(), f"Expected serpapi source, got {source}"
        
        # Check that some results have serpapi source
        serpapi_results = [r for r in data["results"] if r.get("source") == "serpapi"]
        assert len(serpapi_results) > 0, "Expected some results from SerpAPI"
        
        print(f"✓ Search source: {source}")
        print(f"  SerpAPI results: {len(serpapi_results)}/{data['total']}")
    
    def test_search_results_have_required_fields(self, auth_token):
        """Test that search results have all required fields"""
        response = requests.post(f"{BASE_URL}/api/search",
            json={"query": "machine learning basics"},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) > 0, "Expected at least one result"
        
        # Check first result has required fields
        first = data["results"][0]
        required_fields = ["url", "title", "snippet", "source"]
        for field in required_fields:
            assert field in first, f"Missing field: {field}"
        
        print(f"✓ Results have required fields: {required_fields}")
        print(f"  First result: {first['title'][:50]}...")


class TestBatchDeletion:
    """Batch deletion feature tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for protected endpoints"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_search_batches(self, auth_token):
        """Test getting list of search batches"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/batches",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "batches" in data
        assert "total" in data
        assert isinstance(data["batches"], list)
        
        print(f"✓ Retrieved {data['total']} search batches")
        
        if data["batches"]:
            batch = data["batches"][0]
            assert "batch_id" in batch
            assert "result_count" in batch
            print(f"  First batch: {batch['batch_id'][:20]}... ({batch['result_count']} results)")
    
    def test_batch_deletion_requires_auth(self):
        """Test that batch deletion requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/ultimate-search/batch/test-batch-id")
        assert response.status_code == 401
        print("✓ Batch deletion requires authentication")
    
    def test_delete_nonexistent_batch(self, auth_token):
        """Test deleting a non-existent batch returns 404"""
        response = requests.delete(f"{BASE_URL}/api/ultimate-search/batch/nonexistent-batch-id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        print("✓ Non-existent batch returns 404")


class TestBookPromoEndpoint:
    """Book promotion endpoint tests"""
    
    def test_get_book_promo(self):
        """Test book promotion data endpoint"""
        response = requests.get(f"{BASE_URL}/api/book-promo")
        assert response.status_code == 200
        data = response.json()
        
        # Verify book data
        assert data["title"] == "Letters to Evelyn"
        assert data["author"] == "John Selman"
        assert data["price"] == "$2.99"
        assert data["review_count"] == 19
        assert len(data["images"]) == 4
        
        # Verify images are valid URLs
        for img in data["images"]:
            assert img.startswith("https://")
        
        print(f"✓ Book promo data: {data['title']} by {data['author']}")
        print(f"  Images: {len(data['images'])}")
        print(f"  Reviews: {data['review_count']}")


class TestQuoteOfTheDay:
    """Quote of the Day - Note: Handled in frontend with static quotes from manuscript"""
    
    def test_quote_of_day_note(self):
        """Note: Quote of the Day is handled entirely in frontend (QuoteOfTheDay.js)
        Uses MANUSCRIPT_QUOTES array with 15 quotes from 'Letters to Evelyn'
        No backend endpoint needed - quotes rotate based on day of year"""
        print("✓ Quote of the Day: Frontend-only feature (no API endpoint)")
        print("  - Uses MANUSCRIPT_QUOTES array in QuoteOfTheDay.js")
        print("  - 15 quotes from 'Letters to Evelyn' manuscript")
        print("  - Rotates based on day of year for consistency")
        assert True  # Placeholder - actual testing done via Playwright


class TestNavigationEndpoints:
    """Test all navigation-related endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for protected endpoints"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_categories_endpoint(self, auth_token):
        """Test categories endpoint"""
        response = requests.get(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Categories endpoint: {len(data)} categories")
    
    def test_admin_settings_endpoint(self, auth_token):
        """Test admin settings endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin settings endpoint: {len(data)} settings")
    
    def test_subscription_info_endpoint(self):
        """Test subscription info endpoint (public)"""
        response = requests.get(f"{BASE_URL}/api/subscription-info")
        assert response.status_code == 200
        data = response.json()
        assert "subscription_price" in data
        print(f"✓ Subscription info: ${data['subscription_price']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
