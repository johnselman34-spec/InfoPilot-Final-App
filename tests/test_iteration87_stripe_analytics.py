"""
Iteration 87 - Comprehensive Stability Test
Tests: Stripe Payment Integration, Map Analytics Dashboard, Core Features
"""
import pytest
import requests
import os
import json
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestStripePaymentIntegration:
    """Test Stripe payment endpoints - NEW FEATURE"""
    
    def test_stripe_config_returns_enabled(self):
        """Stripe config should return enabled=true with publishable key"""
        response = requests.get(f"{BASE_URL}/api/stripe/config")
        assert response.status_code == 200
        data = response.json()
        assert "publishable_key" in data
        assert "enabled" in data
        assert data["enabled"] == True
        assert data["publishable_key"].startswith("pk_live_")
        print(f"✓ Stripe config: enabled={data['enabled']}, key starts with pk_live_")
    
    def test_stripe_prices_returns_pricing_options(self):
        """Stripe prices should return pricing options"""
        response = requests.get(f"{BASE_URL}/api/stripe/prices")
        assert response.status_code == 200
        data = response.json()
        assert "prices" in data
        assert "currency" in data
        assert data["currency"] == "usd"
        
        # Verify pricing structure
        prices = data["prices"]
        expected_prices = ["protocol_basic", "protocol_pro", "protocol_premium", 
                          "subscription_monthly", "subscription_yearly"]
        for price_key in expected_prices:
            assert price_key in prices, f"Missing price: {price_key}"
            assert "name" in prices[price_key]
            assert "amount" in prices[price_key]
        
        print(f"✓ Stripe prices: {len(prices)} pricing options available")


class TestAuthentication:
    """Test authentication flow"""
    
    def test_login_success(self):
        """Admin login should succeed"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"✓ Login successful for {ADMIN_EMAIL}")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Invalid login should fail"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 400]
        print("✓ Invalid login correctly rejected")


class TestCategoriesEndpoints:
    """Test categories CRUD operations"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_categories_requires_auth(self):
        """Categories endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 401
        print("✓ Categories endpoint correctly requires auth")
    
    def test_get_categories_with_auth(self, auth_token):
        """Get categories with authentication"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 16, f"Expected 16+ categories, got {len(data)}"
        print(f"✓ Categories loaded: {len(data)} categories")
    
    def test_create_update_delete_category(self, auth_token):
        """Test full CRUD cycle for categories"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # CREATE
        create_payload = {
            "name": f"TEST_Iteration87_{datetime.now().timestamp()}",
            "protocol": "(test) & (iteration)",
            "is_private": False,
            "price": 0
        }
        create_response = requests.post(f"{BASE_URL}/api/categories", 
                                        json=create_payload, headers=headers)
        assert create_response.status_code == 200
        created = create_response.json()
        assert "id" in created or "_id" in created
        cat_id = created.get("id") or created.get("_id")
        print(f"✓ Category created: {cat_id}")
        
        # UPDATE
        update_payload = {"name": f"TEST_Updated_{datetime.now().timestamp()}"}
        update_response = requests.put(f"{BASE_URL}/api/categories/{cat_id}",
                                       json=update_payload, headers=headers)
        assert update_response.status_code == 200
        print(f"✓ Category updated: {cat_id}")
        
        # DELETE
        delete_response = requests.delete(f"{BASE_URL}/api/categories/{cat_id}",
                                          headers=headers)
        assert delete_response.status_code == 200
        print(f"✓ Category deleted: {cat_id}")


class TestCorePages:
    """Test core page endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_statistics_overview(self):
        """Statistics overview endpoint"""
        response = requests.get(f"{BASE_URL}/api/statistics/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_categories" in data
        assert "total_searches" in data
        print(f"✓ Statistics: {data['total_users']} users, {data['total_categories']} categories")
    
    def test_marketplace_protocols(self):
        """Marketplace protocols endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        assert "total" in data
        print(f"✓ Marketplace: {data['total']} protocols available")
    
    def test_map_data_endpoint(self, auth_token):
        """Map data endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/map-data", headers=headers)
        assert response.status_code == 200
        print("✓ Map data endpoint working")
    
    def test_admin_users_endpoint(self, auth_token):
        """Admin users endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data or isinstance(data, list)
        print("✓ Admin users endpoint working")
    
    def test_admin_settings_endpoint(self, auth_token):
        """Admin settings endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=headers)
        assert response.status_code == 200
        print("✓ Admin settings endpoint working")
    
    def test_gamification_leaderboard(self, auth_token):
        """Gamification leaderboard endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard", headers=headers)
        assert response.status_code == 200
        print("✓ Gamification leaderboard endpoint working")
    
    def test_search_engines_endpoint(self):
        """Search engines endpoint"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        print(f"✓ Search engines: {data.get('total_available', 0)} engines available")
    
    def test_ultimate_search_endpoint(self, auth_token):
        """Ultimate search endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ultimate-search?limit=5", headers=headers)
        assert response.status_code == 200
        print("✓ Ultimate search endpoint working")


class TestAIFeatures:
    """Test AI-related features"""
    
    def test_ai_news_endpoint(self):
        """AI news endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai/news")
        assert response.status_code == 200
        print("✓ AI news endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
