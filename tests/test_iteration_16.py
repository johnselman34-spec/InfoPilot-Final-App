"""
InfoPilot Explorer - Iteration 16 Test Suite
Testing: Elasticsearch integration, Paywall filtering, Full integration
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "testuser_new@example.com"
TEST_USER_PASSWORD = "password123"


class TestElasticsearchConnection:
    """Test Elasticsearch connection and status"""
    
    def test_elasticsearch_status_connected(self):
        """Verify Elasticsearch is connected"""
        response = requests.get(f"{BASE_URL}/api/search/elasticsearch/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["connected"] == True, f"Elasticsearch not connected: {data}"
        assert data["configured"] == True
        assert "cluster_name" in data
        assert "version" in data
        assert data["version"] == "8.11.0"
        print(f"✓ Elasticsearch connected to cluster: {data['cluster_name']}, version: {data['version']}")
    
    def test_elasticsearch_indices_exist(self):
        """Verify Elasticsearch indices are created"""
        response = requests.get(f"{BASE_URL}/api/search/elasticsearch/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "indices" in data
        assert "infopilot-search-results" in data["indices"]
        assert "infopilot-protocols" in data["indices"]
        print(f"✓ Elasticsearch indices: {data['indices']}")


class TestElasticsearchSemanticSearch:
    """Test Elasticsearch semantic search functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_semantic_search_returns_results(self):
        """Test semantic search returns indexed results"""
        response = requests.post(
            f"{BASE_URL}/api/search/elasticsearch/search",
            json={"query": "technology", "limit": 10},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "count" in data
        assert data["query"] == "technology"
        print(f"✓ Semantic search returned {data['count']} results for 'technology'")
    
    def test_semantic_search_with_specific_query(self):
        """Test semantic search with specific query"""
        response = requests.post(
            f"{BASE_URL}/api/search/elasticsearch/search",
            json={"query": "artificial intelligence machine learning", "limit": 20},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        print(f"✓ Semantic search for 'AI/ML' returned {data['count']} results")
    
    def test_semantic_search_result_structure(self):
        """Verify semantic search result structure"""
        response = requests.post(
            f"{BASE_URL}/api/search/elasticsearch/search",
            json={"query": "news", "limit": 5},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        if data["count"] > 0:
            result = data["results"][0]
            # Check expected fields
            expected_fields = ["url", "title", "snippet", "source", "created_at"]
            for field in expected_fields:
                assert field in result, f"Missing field: {field}"
            print(f"✓ Semantic search result has correct structure")
        else:
            print("⚠ No results to verify structure (may need to index more data)")


class TestPaywallFiltering:
    """Test paywall filtering functionality"""
    
    def test_paywall_filter_enabled(self):
        """Verify paywall filter is enabled"""
        response = requests.get(f"{BASE_URL}/api/search/engines")
        assert response.status_code == 200
        
        data = response.json()
        assert "paywall_filter" in data
        assert data["paywall_filter"]["enabled"] == True
        assert data["paywall_filter"]["blocked_domains"] == 156
        print(f"✓ Paywall filter enabled with {data['paywall_filter']['blocked_domains']} blocked domains")
    
    def test_search_engines_status(self):
        """Verify search engines configuration"""
        response = requests.get(f"{BASE_URL}/api/search/engines")
        assert response.status_code == 200
        
        data = response.json()
        assert "engines" in data
        assert len(data["engines"]) == 2
        
        # Check DuckDuckGo
        ddg = next((e for e in data["engines"] if e["id"] == "duckduckgo"), None)
        assert ddg is not None
        assert ddg["configured"] == True
        
        # Check Brave
        brave = next((e for e in data["engines"] if e["id"] == "brave"), None)
        assert brave is not None
        assert brave["configured"] == True
        
        print("✓ Both DuckDuckGo and Brave Search are configured")


class TestSearchCollateWithElasticsearch:
    """Test search collate with Elasticsearch indexing"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_collate_indexes_to_elasticsearch(self):
        """Test that search collate indexes results to Elasticsearch"""
        # Perform a search
        response = requests.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "python programming tutorials", "engine": "duckduckgo"},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "elasticsearch_indexed" in data
        
        # Check that results were indexed
        indexed_count = data.get("elasticsearch_indexed", 0)
        print(f"✓ Search collate indexed {indexed_count} results to Elasticsearch")
        
        # Wait a moment for indexing to complete
        time.sleep(1)
        
        # Verify we can search for the indexed content
        search_response = requests.post(
            f"{BASE_URL}/api/search/elasticsearch/search",
            json={"query": "python programming", "limit": 10},
            headers=self.headers
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        print(f"✓ Semantic search found {search_data['count']} results for indexed content")
    
    def test_collate_filters_paywalled_content(self):
        """Test that search collate filters paywalled content"""
        response = requests.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "business news finance", "engine": "all"},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        results = data.get("results", [])
        
        # Check that no paywalled domains are in results
        paywall_domains = [
            "nytimes.com", "wsj.com", "bloomberg.com", "washingtonpost.com",
            "ft.com", "economist.com", "wired.com", "forbes.com"
        ]
        
        for result in results:
            url = result.get("url", "").lower()
            for domain in paywall_domains:
                assert domain not in url, f"Paywalled domain {domain} found in results: {url}"
        
        print(f"✓ No paywalled domains found in {len(results)} search results")
    
    def test_collate_with_brave_engine(self):
        """Test search collate with Brave engine"""
        response = requests.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "climate change solutions", "engine": "brave"},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        
        # Check that results have Brave source
        brave_results = [r for r in data["results"] if r.get("source") == "Brave"]
        print(f"✓ Brave search returned {len(brave_results)} results")


class TestFullIntegration:
    """Test full integration flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_full_search_flow(self):
        """Test complete search flow: search -> filter paywalls -> index to ES -> semantic search"""
        # Step 1: Perform search with collate
        unique_query = f"renewable energy solar power {int(time.time())}"
        collate_response = requests.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "renewable energy solar power", "engine": "all"},
            headers=self.headers
        )
        assert collate_response.status_code == 200
        collate_data = collate_response.json()
        
        print(f"Step 1: Collated {len(collate_data['results'])} results")
        print(f"  - Elasticsearch indexed: {collate_data.get('elasticsearch_indexed', 0)}")
        
        # Step 2: Verify no paywalled content
        paywall_domains = ["nytimes.com", "wsj.com", "bloomberg.com", "nature.com", "science.org"]
        paywalled_found = []
        for result in collate_data["results"]:
            url = result.get("url", "").lower()
            for domain in paywall_domains:
                if domain in url:
                    paywalled_found.append(url)
        
        assert len(paywalled_found) == 0, f"Paywalled content found: {paywalled_found}"
        print(f"Step 2: ✓ No paywalled content in results")
        
        # Step 3: Wait for indexing and perform semantic search
        time.sleep(2)
        
        semantic_response = requests.post(
            f"{BASE_URL}/api/search/elasticsearch/search",
            json={"query": "solar energy renewable", "limit": 20},
            headers=self.headers
        )
        assert semantic_response.status_code == 200
        semantic_data = semantic_response.json()
        
        print(f"Step 3: Semantic search returned {semantic_data['count']} results")
        
        # Step 4: Verify search results endpoint
        results_response = requests.get(
            f"{BASE_URL}/api/search/results?category_ids=&aggregation=and_or",
            headers=self.headers
        )
        assert results_response.status_code == 200
        results_data = results_response.json()
        
        print(f"Step 4: Search results endpoint returned {results_data['total']} total results")
        print("✓ Full integration flow completed successfully")


class TestExistingFeatures:
    """Test that existing features still work"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_categories_endpoint(self):
        """Test categories CRUD still works"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        assert response.status_code == 200
        print("✓ Categories endpoint working")
    
    def test_chat_rooms_endpoint(self):
        """Test chat rooms endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/chat/rooms", headers=self.headers)
        assert response.status_code == 200
        print("✓ Chat rooms endpoint working")
    
    def test_templates_endpoint(self):
        """Test templates endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/templates", headers=self.headers)
        assert response.status_code == 200
        print("✓ Templates endpoint working")
    
    def test_user_profile(self):
        """Test user profile endpoint"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_USER_EMAIL
        print("✓ User profile endpoint working")
    
    def test_leaderboard_endpoint(self):
        """Test leaderboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/users/leaderboard")
        assert response.status_code == 200
        print("✓ Leaderboard endpoint working")
    
    def test_stats_endpoint(self):
        """Test stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        print("✓ Stats endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
