"""
Test Suite for InfoPilot Explorer - Iteration 12
Testing: Marketplace, PayPal Integration, Sale Settings, Categories Monetization

Features tested:
1. User login with john@infojet.com / password123
2. Categories page loads and shows existing categories
3. Create Category modal with MONETIZATION OPTIONS
4. Marketplace page with Browse/Purchases/Sales tabs
5. Subscribe page with PayPal hosted button
6. API endpoints: /api/marketplace/protocols, /api/categories/{id}/sale-settings
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Test authentication with provided credentials"""
    
    def test_login_admin_user(self):
        """Test login with admin user john@infojet.com"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "john@infojet.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "john@infojet.com"
        print(f"✓ Admin login successful: {data['user']['email']}")
        return data["access_token"]
    
    def test_login_test_user(self):
        """Test login with test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser@example.com",
            "password": "password123"
        })
        # Test user may or may not exist
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            print(f"✓ Test user login successful")
        else:
            print(f"⚠ Test user does not exist (expected if not created)")


class TestCategoriesAPI:
    """Test Categories API endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "john@infojet.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_categories(self, auth_token):
        """Test GET /api/categories returns list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Categories list returned: {len(data)} categories")
    
    def test_create_private_category_for_sale(self, auth_token):
        """Test creating a private category with for_sale option"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        unique_name = f"TEST_SaleProtocol_{uuid.uuid4().hex[:6]}"
        
        response = requests.post(f"{BASE_URL}/api/categories", headers=headers, json={
            "name": unique_name,
            "protocol": {"protocol_string": "(test) & (protocol)"},
            "is_public": False,
            "for_sale": True,
            "price": 1.50
        })
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert data["name"] == unique_name
        assert data["is_public"] == False
        assert data.get("for_sale") == True
        assert data.get("price") == 1.50
        print(f"✓ Private category for sale created: {unique_name}")
        return data["id"]
    
    def test_create_public_category_not_for_sale(self, auth_token):
        """Test that public categories cannot be for sale"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        unique_name = f"TEST_PublicProtocol_{uuid.uuid4().hex[:6]}"
        
        response = requests.post(f"{BASE_URL}/api/categories", headers=headers, json={
            "name": unique_name,
            "protocol": {"protocol_string": "(public) & (test)"},
            "is_public": True,
            "for_sale": True,  # Should be ignored for public
            "price": 1.00
        })
        assert response.status_code == 200
        data = response.json()
        assert data["is_public"] == True
        # for_sale should be False for public protocols
        assert data.get("for_sale", False) == False
        print(f"✓ Public category created (for_sale correctly ignored)")
        return data["id"]


class TestSaleSettingsAPI:
    """Test sale settings endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "john@infojet.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def private_category_id(self, auth_token):
        """Create a private category for testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        unique_name = f"TEST_SaleSettings_{uuid.uuid4().hex[:6]}"
        
        response = requests.post(f"{BASE_URL}/api/categories", headers=headers, json={
            "name": unique_name,
            "protocol": {"protocol_string": "(sale) & (settings)"},
            "is_public": False,
            "for_sale": False
        })
        assert response.status_code == 200
        return response.json()["id"]
    
    def test_update_sale_settings_enable(self, auth_token, private_category_id):
        """Test PUT /api/categories/{id}/sale-settings to enable sale"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/categories/{private_category_id}/sale-settings",
            headers=headers,
            params={"for_sale": True, "price": 1.25}
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "listed for sale" in data["message"].lower()
        print(f"✓ Sale settings enabled: {data['message']}")
    
    def test_update_sale_settings_disable(self, auth_token, private_category_id):
        """Test PUT /api/categories/{id}/sale-settings to disable sale"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First enable
        requests.put(
            f"{BASE_URL}/api/categories/{private_category_id}/sale-settings",
            headers=headers,
            params={"for_sale": True, "price": 1.00}
        )
        
        # Then disable
        response = requests.put(
            f"{BASE_URL}/api/categories/{private_category_id}/sale-settings",
            headers=headers,
            params={"for_sale": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert "removed from sale" in data["message"].lower()
        print(f"✓ Sale settings disabled: {data['message']}")
    
    def test_sale_settings_price_validation(self, auth_token, private_category_id):
        """Test price validation ($0.75 - $2.99)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test minimum price
        response = requests.put(
            f"{BASE_URL}/api/categories/{private_category_id}/sale-settings",
            headers=headers,
            params={"for_sale": True, "price": 0.75}
        )
        assert response.status_code == 200
        print(f"✓ Minimum price $0.75 accepted")
        
        # Test maximum price
        response = requests.put(
            f"{BASE_URL}/api/categories/{private_category_id}/sale-settings",
            headers=headers,
            params={"for_sale": True, "price": 2.99}
        )
        assert response.status_code == 200
        print(f"✓ Maximum price $2.99 accepted")


class TestMarketplaceAPI:
    """Test Marketplace API endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "john@infojet.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_marketplace_protocols(self, auth_token):
        """Test GET /api/marketplace/protocols returns protocols list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "protocols" in data
        assert isinstance(data["protocols"], list)
        print(f"✓ Marketplace protocols returned: {len(data['protocols'])} protocols for sale")
        return data["protocols"]
    
    def test_get_my_purchases(self, auth_token):
        """Test GET /api/marketplace/my-purchases"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/my-purchases", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "purchases" in data
        assert isinstance(data["purchases"], list)
        print(f"✓ My purchases returned: {len(data['purchases'])} purchases")
    
    def test_get_my_sales(self, auth_token):
        """Test GET /api/marketplace/my-sales"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/my-sales", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "sales" in data
        assert isinstance(data["sales"], list)
        assert "total_revenue" in data
        print(f"✓ My sales returned: {len(data['sales'])} sales, total revenue: ${data['total_revenue']}")


class TestSubscriptionAPI:
    """Test Subscription/PayPal related endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "john@infojet.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_subscription_config(self, auth_token):
        """Test GET /api/subscription/config"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/subscription/config", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Check for PayPal related config
        print(f"✓ Subscription config returned: {list(data.keys())}")
    
    def test_get_subscription_status(self, auth_token):
        """Test GET /api/subscription/status"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/subscription/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "is_subscribed" in data
        print(f"✓ Subscription status: is_subscribed={data['is_subscribed']}")


class TestHealthAndBasics:
    """Test basic health and API endpoints"""
    
    def test_health_check(self):
        """Test /api/health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        print(f"✓ Health check passed: {data}")
    
    def test_root_endpoint(self):
        """Test /api/ root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Root endpoint: {data['message']}")


class TestCategoryUpdateWithSale:
    """Test category update with sale settings"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "john@infojet.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_update_category_with_sale_settings(self, auth_token):
        """Test updating category with for_sale and price"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a private category first
        unique_name = f"TEST_UpdateSale_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/categories", headers=headers, json={
            "name": unique_name,
            "protocol": {"protocol_string": "(update) & (sale)"},
            "is_public": False
        })
        assert create_response.status_code == 200
        category_id = create_response.json()["id"]
        
        # Update with sale settings
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}", headers=headers, json={
            "name": unique_name,
            "protocol_string": "(update) & (sale)",
            "is_public": False,
            "for_sale": True,
            "price": 1.99
        })
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        data = update_response.json()
        assert data.get("for_sale") == True
        assert data.get("price") == 1.99
        print(f"✓ Category updated with sale settings: for_sale=True, price=$1.99")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)


class TestMarketplaceProtocolVisibility:
    """Test that protocols appear in marketplace when for_sale=True"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "john@infojet.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_protocol_appears_in_marketplace(self, auth_token):
        """Test that a for_sale protocol appears in marketplace"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a private category for sale
        unique_name = f"TEST_MarketVisible_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/categories", headers=headers, json={
            "name": unique_name,
            "protocol": {"protocol_string": "(market) & (visible)"},
            "is_public": False,
            "for_sale": True,
            "price": 0.99
        })
        assert create_response.status_code == 200
        category_id = create_response.json()["id"]
        
        # Check marketplace
        market_response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=headers)
        assert market_response.status_code == 200
        protocols = market_response.json()["protocols"]
        
        # Find our protocol
        found = any(p["id"] == category_id for p in protocols)
        assert found, f"Protocol {category_id} not found in marketplace"
        print(f"✓ Protocol appears in marketplace: {unique_name}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)


# Cleanup fixture to remove test data
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed categories after all tests"""
    yield
    
    # Login and cleanup
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "john@infojet.com",
        "password": "password123"
    })
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all categories
        cats_response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        if cats_response.status_code == 200:
            categories = cats_response.json()
            for cat in categories:
                if cat.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/categories/{cat['id']}", headers=headers)
                    print(f"Cleaned up: {cat['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
