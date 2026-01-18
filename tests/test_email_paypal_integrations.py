"""
InfoPilot Explorer - Email and PayPal Integration Tests
Tests for Resend email integration and PayPal Orders v2 API
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "testuser_new@example.com"
TEST_USER_PASSWORD = "password123"
ADMIN_EMAIL = "admin@infopilot.com"
ADMIN_PASSWORD = "admin123"
TEST_NEWSLETTER_EMAIL = f"test_newsletter_{uuid.uuid4().hex[:8]}@example.com"


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
        token = response.json().get("token")
        api_client.headers.update({"Authorization": f"Bearer {token}"})
        return token
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get authentication token for admin user"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    return None


class TestEmailConfiguration:
    """Test email configuration endpoints"""
    
    def test_email_config_status(self, api_client):
        """GET /api/email/test - Check email configuration status"""
        response = api_client.get(f"{BASE_URL}/api/email/test")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "configured" in data, "Response should have 'configured' field"
        assert data["configured"] == True, "Email should be configured with Resend API key"
        assert "sender_email" in data, "Response should have 'sender_email' field"
        assert "status" in data, "Response should have 'status' field"
        print(f"✓ Email config: configured={data['configured']}, sender={data['sender_email']}, status={data['status']}")


class TestNewsletterSubscription:
    """Test newsletter subscription endpoints"""
    
    def test_newsletter_subscribe(self, api_client):
        """POST /api/email/subscribe - Subscribe to newsletter"""
        response = api_client.post(f"{BASE_URL}/api/email/subscribe", json={
            "email": TEST_NEWSLETTER_EMAIL,
            "name": "Test Subscriber"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should have 'message' field"
        assert "status" in data, "Response should have 'status' field"
        assert data["status"] in ["subscribed", "exists"], f"Status should be 'subscribed' or 'exists', got {data['status']}"
        print(f"✓ Newsletter subscribe: {data['message']}, status={data['status']}")
    
    def test_newsletter_subscribe_duplicate(self, api_client):
        """POST /api/email/subscribe - Subscribe with existing email"""
        response = api_client.post(f"{BASE_URL}/api/email/subscribe", json={
            "email": TEST_NEWSLETTER_EMAIL,
            "name": "Test Subscriber Again"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["status"] == "exists", "Duplicate subscription should return 'exists' status"
        print(f"✓ Duplicate subscription handled: {data['message']}")
    
    def test_newsletter_unsubscribe(self, api_client):
        """DELETE /api/email/unsubscribe - Unsubscribe from newsletter"""
        response = api_client.delete(f"{BASE_URL}/api/email/unsubscribe", params={
            "email": TEST_NEWSLETTER_EMAIL
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should have 'message' field"
        assert "email" in data, "Response should have 'email' field"
        print(f"✓ Newsletter unsubscribe: {data['message']}")
    
    def test_newsletter_unsubscribe_not_found(self, api_client):
        """DELETE /api/email/unsubscribe - Unsubscribe non-existent email"""
        response = api_client.delete(f"{BASE_URL}/api/email/unsubscribe", params={
            "email": "nonexistent@example.com"
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ Non-existent email unsubscribe returns 404")


class TestPayPalConfiguration:
    """Test PayPal configuration endpoints"""
    
    def test_paypal_config_status(self, api_client):
        """GET /api/paypal/config - Check PayPal configuration status"""
        response = api_client.get(f"{BASE_URL}/api/paypal/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "configured" in data, "Response should have 'configured' field"
        assert "mode" in data, "Response should have 'mode' field"
        assert "business_email" in data, "Response should have 'business_email' field"
        assert "simple_payments_enabled" in data, "Response should have 'simple_payments_enabled' field"
        assert data["simple_payments_enabled"] == True, "Simple payments should be enabled"
        print(f"✓ PayPal config: configured={data['configured']}, mode={data['mode']}, simple_payments={data['simple_payments_enabled']}")


class TestPayPalOrders:
    """Test PayPal order creation and purchase history"""
    
    def test_paypal_create_order_requires_auth(self, api_client):
        """POST /api/paypal/create-order - Should require authentication"""
        # Remove auth header temporarily
        auth_header = api_client.headers.pop("Authorization", None)
        
        response = api_client.post(f"{BASE_URL}/api/paypal/create-order", json={
            "protocol_id": "test-protocol-id",
            "amount": 9.99
        })
        
        # Restore auth header
        if auth_header:
            api_client.headers["Authorization"] = auth_header
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}: {response.text}"
        print("✓ PayPal create-order requires authentication")
    
    def test_paypal_create_order_invalid_protocol(self, api_client, auth_token):
        """POST /api/paypal/create-order - Invalid protocol ID"""
        response = api_client.post(f"{BASE_URL}/api/paypal/create-order", json={
            "protocol_id": "nonexistent-protocol-id",
            "amount": 9.99
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ PayPal create-order returns 404 for invalid protocol")
    
    def test_paypal_purchases_requires_auth(self, api_client):
        """GET /api/paypal/purchases - Should require authentication"""
        # Remove auth header temporarily
        auth_header = api_client.headers.pop("Authorization", None)
        
        response = api_client.get(f"{BASE_URL}/api/paypal/purchases")
        
        # Restore auth header
        if auth_header:
            api_client.headers["Authorization"] = auth_header
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}: {response.text}"
        print("✓ PayPal purchases requires authentication")
    
    def test_paypal_purchases_list(self, api_client, auth_token):
        """GET /api/paypal/purchases - Get purchase history"""
        response = api_client.get(f"{BASE_URL}/api/paypal/purchases")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "purchases" in data, "Response should have 'purchases' field"
        assert isinstance(data["purchases"], list), "Purchases should be a list"
        print(f"✓ PayPal purchases: {len(data['purchases'])} purchases found")


class TestMarketplaceProtocols:
    """Test marketplace protocol listing"""
    
    def test_marketplace_protocols_list(self, api_client, auth_token):
        """GET /api/marketplace/protocols - Get marketplace protocols"""
        response = api_client.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "protocols" in data, "Response should have 'protocols' field"
        assert "total" in data, "Response should have 'total' field"
        print(f"✓ Marketplace protocols: {data['total']} protocols available")


class TestRestoredPages:
    """Test that restored pages APIs are working"""
    
    def test_reports_api(self, api_client, auth_token):
        """GET /api/reports - Reports page API"""
        response = api_client.get(f"{BASE_URL}/api/reports")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "reports" in data, "Response should have 'reports' field"
        print(f"✓ Reports API: {len(data.get('reports', []))} reports")
    
    def test_revenue_dashboard_api(self, api_client, auth_token):
        """GET /api/revenue/dashboard - Revenue page API"""
        response = api_client.get(f"{BASE_URL}/api/revenue/dashboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total_revenue" in data or "total_earnings" in data, "Response should have revenue data"
        print(f"✓ Revenue dashboard API working: {list(data.keys())}")
    
    def test_templates_api(self, api_client, auth_token):
        """GET /api/templates - Templates page API"""
        response = api_client.get(f"{BASE_URL}/api/templates")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "official_templates" in data or "templates" in data, "Response should have templates data"
        print(f"✓ Templates API working")
    
    def test_stats_api(self, api_client, auth_token):
        """GET /api/stats - Stats page API"""
        response = api_client.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"✓ Stats API working: {list(data.keys())}")
    
    def test_categories_api(self, api_client, auth_token):
        """GET /api/categories - Categories for Ultimate Search"""
        response = api_client.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "categories" in data, "Response should have 'categories' field"
        print(f"✓ Categories API: {len(data.get('categories', []))} categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
