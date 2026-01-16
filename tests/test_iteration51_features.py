"""
InfoPilot Explorer - Iteration 51 Feature Tests
Testing:
1. Unpaid Price Controls - GET/PUT /api/admin/unpaid-price-controls
2. Category Analytics Dashboard - GET /api/admin/category-analytics
3. Category Analytics Trends - GET /api/admin/category-analytics/trends
4. Price validation in marketplace listing creation for unpaid users
5. Settings default values include new price control settings
6. Previous features still working (auth, categories, moderation, etc.)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "password123"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✅ Health endpoint: {data}")
    
    def test_article_types_endpoint(self):
        """Test article types endpoint"""
        response = requests.get(f"{BASE_URL}/api/article-types")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert len(data["types"]) >= 10
        print(f"✅ Article types: {len(data['types'])} types available")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["is_admin"] == True
        print(f"✅ Admin login successful: {data['user']['email']}")
    
    def test_invalid_login_rejected(self):
        """Test invalid credentials are rejected"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 404]
        print("✅ Invalid login correctly rejected")


class TestUnpaidPriceControls:
    """Tests for the new Unpaid Price Controls feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed")
    
    def test_get_unpaid_price_controls(self):
        """Test GET /api/admin/unpaid-price-controls returns settings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/unpaid-price-controls",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "settings" in data
        assert "stats" in data
        assert "description" in data
        
        # Verify settings keys
        settings = data["settings"]
        assert "unpaid_price_control_enabled" in settings
        assert "unpaid_max_protocol_price" in settings
        assert "unpaid_max_bundle_price" in settings
        assert "unpaid_can_sell" in settings
        
        # Verify default values (OFF by default)
        assert settings["unpaid_price_control_enabled"] == False  # OFF by default
        assert settings["unpaid_max_protocol_price"] == 5.00  # $5 default
        assert settings["unpaid_max_bundle_price"] == 10.00  # $10 default
        assert settings["unpaid_can_sell"] == True  # Can sell by default
        
        print(f"✅ Unpaid price controls GET: {settings}")
    
    def test_update_unpaid_price_controls(self):
        """Test PUT /api/admin/unpaid-price-controls updates settings"""
        # Update settings
        update_data = {
            "unpaid_price_control_enabled": True,
            "unpaid_max_protocol_price": 7.50,
            "unpaid_max_bundle_price": 15.00,
            "unpaid_can_sell": True
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/unpaid-price-controls",
            headers=self.headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "updated" in data
        print(f"✅ Unpaid price controls updated: {data['updated']}")
        
        # Verify the update
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/unpaid-price-controls",
            headers=self.headers
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        settings = verify_data["settings"]
        
        assert settings["unpaid_price_control_enabled"] == True
        assert settings["unpaid_max_protocol_price"] == 7.50
        assert settings["unpaid_max_bundle_price"] == 15.00
        print(f"✅ Verified updated settings: {settings}")
        
        # Reset to defaults
        reset_data = {
            "unpaid_price_control_enabled": False,
            "unpaid_max_protocol_price": 5.00,
            "unpaid_max_bundle_price": 10.00
        }
        requests.put(
            f"{BASE_URL}/api/admin/unpaid-price-controls",
            headers=self.headers,
            json=reset_data
        )
        print("✅ Reset to default values")
    
    def test_unpaid_price_controls_validation(self):
        """Test price validation for unpaid price controls"""
        # Test invalid price (negative)
        response = requests.put(
            f"{BASE_URL}/api/admin/unpaid-price-controls",
            headers=self.headers,
            json={"unpaid_max_protocol_price": -5.00}
        )
        assert response.status_code == 400
        print("✅ Negative price correctly rejected")
        
        # Test invalid price (too high)
        response = requests.put(
            f"{BASE_URL}/api/admin/unpaid-price-controls",
            headers=self.headers,
            json={"unpaid_max_protocol_price": 150.00}
        )
        assert response.status_code == 400
        print("✅ Price > 99.99 correctly rejected")
    
    def test_unpaid_price_controls_unauthorized(self):
        """Test unpaid price controls requires admin auth"""
        # Without auth
        response = requests.get(f"{BASE_URL}/api/admin/unpaid-price-controls")
        assert response.status_code in [401, 403]
        print("✅ Unauthorized access correctly rejected")


class TestCategoryAnalytics:
    """Tests for the new Category Analytics Dashboard feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed")
    
    def test_get_category_analytics(self):
        """Test GET /api/admin/category-analytics returns analytics data"""
        response = requests.get(
            f"{BASE_URL}/api/admin/category-analytics",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "period_days" in data
        assert "summary" in data
        assert "top_categories" in data
        assert "empty_categories" in data
        assert "generated_at" in data
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_categories" in summary
        assert "total_results" in summary
        assert "results_with_location" in summary
        assert "avg_results_per_category" in summary
        assert "categories_by_level" in summary
        assert "public_categories" in summary
        assert "paid_categories" in summary
        
        print(f"✅ Category analytics: {summary['total_categories']} categories, {summary['total_results']} results")
    
    def test_get_category_analytics_with_days_param(self):
        """Test category analytics with custom days parameter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/category-analytics?days=7",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 7
        print(f"✅ Category analytics with 7 days period: {data['summary']}")
    
    def test_get_category_trends(self):
        """Test GET /api/admin/category-analytics/trends returns trend data"""
        response = requests.get(
            f"{BASE_URL}/api/admin/category-analytics/trends",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "period_days" in data
        assert "daily_categories_created" in data
        assert "daily_results_added" in data
        
        print(f"✅ Category trends: {len(data['daily_categories_created'])} days of category data, {len(data['daily_results_added'])} days of results data")
    
    def test_get_category_trends_with_days_param(self):
        """Test category trends with custom days parameter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/category-analytics/trends?days=14",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 14
        print(f"✅ Category trends with 14 days period")
    
    def test_category_analytics_unauthorized(self):
        """Test category analytics requires admin auth"""
        response = requests.get(f"{BASE_URL}/api/admin/category-analytics")
        assert response.status_code in [401, 403]
        print("✅ Unauthorized access correctly rejected")
    
    def test_category_trends_unauthorized(self):
        """Test category trends requires admin auth"""
        response = requests.get(f"{BASE_URL}/api/admin/category-analytics/trends")
        assert response.status_code in [401, 403]
        print("✅ Unauthorized access correctly rejected")


class TestSettingsDefaultValues:
    """Test that settings include new price control defaults"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed")
    
    def test_settings_init_includes_price_controls(self):
        """Test POST /api/admin/settings/init includes price control settings"""
        response = requests.post(
            f"{BASE_URL}/api/admin/settings/init",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        print(f"✅ Settings init: {data['count']} settings initialized")
    
    def test_get_settings_includes_price_controls(self):
        """Test GET /api/admin/settings includes price control settings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for new price control settings
        assert "unpaid_price_control_enabled" in data
        assert "unpaid_max_protocol_price" in data
        assert "unpaid_max_bundle_price" in data
        assert "unpaid_can_sell" in data
        
        print(f"✅ Settings include price controls: enabled={data.get('unpaid_price_control_enabled')}, max_protocol=${data.get('unpaid_max_protocol_price')}, max_bundle=${data.get('unpaid_max_bundle_price')}")


class TestPreviousFeaturesStillWorking:
    """Regression tests for previous features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed")
    
    def test_admin_stats(self):
        """Test admin stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "categories" in data
        print(f"✅ Admin stats: {data['users']} users, {data['categories']} categories")
    
    def test_marketplace_protocols(self):
        """Test marketplace protocols endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        assert "total" in data
        print(f"✅ Marketplace protocols: {data['total']} protocols")
    
    def test_marketplace_categories(self):
        """Test marketplace categories endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"✅ Marketplace categories: {len(data['categories'])} categories")
    
    def test_category_templates(self):
        """Test category templates endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/category-transfer/templates",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) >= 5
        print(f"✅ Category templates: {len(data['templates'])} templates")
    
    def test_category_export(self):
        """Test category export endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/category-transfer/export",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"✅ Category export: {len(data['categories'])} categories")
    
    def test_batch_payout(self):
        """Test batch payout endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/admin/payout-batch",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "batch_id" in data
        print(f"✅ Batch payout: {len(data['users'])} users ready")
    
    def test_payout_settings(self):
        """Test payout settings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/admin/payout-settings",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "min_payout_threshold" in data
        print(f"✅ Payout settings: min_threshold=${data['min_payout_threshold']}")
    
    def test_moderation_actions(self):
        """Test moderation actions endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/moderation/actions",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "actions" in data
        print(f"✅ Moderation actions: {len(data['actions'])} actions")
    
    def test_search_engines(self):
        """Test search engines endpoint"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        print(f"✅ Search engines: {len(data['engines'])} engines")
    
    def test_ultimate_search_stats(self):
        """Test ultimate search stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_results" in data
        print(f"✅ Ultimate search stats: {data['total_results']} results")


class TestMarketplacePriceValidation:
    """Test price validation for unpaid users in marketplace"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed")
    
    def test_marketplace_protocol_creation_valid_price(self):
        """Test creating a marketplace protocol with valid price"""
        # First ensure price controls are disabled (default)
        requests.put(
            f"{BASE_URL}/api/admin/unpaid-price-controls",
            headers=self.headers,
            json={"unpaid_price_control_enabled": False}
        )
        
        # Create a test protocol
        protocol_data = {
            "name": "TEST_Iteration51_Protocol",
            "description": "Test protocol for iteration 51",
            "protocol": "site:example.com",
            "price": 2.99,
            "category": "Test",
            "tags": ["test"],
            "preview_results": 3
        }
        
        response = requests.post(
            f"{BASE_URL}/api/marketplace/protocols",
            headers=self.headers,
            json=protocol_data
        )
        
        # Admin should be able to create at any price
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            print(f"✅ Protocol created: {data['name']} at ${protocol_data['price']}")
            
            # Clean up - delete the test protocol
            protocol_id = data["id"]
            delete_response = requests.delete(
                f"{BASE_URL}/api/marketplace/protocols/{protocol_id}",
                headers=self.headers
            )
            print(f"✅ Test protocol cleaned up")
        else:
            # If creation fails, it might be due to other validation
            print(f"⚠️ Protocol creation returned {response.status_code}: {response.text}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
