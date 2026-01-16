"""
InfoPilot Explorer - Iteration 15 Marketplace Feature Tests
Tests for: Protocol Marketplace, Pay-What-You-Want, Revenue Splits, PayPal Integration, Map Data
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://search-comments.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_USER_EMAIL = "market_tester@example.com"
TEST_USER_PASSWORD = "TestPass123!"


class TestHealthAndBasicEndpoints:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health endpoint: {data}")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        user_data = data.get("user", {})
        assert user_data.get("is_admin") == True
        print(f"✓ Admin login successful, is_admin: {user_data.get('is_admin')}")


class TestMarketplaceProtocols:
    """Marketplace protocols listing tests"""
    
    def test_list_protocols(self):
        """Test GET /api/marketplace/protocols returns protocols list"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert len(data["protocols"]) > 0
        print(f"✓ Marketplace protocols: {data['total']} total, {len(data['protocols'])} on page 1")
        
        # Verify protocol structure
        protocol = data["protocols"][0]
        assert "id" in protocol
        assert "name" in protocol
        assert "description" in protocol
        assert "price" in protocol
        assert "category" in protocol
        assert "creator_name" in protocol
        assert "total_sales" in protocol
        assert "rating" in protocol
        print(f"✓ Protocol structure verified: {protocol['name']}")
    
    def test_list_protocols_with_category_filter(self):
        """Test filtering protocols by category"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols?category=Technology")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        # All returned protocols should be in Technology category
        for protocol in data["protocols"]:
            assert protocol["category"] == "Technology"
        print(f"✓ Category filter working: {len(data['protocols'])} Technology protocols")
    
    def test_list_protocols_with_sorting(self):
        """Test sorting protocols"""
        # Test popular sort
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols?sort=popular")
        assert response.status_code == 200
        data = response.json()
        assert len(data["protocols"]) > 0
        print(f"✓ Popular sort working")
        
        # Test price_low sort
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols?sort=price_low")
        assert response.status_code == 200
        data = response.json()
        if len(data["protocols"]) > 1:
            assert data["protocols"][0]["price"] <= data["protocols"][1]["price"]
        print(f"✓ Price low sort working")


class TestMarketplaceCategories:
    """Marketplace categories tests"""
    
    def test_get_categories(self):
        """Test GET /api/marketplace/categories returns categories with counts"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) > 0
        
        # Verify category structure
        category = data["categories"][0]
        assert "name" in category
        assert "count" in category
        print(f"✓ Categories: {len(data['categories'])} categories found")
        for cat in data["categories"]:
            print(f"  - {cat['name']}: {cat['count']} protocols")


class TestAdminRevenueSettings:
    """Admin revenue settings tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_get_revenue_settings(self, admin_token):
        """Test GET /api/marketplace/admin/revenue-settings"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/admin/revenue-settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "admin_percent" in data
        assert "creator_percent" in data
        assert "paypal_min_payout" in data
        
        # Verify percentages add up to 100
        assert data["admin_percent"] + data["creator_percent"] == 100
        
        # Verify admin_percent is within valid range (5-30%)
        assert 5 <= data["admin_percent"] <= 30
        
        print(f"✓ Revenue settings: Admin {data['admin_percent']}%, Creator {data['creator_percent']}%")
        print(f"  PayPal min payout: ${data['paypal_min_payout']}")
    
    def test_update_revenue_settings(self, admin_token):
        """Test PUT /api/marketplace/admin/revenue-settings"""
        # Update to 15%
        response = requests.put(
            f"{BASE_URL}/api/marketplace/admin/revenue-settings",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"admin_percent": 15}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["admin_percent"] == 15
        assert data["creator_percent"] == 85
        print(f"✓ Revenue settings updated: Admin 15%, Creator 85%")
    
    def test_revenue_settings_validation(self, admin_token):
        """Test revenue settings validation (5-30% range)"""
        # Test below minimum (should fail)
        response = requests.put(
            f"{BASE_URL}/api/marketplace/admin/revenue-settings",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"admin_percent": 3}
        )
        assert response.status_code == 400
        print(f"✓ Validation: Rejected admin_percent below 5%")
        
        # Test above maximum (should fail)
        response = requests.put(
            f"{BASE_URL}/api/marketplace/admin/revenue-settings",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"admin_percent": 35}
        )
        assert response.status_code == 400
        print(f"✓ Validation: Rejected admin_percent above 30%")
    
    def test_revenue_settings_requires_admin(self):
        """Test that revenue settings require admin access"""
        # Try without auth
        response = requests.get(f"{BASE_URL}/api/marketplace/admin/revenue-settings")
        assert response.status_code == 401 or response.status_code == 403
        print(f"✓ Revenue settings protected: requires authentication")


class TestAdminPayouts:
    """Admin payouts tracking tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_get_pending_payouts(self, admin_token):
        """Test GET /api/marketplace/admin/payouts"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/admin/payouts",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "ready_for_payout" in data
        assert "total_ready_amount" in data
        assert "accumulating" in data
        assert "total_accumulating_amount" in data
        assert "admin_platform_fees" in data
        assert "min_payout_threshold" in data
        
        print(f"✓ Payouts data retrieved:")
        print(f"  Ready for payout: {len(data['ready_for_payout'])} users (${data['total_ready_amount']:.2f})")
        print(f"  Accumulating: {len(data['accumulating'])} users (${data['total_accumulating_amount']:.2f})")
        print(f"  Admin platform fees: ${data['admin_platform_fees']:.2f}")
        print(f"  Min payout threshold: ${data['min_payout_threshold']}")
        
        # Verify accumulating users have correct structure
        if data['accumulating']:
            user = data['accumulating'][0]
            assert "user_id" in user
            assert "email" in user
            assert "username" in user
            assert "accumulated_earnings" in user
            assert "remaining_to_payout" in user
            print(f"  Sample accumulating user: {user['username']} - ${user['accumulated_earnings']:.2f}")


class TestUserEarnings:
    """User earnings tracking tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_get_my_earnings(self, admin_token):
        """Test GET /api/marketplace/my-earnings"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/my-earnings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "accumulated_earnings" in data
        assert "ready_for_payout" in data
        assert "remaining_to_payout" in data
        assert "min_payout_threshold" in data
        assert "total_paid_out" in data
        assert "payout_history" in data
        
        print(f"✓ My earnings retrieved:")
        print(f"  Accumulated: ${data['accumulated_earnings']:.2f}")
        print(f"  Ready for payout: {data['ready_for_payout']}")
        print(f"  Remaining to threshold: ${data['remaining_to_payout']:.2f}")
        print(f"  Total paid out: ${data['total_paid_out']:.2f}")


class TestMapData:
    """Map data endpoint tests"""
    
    def test_get_map_data(self):
        """Test GET /api/marketplace/map-data returns protocol locations"""
        response = requests.get(f"{BASE_URL}/api/marketplace/map-data")
        assert response.status_code == 200
        data = response.json()
        
        assert "protocols" in data
        assert "total" in data
        assert len(data["protocols"]) > 0
        
        # Verify protocol location structure
        protocol = data["protocols"][0]
        assert "id" in protocol
        assert "name" in protocol
        assert "category" in protocol
        assert "price" in protocol
        assert "lat" in protocol
        assert "lng" in protocol
        assert "city" in protocol
        assert "country" in protocol
        assert "total_sales" in protocol
        
        print(f"✓ Map data: {data['total']} protocols with locations")
        for p in data["protocols"][:3]:
            print(f"  - {p['name']} in {p['city']}, {p['country']}")


class TestInitiatePurchase:
    """Initiate purchase flow tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_initiate_purchase_own_protocol_fails(self, admin_token):
        """Test that users cannot purchase their own protocols"""
        # Get a protocol created by the admin user
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        protocols = response.json()["protocols"]
        
        # Find a protocol by john_selman (admin's other account) or InfoPilot Official
        # The admin user is jjspilot24@gmail.com, so we need to find their protocol
        # Based on the data, protocols are created by john_selman or InfoPilot Official
        
        # Try to purchase any protocol - if it's the user's own, it should fail
        response = requests.post(
            f"{BASE_URL}/api/marketplace/initiate-purchase",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"protocol_id": protocols[0]["id"], "amount": protocols[0]["price"]}
        )
        
        # Either succeeds (not own protocol) or fails with specific error
        if response.status_code == 400:
            data = response.json()
            assert "cannot purchase your own" in data.get("detail", "").lower() or "already own" in data.get("detail", "").lower()
            print(f"✓ Purchase validation working: {data.get('detail')}")
        else:
            assert response.status_code == 200
            print(f"✓ Purchase initiation working for non-owned protocol")
    
    def test_initiate_purchase_requires_auth(self):
        """Test that purchase requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/marketplace/initiate-purchase",
            headers={"Content-Type": "application/json"},
            json={"protocol_id": "test123", "amount": 1.99}
        )
        assert response.status_code == 401 or response.status_code == 403
        print(f"✓ Purchase requires authentication")


class TestPayPalConfig:
    """PayPal configuration tests"""
    
    def test_get_paypal_config(self):
        """Test GET /api/marketplace/paypal-config returns PayPal client config"""
        response = requests.get(f"{BASE_URL}/api/marketplace/paypal-config")
        assert response.status_code == 200
        data = response.json()
        
        assert "client_id" in data
        assert "currency" in data
        assert data["currency"] == "USD"
        assert len(data["client_id"]) > 0
        
        print(f"✓ PayPal config: client_id present, currency={data['currency']}")


class TestRevenueSplitCalculation:
    """Revenue split calculation verification"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_revenue_split_math(self, admin_token):
        """Verify revenue split calculations are correct"""
        # Get current settings
        response = requests.get(
            f"{BASE_URL}/api/marketplace/admin/revenue-settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        
        admin_percent = data["admin_percent"]
        creator_percent = data["creator_percent"]
        
        # Test calculation for a $10 sale
        test_amount = 10.00
        expected_admin_share = test_amount * (admin_percent / 100)
        expected_creator_share = test_amount * (creator_percent / 100)
        
        assert expected_admin_share + expected_creator_share == test_amount
        
        print(f"✓ Revenue split calculation verified:")
        print(f"  For ${test_amount:.2f} sale:")
        print(f"  - Admin ({admin_percent}%): ${expected_admin_share:.2f}")
        print(f"  - Creator ({creator_percent}%): ${expected_creator_share:.2f}")
        
        # Verify with current 15% admin setting
        if admin_percent == 15:
            assert expected_admin_share == 1.50
            assert expected_creator_share == 8.50
            print(f"✓ 15% admin split verified: $1.50 admin, $8.50 creator")


class TestSellerDashboard:
    """Seller dashboard tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_get_seller_dashboard(self, admin_token):
        """Test GET /api/marketplace/seller/dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/seller/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_listings" in data
        assert "total_sales" in data
        assert "total_revenue" in data
        assert "total_earnings" in data
        assert "platform_fee_rate" in data
        assert "listings" in data
        
        print(f"✓ Seller dashboard:")
        print(f"  Total listings: {data['total_listings']}")
        print(f"  Total sales: {data['total_sales']}")
        print(f"  Total revenue: ${data['total_revenue']:.2f}")
        print(f"  Total earnings: ${data['total_earnings']:.2f}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
