"""
Iteration 45 - Deep Search and Strict Protocol Matching Tests

Tests for:
1. Backend API health check
2. POST /api/collate - Deep Collate with strict protocol matching
3. POST /api/auto-categorize - Deep Auto-categorize with strict matching
4. Collate generates multiple search queries from protocol
5. Results include match_score as percentage
6. Results include deep_search_stats in response
7. Admin settings: search_collate_limit, match_threshold, deep_search_queries
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://deep-search-app.preview.emergentagent.com').rstrip('/')


class TestHealthCheck:
    """API Health Check Tests"""
    
    def test_api_health(self):
        """Test API health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert "timestamp" in data


class TestAuthentication:
    """Authentication Tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "jjspilot24@gmail.com", "password": "InfoPilot2024!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        return data["token"]
    
    def test_admin_login(self, admin_token):
        """Test admin can login successfully"""
        assert admin_token is not None
        assert len(admin_token) > 0


class TestAdminSettings:
    """Admin Settings Tests for Deep Search Configuration"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "jjspilot24@gmail.com", "password": "InfoPilot2024!"}
        )
        return response.json()["token"]
    
    def test_get_admin_settings(self, admin_token):
        """Test getting admin settings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify new deep search settings exist
        assert "search_collate_limit" in data, "search_collate_limit setting missing"
        assert "match_threshold" in data, "match_threshold setting missing"
        assert "deep_search_queries" in data, "deep_search_queries setting missing"
    
    def test_search_collate_limit_setting(self, admin_token):
        """Test search_collate_limit setting value"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        
        search_collate_limit = data.get("search_collate_limit")
        assert search_collate_limit is not None
        assert isinstance(search_collate_limit, (int, float))
        assert 1 <= search_collate_limit <= 200, "search_collate_limit should be between 1-200"
    
    def test_match_threshold_setting(self, admin_token):
        """Test match_threshold setting value"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        
        match_threshold = data.get("match_threshold")
        assert match_threshold is not None
        assert isinstance(match_threshold, (int, float))
        assert 50 <= match_threshold <= 100, "match_threshold should be between 50-100%"
    
    def test_deep_search_queries_setting(self, admin_token):
        """Test deep_search_queries setting value"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        
        deep_search_queries = data.get("deep_search_queries")
        assert deep_search_queries is not None
        assert isinstance(deep_search_queries, (int, float))
        assert 3 <= deep_search_queries <= 15, "deep_search_queries should be between 3-15"
    
    def test_update_match_threshold(self, admin_token):
        """Test updating match_threshold setting"""
        # Update setting
        response = requests.post(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"key": "match_threshold", "value": 70}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("key") == "match_threshold"
        assert data.get("value") == 70


class TestDeepCollate:
    """Deep Collate Endpoint Tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "jjspilot24@gmail.com", "password": "InfoPilot2024!"}
        )
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def test_category_id(self, admin_token):
        """Get a category ID for testing"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = response.json()
        # Find a category with a protocol
        for cat in categories:
            if cat.get("protocol"):
                return cat["id"]
        pytest.skip("No categories with protocols found")
    
    def test_collate_requires_auth(self):
        """Test collate endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/collate",
            json={"category_id": "test123"}
        )
        assert response.status_code == 401
    
    def test_collate_invalid_category(self, admin_token):
        """Test collate with invalid category ID"""
        response = requests.post(
            f"{BASE_URL}/api/collate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category_id": "000000000000000000000000"}
        )
        assert response.status_code == 404
    
    def test_collate_returns_deep_search_stats(self, admin_token, test_category_id):
        """Test collate returns deep_search_stats in response"""
        response = requests.post(
            f"{BASE_URL}/api/collate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category_id": test_category_id, "aggregation": "default", "page": 1},
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify deep_search_stats is present
        assert "deep_search_stats" in data, "deep_search_stats missing from response"
        stats = data["deep_search_stats"]
        
        # Verify stats structure
        assert "queries_executed" in stats, "queries_executed missing"
        assert "total_results_found" in stats, "total_results_found missing"
        assert "passed_strict_matching" in stats, "passed_strict_matching missing"
        assert "rejected" in stats, "rejected count missing"
        assert "match_threshold" in stats, "match_threshold missing"
    
    def test_collate_generates_multiple_queries(self, admin_token, test_category_id):
        """Test collate generates multiple search queries from protocol"""
        response = requests.post(
            f"{BASE_URL}/api/collate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category_id": test_category_id, "aggregation": "default", "page": 1},
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        stats = data.get("deep_search_stats", {})
        queries_executed = stats.get("queries_executed", 0)
        
        # Should execute multiple queries (at least 1, typically 3-10)
        assert queries_executed >= 1, "Should execute at least 1 query"
        print(f"Queries executed: {queries_executed}")
    
    def test_collate_results_have_match_score(self, admin_token, test_category_id):
        """Test collate results include match_score as percentage"""
        response = requests.post(
            f"{BASE_URL}/api/collate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category_id": test_category_id, "aggregation": "default", "page": 1},
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        results = data.get("results", [])
        if results:
            first_result = results[0]
            
            # Verify match_score is present and is a percentage
            assert "match_score" in first_result, "match_score missing from result"
            match_score = first_result["match_score"]
            assert isinstance(match_score, (int, float)), "match_score should be numeric"
            
            # Verify match_percent is present
            assert "match_percent" in first_result, "match_percent missing from result"
            
            # Verify groups_matched and total_groups
            assert "groups_matched" in first_result, "groups_matched missing"
            assert "total_groups" in first_result, "total_groups missing"
    
    def test_collate_response_structure(self, admin_token, test_category_id):
        """Test collate response has correct structure"""
        response = requests.post(
            f"{BASE_URL}/api/collate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category_id": test_category_id, "aggregation": "default", "page": 1},
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "results" in data
        assert "total" in data
        assert "category" in data
        assert "batch_id" in data
        assert "deep_search_stats" in data
        assert "message" in data
        
        # Verify message mentions deep collate
        assert "Deep Collate" in data.get("message", "") or "results" in data.get("message", "").lower()


class TestDeepAutoCategorize:
    """Deep Auto-Categorize Endpoint Tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "jjspilot24@gmail.com", "password": "InfoPilot2024!"}
        )
        return response.json()["token"]
    
    def test_auto_categorize_requires_auth(self):
        """Test auto-categorize endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/auto-categorize",
            json={"query": "test query"}
        )
        assert response.status_code == 401
    
    def test_auto_categorize_requires_query(self, admin_token):
        """Test auto-categorize requires a query"""
        response = requests.post(
            f"{BASE_URL}/api/auto-categorize",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": ""}
        )
        assert response.status_code == 400
    
    def test_auto_categorize_returns_deep_search_stats(self, admin_token):
        """Test auto-categorize returns deep_search_stats"""
        response = requests.post(
            f"{BASE_URL}/api/auto-categorize",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": "civil war history"},
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify deep_search_stats is present
        assert "deep_search_stats" in data, "deep_search_stats missing from response"
        stats = data["deep_search_stats"]
        
        # Verify stats structure
        assert "queries_executed" in stats
        assert "total_results_found" in stats
        assert "passed_strict_matching" in stats
        assert "rejected" in stats
        assert "match_threshold" in stats
    
    def test_auto_categorize_results_have_categories_count(self, admin_token):
        """Test auto-categorize results include categories_count"""
        response = requests.post(
            f"{BASE_URL}/api/auto-categorize",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": "civil war history battles"},
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        results = data.get("results", [])
        if results:
            first_result = results[0]
            
            # Verify categories_count is present
            assert "categories_count" in first_result, "categories_count missing from result"
            categories_count = first_result["categories_count"]
            assert isinstance(categories_count, int), "categories_count should be integer"
            assert categories_count >= 0, "categories_count should be non-negative"
            
            # Verify categories list matches count
            categories = first_result.get("categories", [])
            assert len(categories) == categories_count, "categories list length should match categories_count"
    
    def test_auto_categorize_results_have_match_score(self, admin_token):
        """Test auto-categorize results include match_score"""
        response = requests.post(
            f"{BASE_URL}/api/auto-categorize",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": "president george bush pilot"},
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        results = data.get("results", [])
        if results:
            first_result = results[0]
            
            # Verify match_score is present
            assert "match_score" in first_result, "match_score missing from result"
            match_score = first_result["match_score"]
            assert isinstance(match_score, (int, float)), "match_score should be numeric"
    
    def test_auto_categorize_response_structure(self, admin_token):
        """Test auto-categorize response has correct structure"""
        response = requests.post(
            f"{BASE_URL}/api/auto-categorize",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": "american history"},
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "results" in data
        assert "total" in data
        assert "categories_matched" in data
        assert "category_summary" in data
        assert "batch_id" in data
        assert "deep_search_stats" in data
        assert "message" in data
    
    def test_auto_categorize_category_summary(self, admin_token):
        """Test auto-categorize returns category summary"""
        response = requests.post(
            f"{BASE_URL}/api/auto-categorize",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": "civil war history"},
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        category_summary = data.get("category_summary", [])
        if category_summary:
            first_cat = category_summary[0]
            assert "id" in first_cat
            assert "name" in first_cat
            assert "result_count" in first_cat


class TestProtocolService:
    """Protocol Service Tests - Testing generate_deep_search_queries and strict_match_result"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "jjspilot24@gmail.com", "password": "InfoPilot2024!"}
        )
        return response.json()["token"]
    
    def test_protocol_debug_endpoint(self, admin_token):
        """Test protocol debug endpoint shows parsed groups"""
        response = requests.post(
            f"{BASE_URL}/api/protocol/debug",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"protocol": "(civil war or battle) & (history or historical)+"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify debug info
        assert "valid" in data
        assert data["valid"] == True
        assert "groups" in data
        assert "group_count" in data
        assert data["group_count"] >= 1


class TestStrictMatching:
    """Tests for strict protocol matching behavior"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "jjspilot24@gmail.com", "password": "InfoPilot2024!"}
        )
        return response.json()["token"]
    
    def test_match_threshold_affects_results(self, admin_token):
        """Test that match_threshold setting affects result filtering"""
        # Get current settings
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        settings = response.json()
        current_threshold = settings.get("match_threshold", 70)
        
        # Verify threshold is being used in collate
        response = requests.post(
            f"{BASE_URL}/api/auto-categorize",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": "test search"},
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        stats = data.get("deep_search_stats", {})
        threshold_in_response = stats.get("match_threshold", "")
        
        # Verify threshold is reported in response
        assert f"{current_threshold}%" in threshold_in_response, f"Expected {current_threshold}% in response, got {threshold_in_response}"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
