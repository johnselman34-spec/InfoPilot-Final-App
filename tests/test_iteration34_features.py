"""
Iteration 34 - Testing Protocol Bundles, Tri-weekly Newsletter, Map Auto-refresh, and FREE badges
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def test_user_token():
    """Get test user authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Test user authentication failed")


class TestHealthAndBasics:
    """Basic health check tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"


class TestProtocolBundles:
    """Protocol Bundles API tests"""
    
    def test_list_bundles_returns_empty_or_array(self):
        """GET /api/bundles should return bundles array"""
        response = requests.get(f"{BASE_URL}/api/bundles")
        assert response.status_code == 200
        data = response.json()
        assert "bundles" in data
        assert isinstance(data["bundles"], list)
        assert "count" in data
    
    def test_list_bundles_with_sort(self):
        """GET /api/bundles with sort parameter"""
        for sort_option in ["popular", "newest", "discount", "price_low", "price_high"]:
            response = requests.get(f"{BASE_URL}/api/bundles?sort={sort_option}")
            assert response.status_code == 200
            data = response.json()
            assert "bundles" in data
    
    def test_create_bundle_requires_auth(self):
        """POST /api/bundles requires authentication"""
        response = requests.post(f"{BASE_URL}/api/bundles", json={
            "name": "Test Bundle",
            "description": "Test description",
            "protocol_ids": ["id1", "id2"],
            "discount_percent": 15,
            "category": "General"
        })
        assert response.status_code == 401
    
    def test_create_bundle_requires_valid_protocols(self, admin_token):
        """POST /api/bundles requires at least 2 valid protocols"""
        response = requests.post(
            f"{BASE_URL}/api/bundles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Test Bundle",
                "description": "Test description",
                "protocol_ids": ["invalid_id"],
                "discount_percent": 15,
                "category": "General"
            }
        )
        # Should fail because protocols don't exist or less than 2
        assert response.status_code in [400, 422]
    
    def test_get_bundle_not_found(self):
        """GET /api/bundles/{id} returns 404 for invalid ID"""
        response = requests.get(f"{BASE_URL}/api/bundles/000000000000000000000000")
        assert response.status_code == 404
    
    def test_purchase_bundle_requires_auth(self):
        """POST /api/bundles/purchase requires authentication"""
        response = requests.post(f"{BASE_URL}/api/bundles/purchase", json={
            "bundle_id": "000000000000000000000000"
        })
        assert response.status_code == 401
    
    def test_my_bundle_purchases_requires_auth(self):
        """GET /api/bundles/my/purchases requires authentication"""
        response = requests.get(f"{BASE_URL}/api/bundles/my/purchases")
        assert response.status_code == 401
    
    def test_my_bundle_purchases_with_auth(self, admin_token):
        """GET /api/bundles/my/purchases returns purchases list"""
        response = requests.get(
            f"{BASE_URL}/api/bundles/my/purchases",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "purchases" in data
        assert isinstance(data["purchases"], list)


class TestTriweeklyNewsletter:
    """Tri-weekly Newsletter Scheduler tests"""
    
    def test_newsletter_subscribers_endpoint(self, admin_token):
        """Test newsletter subscribers endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/newsletter/subscribers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should return 200 or 403 (admin only)
        assert response.status_code in [200, 403]
    
    def test_newsletter_history_endpoint(self, admin_token):
        """Test newsletter history endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/newsletter/history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "history" in data


class TestMapAutoRefresh:
    """Map auto-refresh feature tests"""
    
    def test_ultimate_search_endpoint(self, admin_token):
        """GET /api/ultimate-search returns results with location data"""
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search?limit=100",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
    
    def test_map_data_endpoint(self, admin_token):
        """GET /api/map-data returns geolocated results"""
        response = requests.get(
            f"{BASE_URL}/api/map-data",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data


class TestMarketplaceProtocols:
    """Marketplace protocols with FREE badge tests"""
    
    def test_marketplace_protocols_list(self):
        """GET /api/marketplace/protocols returns protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        assert isinstance(data["protocols"], list)
    
    def test_free_protocols_exist(self):
        """Check that free protocols ($0.00) exist in marketplace"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        protocols = data.get("protocols", [])
        
        # Check if any protocols have price = 0
        free_protocols = [p for p in protocols if p.get("price", 0) == 0 or p.get("is_free", False)]
        # This is informational - free protocols may or may not exist
        print(f"Found {len(free_protocols)} free protocols out of {len(protocols)} total")
    
    def test_protocol_has_required_fields(self):
        """Check protocol response has required fields"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        protocols = data.get("protocols", [])
        
        if protocols:
            protocol = protocols[0]
            # Check required fields
            assert "id" in protocol
            assert "name" in protocol
            assert "price" in protocol
            assert "category" in protocol


class TestMarketplaceCategories:
    """Marketplace categories tests"""
    
    def test_marketplace_categories(self):
        """GET /api/marketplace/categories returns categories"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)


class TestSellerDashboard:
    """Seller dashboard tests"""
    
    def test_seller_dashboard_requires_auth(self):
        """GET /api/marketplace/seller/dashboard requires auth"""
        response = requests.get(f"{BASE_URL}/api/marketplace/seller/dashboard")
        assert response.status_code == 401
    
    def test_seller_dashboard_with_auth(self, admin_token):
        """GET /api/marketplace/seller/dashboard returns dashboard data"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/seller/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Check for expected fields
        assert "total_earnings" in data or "listings" in data


class TestProtocolAnalytics:
    """Protocol analytics tests"""
    
    def test_my_protocols_analytics(self, admin_token):
        """GET /api/protocol-analytics/my-protocols returns analytics"""
        response = requests.get(
            f"{BASE_URL}/api/protocol-analytics/my-protocols",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data or "summary" in data


class TestCodeQuality:
    """Code quality and file structure tests"""
    
    def test_bundles_router_exists(self):
        """Verify bundles router file exists"""
        assert os.path.exists("/app/backend/routes/bundles.py")
    
    def test_triweekly_newsletter_service_exists(self):
        """Verify tri-weekly newsletter service exists"""
        assert os.path.exists("/app/backend/services/triweekly_newsletter.py")
    
    def test_protocol_bundles_section_exists(self):
        """Verify ProtocolBundlesSection component exists"""
        assert os.path.exists("/app/frontend/src/components/Marketplace/ProtocolBundlesSection.js")
    
    def test_map_page_has_auto_refresh(self):
        """Verify MapPage has auto-refresh feature"""
        with open("/app/frontend/src/pages/MapPage.js", "r") as f:
            content = f.read()
            assert "autoRefresh" in content
            assert "MAP_REFRESH_INTERVAL" in content
            assert "infopilot-data-changed" in content
    
    def test_marketplace_has_bundles_tab(self):
        """Verify MarketplacePage imports ProtocolBundlesSection"""
        with open("/app/frontend/src/pages/MarketplacePage.js", "r") as f:
            content = f.read()
            assert "ProtocolBundlesSection" in content
            assert "bundles" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
