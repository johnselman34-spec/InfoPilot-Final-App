"""
InfoPilot Explorer - Stripe Payment Integration Tests
Tests for Stripe checkout, subscriptions, and marketplace payments
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://pilotdata.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "testuser_new@example.com"
TEST_USER_PASSWORD = "password123"
ADMIN_EMAIL = "admin@infopilot.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for test user"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestStripeConfig:
    """Stripe configuration endpoint tests"""
    
    def test_stripe_config_returns_configured_true(self, api_client):
        """GET /api/stripe/config should return configured:true"""
        response = api_client.get(f"{BASE_URL}/api/stripe/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify configuration status
        assert data.get("configured") == True
        assert data.get("mode") == "test"
        
        # Verify subscription packages are present
        assert "subscription_packages" in data
        packages = data["subscription_packages"]
        assert "monthly" in packages
        assert "yearly" in packages
        
        # Verify monthly package details
        assert packages["monthly"]["amount"] == 1.0
        assert packages["monthly"]["name"] == "InfoPilot Monthly"
        
        # Verify yearly package details
        assert packages["yearly"]["amount"] == 9.98
        assert packages["yearly"]["name"] == "InfoPilot Yearly"
        
        # Verify features
        assert "features" in data
        assert "one_time_payments" in data["features"]
        assert "subscriptions" in data["features"]
        assert "marketplace" in data["features"]
        
        print(f"✓ Stripe config: configured={data['configured']}, mode={data['mode']}")


class TestStripeCheckoutSubscription:
    """Stripe checkout for subscription tests"""
    
    def test_create_checkout_monthly_subscription(self, authenticated_client):
        """POST /api/stripe/create-checkout with package_type:monthly"""
        response = authenticated_client.post(f"{BASE_URL}/api/stripe/create-checkout", json={
            "package_type": "monthly",
            "origin_url": "https://pilotdata.preview.emergentagent.com"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify checkout URL is returned
        assert "checkout_url" in data
        assert data["checkout_url"].startswith("https://checkout.stripe.com")
        
        # Verify session ID is returned
        assert "session_id" in data
        assert len(data["session_id"]) > 0
        
        # Verify amount matches monthly price
        assert data["amount"] == 1.0
        assert data["currency"] == "usd"
        
        print(f"✓ Monthly checkout created: session_id={data['session_id'][:20]}...")
        print(f"  checkout_url starts with: {data['checkout_url'][:50]}...")
    
    def test_create_checkout_yearly_subscription(self, authenticated_client):
        """POST /api/stripe/create-checkout with package_type:yearly"""
        response = authenticated_client.post(f"{BASE_URL}/api/stripe/create-checkout", json={
            "package_type": "yearly",
            "origin_url": "https://pilotdata.preview.emergentagent.com"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify checkout URL is returned
        assert "checkout_url" in data
        assert data["checkout_url"].startswith("https://checkout.stripe.com")
        
        # Verify session ID is returned
        assert "session_id" in data
        assert len(data["session_id"]) > 0
        
        # Verify amount matches yearly price
        assert data["amount"] == 9.98
        assert data["currency"] == "usd"
        
        print(f"✓ Yearly checkout created: session_id={data['session_id'][:20]}...")
    
    def test_create_checkout_invalid_package_type(self, authenticated_client):
        """POST /api/stripe/create-checkout with invalid package_type should fail"""
        response = authenticated_client.post(f"{BASE_URL}/api/stripe/create-checkout", json={
            "package_type": "invalid_package",
            "origin_url": "https://pilotdata.preview.emergentagent.com"
        })
        
        # Should return 400 for invalid package type
        assert response.status_code == 400
        print(f"✓ Invalid package type correctly rejected with 400")
    
    def test_create_checkout_requires_auth(self, api_client):
        """POST /api/stripe/create-checkout without auth should fail"""
        # Create a new session without auth
        unauthenticated = requests.Session()
        unauthenticated.headers.update({"Content-Type": "application/json"})
        
        response = unauthenticated.post(f"{BASE_URL}/api/stripe/create-checkout", json={
            "package_type": "monthly",
            "origin_url": "https://pilotdata.preview.emergentagent.com"
        })
        
        # Should return 401 or 403 for unauthenticated request
        assert response.status_code in [401, 403]
        print(f"✓ Unauthenticated request correctly rejected with {response.status_code}")


class TestStripeCheckoutProtocol:
    """Stripe checkout for protocol purchase tests"""
    
    def test_create_checkout_protocol_not_found(self, authenticated_client):
        """POST /api/stripe/create-checkout with non-existent protocol_id should fail"""
        response = authenticated_client.post(f"{BASE_URL}/api/stripe/create-checkout", json={
            "protocol_id": "non_existent_protocol_id",
            "package_type": "protocol_purchase",
            "origin_url": "https://pilotdata.preview.emergentagent.com"
        })
        
        # Should return 404 for non-existent protocol
        assert response.status_code == 404
        print(f"✓ Non-existent protocol correctly rejected with 404")
    
    def test_create_checkout_protocol_missing_id(self, authenticated_client):
        """POST /api/stripe/create-checkout with protocol_purchase but no protocol_id should fail"""
        response = authenticated_client.post(f"{BASE_URL}/api/stripe/create-checkout", json={
            "package_type": "protocol_purchase",
            "origin_url": "https://pilotdata.preview.emergentagent.com"
        })
        
        # Should return 400 for missing protocol_id
        assert response.status_code == 400
        print(f"✓ Missing protocol_id correctly rejected with 400")


class TestStripeStatus:
    """Stripe checkout status tests"""
    
    def test_get_status_invalid_session(self, authenticated_client):
        """GET /api/stripe/status/{session_id} with invalid session should fail"""
        response = authenticated_client.get(f"{BASE_URL}/api/stripe/status/invalid_session_id")
        
        # Should return 404 for non-existent session
        assert response.status_code == 404
        print(f"✓ Invalid session ID correctly rejected with 404")
    
    def test_get_status_requires_auth(self, api_client):
        """GET /api/stripe/status/{session_id} without auth should fail"""
        unauthenticated = requests.Session()
        unauthenticated.headers.update({"Content-Type": "application/json"})
        
        response = unauthenticated.get(f"{BASE_URL}/api/stripe/status/some_session_id")
        
        # Should return 401 or 403 for unauthenticated request
        assert response.status_code in [401, 403]
        print(f"✓ Unauthenticated status request correctly rejected with {response.status_code}")


class TestStripeTransactions:
    """Stripe transactions endpoint tests"""
    
    def test_get_transactions_authenticated(self, authenticated_client):
        """GET /api/stripe/transactions should return user's transactions"""
        response = authenticated_client.get(f"{BASE_URL}/api/stripe/transactions")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "transactions" in data
        assert isinstance(data["transactions"], list)
        
        print(f"✓ Transactions endpoint returned {len(data['transactions'])} transactions")
    
    def test_get_transactions_requires_auth(self, api_client):
        """GET /api/stripe/transactions without auth should fail"""
        unauthenticated = requests.Session()
        unauthenticated.headers.update({"Content-Type": "application/json"})
        
        response = unauthenticated.get(f"{BASE_URL}/api/stripe/transactions")
        
        # Should return 401 or 403 for unauthenticated request
        assert response.status_code in [401, 403]
        print(f"✓ Unauthenticated transactions request correctly rejected with {response.status_code}")


class TestMarketplaceProtocols:
    """Marketplace protocols endpoint tests"""
    
    def test_get_marketplace_protocols(self, api_client):
        """GET /api/marketplace/protocols should return protocol list"""
        response = api_client.get(f"{BASE_URL}/api/marketplace/protocols")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "protocols" in data
        assert isinstance(data["protocols"], list)
        
        print(f"✓ Marketplace returned {len(data['protocols'])} protocols")
        
        # If there are protocols, verify structure
        if len(data["protocols"]) > 0:
            protocol = data["protocols"][0]
            assert "id" in protocol
            assert "name" in protocol
            print(f"  First protocol: {protocol.get('name', 'N/A')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
