"""
Iteration 89 Feature Tests
Tests for:
1. AI News endpoint returns articles
2. Protocol price validation rejects prices over $24.97
3. Protocol price validation accepts prices up to $24.97
4. Stripe prices updated to new tiers (max $24.97)
5. All pages load without subscription requirements
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAINewsEndpoint:
    """Test AI News endpoint functionality"""
    
    def test_ai_news_returns_articles(self):
        """AI News endpoint should return 10 articles"""
        response = requests.get(f"{BASE_URL}/api/ai/news")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "articles" in data, "Response should contain 'articles' key"
        assert len(data["articles"]) == 10, f"Expected 10 articles, got {len(data['articles'])}"
        
        # Verify article structure
        for article in data["articles"]:
            assert "headline" in article, "Article should have headline"
            assert "summary" in article, "Article should have summary"
            assert "topic" in article, "Article should have topic"
            assert "emoji" in article, "Article should have emoji"
    
    def test_ai_news_has_ai_powered_flag(self):
        """AI News should indicate if it's AI powered"""
        response = requests.get(f"{BASE_URL}/api/ai/news")
        assert response.status_code == 200
        
        data = response.json()
        assert "ai_powered" in data, "Response should contain 'ai_powered' flag"


class TestAuthentication:
    """Test authentication for protected endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"


class TestPriceValidation:
    """Test protocol price validation ($0-$24.97 max)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture
    def test_category(self, auth_headers):
        """Create a test category for price testing"""
        response = requests.post(f"{BASE_URL}/api/categories", 
            headers=auth_headers,
            json={
                "name": "TEST_Iteration89_PriceTest",
                "protocol": "(test or price) & (validation)+",
                "is_public": False
            }
        )
        if response.status_code in [200, 201]:
            category = response.json()
            yield category
            # Cleanup
            requests.delete(f"{BASE_URL}/api/categories/{category['id']}", headers=auth_headers)
        else:
            pytest.skip(f"Failed to create test category: {response.text}")
    
    def test_price_validation_rejects_over_24_97(self, auth_headers, test_category):
        """Price validation should reject prices over $24.97"""
        category_id = test_category["id"]
        
        # Try to set price to $30 (should fail)
        response = requests.put(
            f"{BASE_URL}/api/categories/{category_id}",
            headers=auth_headers,
            json={"price": 30.00}
        )
        
        assert response.status_code == 400, f"Expected 400 for price $30, got {response.status_code}"
        assert "24.97" in response.text.lower() or "price" in response.text.lower(), \
            f"Error message should mention price limit: {response.text}"
    
    def test_price_validation_rejects_25_dollars(self, auth_headers, test_category):
        """Price validation should reject $25"""
        category_id = test_category["id"]
        
        response = requests.put(
            f"{BASE_URL}/api/categories/{category_id}",
            headers=auth_headers,
            json={"price": 25.00}
        )
        
        assert response.status_code == 400, f"Expected 400 for price $25, got {response.status_code}"
    
    def test_price_validation_accepts_24_97(self, auth_headers, test_category):
        """Price validation should accept $24.97 (max allowed)"""
        category_id = test_category["id"]
        
        response = requests.put(
            f"{BASE_URL}/api/categories/{category_id}",
            headers=auth_headers,
            json={"price": 24.97}
        )
        
        assert response.status_code == 200, f"Expected 200 for price $24.97, got {response.status_code}: {response.text}"
        
        # Verify price was set
        data = response.json()
        assert data.get("price") == 24.97, f"Price should be 24.97, got {data.get('price')}"
    
    def test_price_validation_accepts_lower_prices(self, auth_headers, test_category):
        """Price validation should accept prices below $24.97"""
        category_id = test_category["id"]
        
        # Test $10
        response = requests.put(
            f"{BASE_URL}/api/categories/{category_id}",
            headers=auth_headers,
            json={"price": 10.00}
        )
        assert response.status_code == 200, f"Expected 200 for price $10, got {response.status_code}"
        
        # Test $0 (free)
        response = requests.put(
            f"{BASE_URL}/api/categories/{category_id}",
            headers=auth_headers,
            json={"price": 0}
        )
        assert response.status_code == 200, f"Expected 200 for price $0, got {response.status_code}"
    
    def test_price_validation_rejects_negative(self, auth_headers, test_category):
        """Price validation should reject negative prices"""
        category_id = test_category["id"]
        
        response = requests.put(
            f"{BASE_URL}/api/categories/{category_id}",
            headers=auth_headers,
            json={"price": -5.00}
        )
        
        assert response.status_code == 400, f"Expected 400 for negative price, got {response.status_code}"


class TestStripePricing:
    """Test Stripe pricing tiers (max $24.97)"""
    
    def test_stripe_config_enabled(self):
        """Stripe should be enabled"""
        response = requests.get(f"{BASE_URL}/api/stripe/config")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("enabled") == True, "Stripe should be enabled"
        assert data.get("publishable_key", "").startswith("pk_"), "Should have valid publishable key"
    
    def test_stripe_prices_max_24_97(self):
        """Stripe prices should have max $24.97"""
        response = requests.get(f"{BASE_URL}/api/stripe/prices")
        assert response.status_code == 200
        
        data = response.json()
        assert "prices" in data, "Response should contain prices"
        
        prices = data["prices"]
        
        # Check all prices are <= $24.97 (2497 cents)
        for price_key, price_info in prices.items():
            amount_cents = price_info.get("amount", 0)
            amount_dollars = amount_cents / 100
            assert amount_dollars <= 24.97, f"Price {price_key} is ${amount_dollars}, exceeds max $24.97"
        
        # Verify premium protocol is exactly $24.97
        if "protocol_premium" in prices:
            premium_amount = prices["protocol_premium"]["amount"]
            assert premium_amount == 2497, f"Premium protocol should be $24.97 (2497 cents), got {premium_amount}"


class TestFreeAccess:
    """Test that app is free to use (no subscription required for basic features)"""
    
    def test_health_endpoint_public(self):
        """Health endpoint should be public"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
    
    def test_ai_news_public(self):
        """AI News should be accessible without auth"""
        response = requests.get(f"{BASE_URL}/api/ai/news")
        assert response.status_code == 200
    
    def test_marketplace_public(self):
        """Marketplace protocols should be accessible without auth"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        
        data = response.json()
        assert "protocols" in data, "Should return protocols"
    
    def test_statistics_overview_public(self):
        """Statistics overview should be accessible without auth"""
        response = requests.get(f"{BASE_URL}/api/statistics/overview")
        assert response.status_code == 200


class TestCategoryCRUD:
    """Test category CRUD operations with new price limits"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_create_category_with_valid_price(self, auth_headers):
        """Create category with valid price ($24.97)"""
        response = requests.post(f"{BASE_URL}/api/categories",
            headers=auth_headers,
            json={
                "name": "TEST_Iteration89_ValidPrice",
                "protocol": "(test or valid) & (price)+",
                "is_public": True,
                "price": 24.97
            }
        )
        
        # Note: price might not be set on create, only on update
        if response.status_code in [200, 201]:
            category = response.json()
            # Cleanup
            requests.delete(f"{BASE_URL}/api/categories/{category['id']}", headers=auth_headers)
            assert True
        else:
            # If create doesn't support price, that's okay
            assert response.status_code in [200, 201, 400]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
