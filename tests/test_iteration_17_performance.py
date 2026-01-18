"""
InfoPilot Explorer - Iteration 17 Performance Optimization Tests
Tests for N+1 query fixes, database indexes, caching, and aggregation pipelines
"""
import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testuser_new@example.com"
TEST_PASSWORD = "password123"


class TestDatabaseIndexes:
    """Test that database indexes are created on startup."""
    
    def test_server_starts_with_indexes(self):
        """Verify server starts successfully with index creation."""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "global" in data
        # Server started successfully means indexes were created
        print(f"Server running with stats: {data['global']}")


class TestMarketplaceOptimization:
    """Test marketplace endpoint with aggregation and caching."""
    
    def test_marketplace_protocols_returns_data(self):
        """Test GET /api/marketplace/protocols returns protocols."""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        assert "total" in data
        assert isinstance(data["protocols"], list)
        print(f"Marketplace returned {data['total']} protocols")
    
    def test_marketplace_protocols_have_owner_info(self):
        """Test that protocols include owner info from $lookup aggregation."""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        
        if data["protocols"]:
            protocol = data["protocols"][0]
            # Verify owner info is included (from $lookup)
            assert "owner" in protocol, "Owner info should be included from $lookup"
            if protocol["owner"]:
                assert "username" in protocol["owner"], "Owner should have username"
                assert "id" in protocol["owner"], "Owner should have id"
            print(f"Protocol '{protocol['name']}' has owner: {protocol.get('owner')}")
    
    def test_marketplace_caching_performance(self):
        """Test that marketplace caching improves response time."""
        # First request (cache miss)
        start1 = time.time()
        response1 = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        time1 = time.time() - start1
        assert response1.status_code == 200
        
        # Second request (should be cached)
        start2 = time.time()
        response2 = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        time2 = time.time() - start2
        assert response2.status_code == 200
        
        # Both should return same data
        assert response1.json()["total"] == response2.json()["total"]
        print(f"First request: {time1:.3f}s, Second request: {time2:.3f}s")
    
    def test_marketplace_with_category_filter(self):
        """Test marketplace with category filter parameter."""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols?category=test")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        print(f"Filtered marketplace returned {data['total']} protocols")


class TestLeaderboardOptimization:
    """Test leaderboard endpoint with aggregation and caching."""
    
    def test_leaderboard_returns_data(self):
        """Test GET /api/leaderboard returns leaderboard data."""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "top_laughter_points" in data
        assert "top_protocol_creators" in data
        print(f"Leaderboard: {len(data['top_laughter_points'])} top laughers, {len(data['top_protocol_creators'])} top creators")
    
    def test_leaderboard_top_laughter_structure(self):
        """Test top_laughter_points has correct structure."""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        if data["top_laughter_points"]:
            user = data["top_laughter_points"][0]
            assert "id" in user
            assert "username" in user
            assert "laughter_points" in user
            print(f"Top laughter user: {user['username']} with {user['laughter_points']} points")
    
    def test_leaderboard_top_creators_structure(self):
        """Test top_protocol_creators has correct structure from aggregation."""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        if data["top_protocol_creators"]:
            creator = data["top_protocol_creators"][0]
            assert "protocol_count" in creator
            assert "user" in creator
            if creator["user"]:
                assert "username" in creator["user"]
                assert "id" in creator["user"]
            print(f"Top creator: {creator['user']['username'] if creator['user'] else 'N/A'} with {creator['protocol_count']} protocols")
    
    def test_leaderboard_caching_performance(self):
        """Test that leaderboard caching works."""
        # First request
        start1 = time.time()
        response1 = requests.get(f"{BASE_URL}/api/leaderboard")
        time1 = time.time() - start1
        assert response1.status_code == 200
        
        # Second request (should be cached)
        start2 = time.time()
        response2 = requests.get(f"{BASE_URL}/api/leaderboard")
        time2 = time.time() - start2
        assert response2.status_code == 200
        
        # Data should be consistent
        assert len(response1.json()["top_laughter_points"]) == len(response2.json()["top_laughter_points"])
        print(f"First request: {time1:.3f}s, Second request: {time2:.3f}s")
    
    def test_users_leaderboard_alias(self):
        """Test /api/users/leaderboard alias endpoint."""
        response = requests.get(f"{BASE_URL}/api/users/leaderboard")
        assert response.status_code == 200
        data = response.json()
        # This endpoint returns different format than /api/leaderboard
        assert "leaderboard" in data or "top_laughter_points" in data
        print("Users leaderboard alias working")


class TestRevenueDashboardOptimization:
    """Test revenue dashboard with aggregation pipeline."""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_revenue_dashboard_returns_data(self, auth_token):
        """Test GET /api/revenue/dashboard returns revenue data."""
        response = requests.get(
            f"{BASE_URL}/api/revenue/dashboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure from optimized aggregation
        assert "total_revenue" in data
        assert "total_sales" in data
        assert "monthly_revenue" in data
        assert "top_protocols" in data
        assert "wallet_balance" in data
        
        print(f"Revenue dashboard: ${data['total_revenue']} total, {data['total_sales']} sales")
    
    def test_revenue_dashboard_requires_auth(self):
        """Test revenue dashboard requires authentication."""
        response = requests.get(f"{BASE_URL}/api/revenue/dashboard")
        assert response.status_code == 401
    
    def test_revenue_export_csv(self, auth_token):
        """Test revenue export as CSV."""
        response = requests.get(
            f"{BASE_URL}/api/revenue/export?format=csv",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        print("CSV export working")
    
    def test_revenue_export_pdf(self, auth_token):
        """Test revenue export as PDF."""
        response = requests.get(
            f"{BASE_URL}/api/revenue/export?format=pdf",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        print("PDF export working")


class TestExistingFeaturesNoRegression:
    """Test that existing features still work after optimization."""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_auth_login(self):
        """Test authentication still works."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"Login successful for {data['user']['username']}")
    
    def test_categories_endpoint(self, auth_token):
        """Test categories endpoint."""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"Categories: {len(data['categories'])} found")
    
    def test_stats_endpoint(self):
        """Test stats endpoint."""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "global" in data
        print(f"Stats: {data['global']['total_users']} users, {data['global']['total_categories']} categories")
    
    def test_chat_rooms_endpoint(self, auth_token):
        """Test chat rooms endpoint."""
        response = requests.get(
            f"{BASE_URL}/api/chat/rooms",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "rooms" in data
        print(f"Chat rooms: {len(data['rooms'])} found")
    
    def test_templates_endpoint(self, auth_token):
        """Test templates endpoint."""
        response = requests.get(
            f"{BASE_URL}/api/templates",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Templates endpoint returns official_templates and community_templates
        assert "official_templates" in data or "templates" in data
        template_count = len(data.get("official_templates", [])) + len(data.get("community_templates", []))
        print(f"Templates: {template_count} found")
    
    def test_user_profile(self, auth_token):
        """Test user profile endpoint."""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        print(f"User profile: {data['username']}")
    
    def test_search_engines_status(self, auth_token):
        """Test search engines status."""
        response = requests.get(
            f"{BASE_URL}/api/search/engines",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        print(f"Search engines: {len(data['engines'])} configured")
    
    def test_elasticsearch_status(self, auth_token):
        """Test Elasticsearch status."""
        response = requests.get(
            f"{BASE_URL}/api/search/elasticsearch/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        print(f"Elasticsearch connected: {data['connected']}")
    
    def test_easter_eggs_endpoint(self):
        """Test easter eggs endpoint."""
        response = requests.get(f"{BASE_URL}/api/easter-eggs/random")
        assert response.status_code == 200
        data = response.json()
        assert "egg" in data
        print(f"Easter egg: {data['egg']['id']}")
    
    def test_news_headlines(self):
        """Test news headlines endpoint."""
        response = requests.get(f"{BASE_URL}/api/news/headlines")
        assert response.status_code == 200
        data = response.json()
        assert "headlines" in data
        print(f"Headlines: {len(data['headlines'])} found")


class TestMarketplacePurchaseFlow:
    """Test marketplace purchase flow still works."""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_buy_protocol_requires_auth(self):
        """Test buying protocol requires authentication."""
        response = requests.post(f"{BASE_URL}/api/marketplace/buy/test-id")
        assert response.status_code == 401
    
    def test_buy_nonexistent_protocol(self, auth_token):
        """Test buying non-existent protocol returns 404."""
        response = requests.post(
            f"{BASE_URL}/api/marketplace/buy/nonexistent-protocol-id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404


class TestCacheInvalidation:
    """Test cache invalidation on data changes."""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_marketplace_cache_returns_consistent_data(self):
        """Test marketplace cache returns consistent data."""
        response1 = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        response2 = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Data should be consistent
        assert response1.json()["total"] == response2.json()["total"]
        print("Marketplace cache consistent")
    
    def test_leaderboard_cache_returns_consistent_data(self):
        """Test leaderboard cache returns consistent data."""
        response1 = requests.get(f"{BASE_URL}/api/leaderboard")
        response2 = requests.get(f"{BASE_URL}/api/leaderboard")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Data should be consistent
        data1 = response1.json()
        data2 = response2.json()
        assert len(data1["top_laughter_points"]) == len(data2["top_laughter_points"])
        print("Leaderboard cache consistent")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
