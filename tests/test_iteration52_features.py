"""
Iteration 52 - Testing CollapsibleCategoryTree, Admin Settings, and API Endpoints
Features to test:
1. Login flow with admin credentials
2. CollapsibleCategoryTree component (frontend)
3. Admin settings: collation_limit=40, newsletter times 05:46, 09:42, 16:20
4. API endpoints: /api/ultimate-search, /api/categories, /api/marketplace/protocols
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infopilot-explorer-3.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"

class TestHealthAndBasicEndpoints:
    """Basic health and endpoint tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health endpoint: {data}")
    
    def test_article_types_endpoint(self):
        """Test article types endpoint returns document types"""
        response = requests.get(f"{BASE_URL}/api/article-types")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert len(data["types"]) >= 10
        print(f"✓ Article types: {len(data['types'])} types returned")
    
    def test_search_engines_endpoint(self):
        """Test search engines endpoint"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        print(f"✓ Search engines: {data['total_available']} available")


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
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful: {data['user']['username']}")
        return data["token"]
    
    def test_invalid_login_rejected(self):
        """Test invalid credentials are rejected"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 404]
        print("✓ Invalid login correctly rejected")


class TestAdminSettings:
    """Admin settings tests - verify collation_limit and newsletter times"""
    
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
    
    def test_admin_settings_init(self, admin_token):
        """Test admin settings initialization includes correct defaults"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Initialize settings
        response = requests.post(f"{BASE_URL}/api/admin/settings/init", headers=headers)
        assert response.status_code == 200
        print("✓ Admin settings initialized")
    
    def test_admin_settings_get(self, admin_token):
        """Test getting admin settings - verify collation_limit and newsletter times"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=headers)
        assert response.status_code == 200
        settings = response.json()
        
        # Verify collation_limit = 40
        assert "collation_limit" in settings
        assert settings["collation_limit"] == 40, f"Expected collation_limit=40, got {settings['collation_limit']}"
        print(f"✓ collation_limit = {settings['collation_limit']}")
        
        # Verify newsletter times
        assert "newsletter_time_1" in settings
        assert settings["newsletter_time_1"] == "05:46", f"Expected newsletter_time_1=05:46, got {settings['newsletter_time_1']}"
        print(f"✓ newsletter_time_1 = {settings['newsletter_time_1']}")
        
        assert "newsletter_time_2" in settings
        assert settings["newsletter_time_2"] == "09:42", f"Expected newsletter_time_2=09:42, got {settings['newsletter_time_2']}"
        print(f"✓ newsletter_time_2 = {settings['newsletter_time_2']}")
        
        assert "newsletter_time_3" in settings
        assert settings["newsletter_time_3"] == "16:20", f"Expected newsletter_time_3=16:20, got {settings['newsletter_time_3']}"
        print(f"✓ newsletter_time_3 = {settings['newsletter_time_3']}")
        
        return settings
    
    def test_admin_stats(self, admin_token):
        """Test admin stats endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "categories" in data
        assert "search_results" in data
        print(f"✓ Admin stats: {data['users']} users, {data['categories']} categories, {data['search_results']} results")


class TestCategoriesAPI:
    """Categories API tests"""
    
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
    
    def test_get_categories(self, admin_token):
        """Test getting user categories"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)
        print(f"✓ Categories endpoint: {len(categories)} categories returned")
        
        # Check category structure if any exist
        if categories:
            cat = categories[0]
            assert "id" in cat or "_id" in cat
            assert "name" in cat
            print(f"  First category: {cat.get('name', 'N/A')}")
        
        return categories


class TestUltimateSearchAPI:
    """Ultimate Search API tests"""
    
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
    
    def test_ultimate_search_get(self, admin_token):
        """Test getting ultimate search results"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/ultimate-search", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data
        print(f"✓ Ultimate Search: {data['count']} results returned")
        
        # Check result structure if any exist
        if data["results"]:
            result = data["results"][0]
            assert "id" in result
            assert "url" in result
            assert "title" in result
            print(f"  First result: {result.get('title', 'N/A')[:50]}...")
        
        return data
    
    def test_ultimate_search_stats(self, admin_token):
        """Test ultimate search stats endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/ultimate-search/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_results" in data
        print(f"✓ Ultimate Search Stats: {data['total_results']} total results")


class TestMarketplaceAPI:
    """Marketplace API tests"""
    
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
    
    def test_marketplace_protocols(self, admin_token):
        """Test marketplace protocols endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        print(f"✓ Marketplace Protocols: {len(data['protocols'])} protocols")
    
    def test_marketplace_categories(self, admin_token):
        """Test marketplace categories endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/marketplace/categories", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"✓ Marketplace Categories: {len(data['categories'])} categories")


class TestCategoryExportAPI:
    """Category export/transfer API tests"""
    
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
    
    def test_category_templates(self, admin_token):
        """Test category templates endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/category-transfer/templates", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        print(f"✓ Category Templates: {len(data['templates'])} templates")
    
    def test_category_export(self, admin_token):
        """Test category export endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/category-transfer/export", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Response has nested structure: data.categories
        assert "data" in data or "categories" in data
        categories = data.get("data", {}).get("categories", data.get("categories", []))
        print(f"✓ Category Export: {len(categories)} categories exported")


class TestUnpaidPriceControls:
    """Unpaid price controls API tests (from iteration 51)"""
    
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
    
    def test_unpaid_price_controls_get(self, admin_token):
        """Test getting unpaid price controls"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/unpaid-price-controls", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "settings" in data
        print(f"✓ Unpaid Price Controls: {data['settings']}")


class TestCategoryAnalytics:
    """Category analytics API tests (from iteration 51)"""
    
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
    
    def test_category_analytics(self, admin_token):
        """Test category analytics endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/category-analytics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "top_categories" in data
        print(f"✓ Category Analytics: {data['summary']['total_categories']} categories analyzed")
    
    def test_category_trends(self, admin_token):
        """Test category trends endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/category-analytics/trends", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "daily_categories_created" in data
        assert "daily_results_added" in data
        print(f"✓ Category Trends: {data['period_days']} days of data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
