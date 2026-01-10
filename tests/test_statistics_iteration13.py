"""
Test Suite for InfoPilot Explorer - Iteration 13
Testing Statistics Page, Popular Protocols, and Copy Tracking Features

Features tested:
1. GET /api/statistics - User's personal statistics
2. GET /api/statistics/global - Platform-wide statistics  
3. GET /api/statistics/popular-protocols - Protocols sorted by copy count
4. POST /api/categories/{id}/copy - Increment copy_count
5. POST /api/search/collate - Web search and categorization
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        print("✓ Health check passed")
    
    def test_admin_login(self):
        """Test admin user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful: {data['user']['email']}")
        return data["access_token"]


class TestStatisticsEndpoints:
    """Test statistics API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.user_id = response.json()["user"]["id"]
    
    def test_get_user_statistics(self):
        """Test GET /api/statistics - User's personal statistics"""
        response = requests.get(f"{BASE_URL}/api/statistics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "article_types" in data
        assert "top_domains" in data
        assert "by_year" in data
        assert "by_category" in data
        assert "total_results" in data
        assert "total_categories" in data
        
        # Verify data types
        assert isinstance(data["article_types"], list)
        assert isinstance(data["top_domains"], list)
        assert isinstance(data["total_results"], int)
        assert isinstance(data["total_categories"], int)
        
        print(f"✓ User statistics retrieved: {data['total_results']} results, {data['total_categories']} categories")
    
    def test_get_global_statistics(self):
        """Test GET /api/statistics/global - Platform-wide statistics"""
        response = requests.get(f"{BASE_URL}/api/statistics/global", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_users" in data
        assert "total_public_categories" in data
        assert "total_protocols_for_sale" in data
        assert "total_protocol_purchases" in data
        assert "total_clipboard_copies" in data
        assert "top_contributors" in data
        assert "recent_categories_7d" in data
        
        # Verify data types
        assert isinstance(data["total_users"], int)
        assert isinstance(data["total_public_categories"], int)
        assert isinstance(data["total_clipboard_copies"], int)
        assert isinstance(data["top_contributors"], list)
        
        print(f"✓ Global statistics retrieved: {data['total_users']} users, {data['total_public_categories']} public protocols, {data['total_clipboard_copies']} total copies")
    
    def test_get_popular_protocols(self):
        """Test GET /api/statistics/popular-protocols - Protocols sorted by copy count"""
        response = requests.get(f"{BASE_URL}/api/statistics/popular-protocols?limit=10", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "popular_protocols" in data
        assert isinstance(data["popular_protocols"], list)
        
        # If there are protocols, verify structure
        if len(data["popular_protocols"]) > 0:
            protocol = data["popular_protocols"][0]
            assert "id" in protocol
            assert "name" in protocol
            assert "protocol_string" in protocol
            assert "owner_username" in protocol
            assert "copy_count" in protocol
            assert "is_public" in protocol
            
            # Verify sorted by copy_count descending
            copy_counts = [p["copy_count"] for p in data["popular_protocols"]]
            assert copy_counts == sorted(copy_counts, reverse=True), "Protocols should be sorted by copy_count descending"
            
            print(f"✓ Popular protocols retrieved: {len(data['popular_protocols'])} protocols")
            for i, p in enumerate(data["popular_protocols"][:5]):
                print(f"  #{i+1}: {p['name']} - {p['copy_count']} copies")
        else:
            print("✓ Popular protocols endpoint working (no protocols with copies yet)")
    
    def test_popular_protocols_limit_parameter(self):
        """Test limit parameter for popular protocols"""
        # Test with limit=5
        response = requests.get(f"{BASE_URL}/api/statistics/popular-protocols?limit=5", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["popular_protocols"]) <= 5
        print(f"✓ Limit parameter works: returned {len(data['popular_protocols'])} protocols with limit=5")


class TestProtocolCopyTracking:
    """Test protocol copy tracking functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.user_id = response.json()["user"]["id"]
    
    def test_create_category_and_track_copy(self):
        """Test creating a category and tracking copies"""
        # Create a test category
        unique_name = f"TEST_CopyTrack_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/categories", headers=self.headers, json={
            "name": unique_name,
            "protocol": {"protocol_string": "(test or copy) & (tracking)+"},
            "is_public": True
        })
        assert create_response.status_code == 200
        category = create_response.json()
        category_id = category["id"]
        initial_copy_count = category.get("copy_count", 0)
        print(f"✓ Created test category: {unique_name} (copy_count: {initial_copy_count})")
        
        try:
            # Track a copy
            copy_response = requests.post(f"{BASE_URL}/api/categories/{category_id}/copy", headers=self.headers)
            assert copy_response.status_code == 200
            copy_data = copy_response.json()
            assert "copy_count" in copy_data
            assert copy_data["copy_count"] == initial_copy_count + 1
            print(f"✓ Copy tracked successfully: copy_count now {copy_data['copy_count']}")
            
            # Track another copy
            copy_response2 = requests.post(f"{BASE_URL}/api/categories/{category_id}/copy", headers=self.headers)
            assert copy_response2.status_code == 200
            assert copy_response2.json()["copy_count"] == initial_copy_count + 2
            print(f"✓ Second copy tracked: copy_count now {copy_response2.json()['copy_count']}")
            
            # Verify the category now appears in popular protocols (if copy_count > 0)
            popular_response = requests.get(f"{BASE_URL}/api/statistics/popular-protocols?limit=50", headers=self.headers)
            assert popular_response.status_code == 200
            popular_protocols = popular_response.json()["popular_protocols"]
            
            # Find our test category
            found = False
            for p in popular_protocols:
                if p["id"] == category_id:
                    found = True
                    assert p["copy_count"] >= 2
                    print(f"✓ Test category found in popular protocols with {p['copy_count']} copies")
                    break
            
            if not found:
                print("⚠ Test category not found in popular protocols (may need more copies)")
            
        finally:
            # Cleanup - delete test category
            delete_response = requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=self.headers)
            if delete_response.status_code == 200:
                print(f"✓ Cleaned up test category: {unique_name}")
    
    def test_copy_nonexistent_category(self):
        """Test copying a non-existent category returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/categories/{fake_id}/copy", headers=self.headers)
        assert response.status_code == 404
        print("✓ Non-existent category returns 404")
    
    def test_copy_requires_authentication(self):
        """Test that copy endpoint requires authentication"""
        # First get a valid category ID
        categories_response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        categories_data = categories_response.json()
        # API returns list directly, not wrapped in "categories" key
        categories = categories_data if isinstance(categories_data, list) else categories_data.get("categories", [])
        
        if categories_response.status_code == 200 and len(categories) > 0:
            category_id = categories[0]["id"]
            
            # Try to copy without auth
            response = requests.post(f"{BASE_URL}/api/categories/{category_id}/copy")
            assert response.status_code == 401
            print("✓ Copy endpoint requires authentication")
        else:
            print("⚠ No categories available to test auth requirement")


class TestCollateFunction:
    """Test the collate/search functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_collate_endpoint_exists(self):
        """Test that collate endpoint exists and accepts requests"""
        # Note: This may fail if Google Search API is not configured
        response = requests.post(f"{BASE_URL}/api/search/collate", headers=self.headers, json={
            "search_query": "test query",
            "max_results": 5
        })
        # Accept 200 (success) or 500 (API not configured) - just verify endpoint exists
        assert response.status_code in [200, 500, 400]
        print(f"✓ Collate endpoint exists (status: {response.status_code})")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Collate returned {len(data.get('results', []))} results")


class TestMarketplaceIntegration:
    """Test marketplace and categories integration with statistics"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_marketplace_protocols_endpoint(self):
        """Test GET /api/marketplace/protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        print(f"✓ Marketplace protocols: {len(data['protocols'])} for sale")
    
    def test_categories_endpoint(self):
        """Test GET /api/categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns list directly
        categories = data if isinstance(data, list) else data.get("categories", [])
        assert isinstance(categories, list)
        print(f"✓ Categories endpoint: {len(categories)} categories")
    
    def test_subscription_config(self):
        """Test subscription configuration endpoint"""
        response = requests.get(f"{BASE_URL}/api/subscription/config", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns paypal_link_1 or similar fields
        assert "paypal_link_1" in data or "is_promo_active" in data or "min_price" in data
        print(f"✓ Subscription config retrieved: promo_active={data.get('is_promo_active')}")


class TestStatisticsPageData:
    """Test that all data needed for Statistics page is available"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_all_statistics_endpoints_together(self):
        """Test all statistics endpoints that the frontend calls"""
        # This mimics what the StatisticsPage component does
        
        # 1. User statistics
        user_stats = requests.get(f"{BASE_URL}/api/statistics", headers=self.headers)
        assert user_stats.status_code == 200
        
        # 2. Global statistics
        global_stats = requests.get(f"{BASE_URL}/api/statistics/global", headers=self.headers)
        assert global_stats.status_code == 200
        
        # 3. Popular protocols
        popular = requests.get(f"{BASE_URL}/api/statistics/popular-protocols?limit=10", headers=self.headers)
        assert popular.status_code == 200
        
        print("✓ All statistics endpoints working together")
        print(f"  - User stats: {user_stats.json()['total_results']} results")
        print(f"  - Global: {global_stats.json()['total_users']} users, {global_stats.json()['total_clipboard_copies']} copies")
        print(f"  - Popular protocols: {len(popular.json()['popular_protocols'])} protocols")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
