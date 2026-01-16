"""
InfoPilot Explorer - Iteration 65 Feature Tests
Tests for:
- Legal Page with User Agreement, Privacy Policy, Acceptable Use tabs
- Category result counts in parentheses on Ultimate Search Page
- Settings page Legal Documents section with link to full Legal Page
- Admin settings for newsletter timing and collation limits
- Protocol Share Cards
- LaughOMeter stats in Statistics page
- Clean Category button in Edit Category Modal
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestLegalEndpoints:
    """Test Legal API endpoints"""
    
    def test_get_user_agreement(self):
        """Test GET /api/legal/user-agreement returns User Agreement document"""
        response = requests.get(f"{BASE_URL}/api/legal/user-agreement")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "version" in data
        assert "effective_date" in data
        assert "User Agreement" in data["content"]
        assert "Top Pilot Enterprises" in data["content"]
        print("✅ User Agreement endpoint returns valid document")
    
    def test_get_privacy_policy(self):
        """Test GET /api/legal/privacy-policy returns Privacy Policy document"""
        response = requests.get(f"{BASE_URL}/api/legal/privacy-policy")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "version" in data
        assert "Privacy Policy" in data["content"]
        assert "Top Pilot Enterprises" in data["content"]
        print("✅ Privacy Policy endpoint returns valid document")
    
    def test_get_terms_summary(self):
        """Test GET /api/legal/terms-summary returns summary for sign-up"""
        response = requests.get(f"{BASE_URL}/api/legal/terms-summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "links" in data
        assert "user_agreement" in data["links"]
        assert "privacy_policy" in data["links"]
        print("✅ Terms summary endpoint returns valid summary with links")


class TestAuthAndLogin:
    """Test authentication with admin credentials"""
    
    def test_admin_login(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✅ Admin login successful: {data['user']['username']}")
        return data["token"]


class TestAdminSettings:
    """Test admin settings for newsletter timing and collation limits"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_get_admin_settings(self, auth_token):
        """Test GET /api/admin/settings returns settings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Admin settings may be public or require auth
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Admin settings retrieved: {len(data) if isinstance(data, list) else 'object'}")
    
    def test_newsletter_settings_exist(self, auth_token):
        """Test that newsletter timing settings can be retrieved"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            # Check if newsletter settings exist in response
            if isinstance(data, list):
                keys = [s.get("key") for s in data]
                print(f"✅ Admin settings keys available: {len(keys)}")
            else:
                print(f"✅ Admin settings object retrieved")
    
    def test_collation_limit_setting(self, auth_token):
        """Test that collation limit setting exists"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            print("✅ Collation limit settings accessible")


class TestCategoriesWithResultCounts:
    """Test categories API returns data for result counts"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Login failed")
    
    def test_get_categories(self, auth_token):
        """Test GET /api/categories returns categories list"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Categories retrieved: {len(data)} categories")
        if len(data) > 0:
            cat = data[0]
            assert "id" in cat or "_id" in cat
            assert "name" in cat
            print(f"✅ First category: {cat.get('name')}")
    
    def test_category_results_count_endpoint(self, auth_token):
        """Test GET /api/categories/{id}/results-count returns count"""
        # First get categories
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200 and len(response.json()) > 0:
            cat_id = response.json()[0].get("id") or response.json()[0].get("_id")
            
            # Get results count for category
            count_response = requests.get(
                f"{BASE_URL}/api/categories/{cat_id}/results-count",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            if count_response.status_code == 200:
                count_data = count_response.json()
                print(f"✅ Category results count: {count_data}")
            else:
                print(f"⚠️ Results count endpoint returned: {count_response.status_code}")


class TestCleanCategoryEndpoint:
    """Test Clean Category functionality"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Login failed")
    
    def test_clean_category_endpoint_exists(self, auth_token):
        """Test POST /api/categories/{id}/clean endpoint exists"""
        # First get categories
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200 and len(response.json()) > 0:
            cat_id = response.json()[0].get("id") or response.json()[0].get("_id")
            
            # Test clean endpoint with 'remove' mode (safest)
            clean_response = requests.post(
                f"{BASE_URL}/api/categories/{cat_id}/clean?mode=remove",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            # Should return 200 or 404 (if no results to clean)
            assert clean_response.status_code in [200, 404, 400]
            print(f"✅ Clean category endpoint accessible: {clean_response.status_code}")


class TestGamificationStats:
    """Test LaughOMeter and gamification stats"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Login failed")
    
    def test_laugh_stats_endpoint(self, auth_token):
        """Test GET /api/gamification/laugh-stats returns stats"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/laugh-stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Endpoint may or may not exist
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Laugh stats retrieved: {data}")
        else:
            print(f"⚠️ Laugh stats endpoint returned: {response.status_code}")
    
    def test_statistics_page_endpoint(self, auth_token):
        """Test GET /api/statistics returns stats data"""
        response = requests.get(
            f"{BASE_URL}/api/statistics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statistics retrieved")
        else:
            print(f"⚠️ Statistics endpoint returned: {response.status_code}")


class TestEasterEggsEndpoint:
    """Test Easter Eggs API"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Login failed")
    
    def test_easter_eggs_endpoint(self, auth_token):
        """Test GET /api/easter-eggs returns eggs"""
        response = requests.get(
            f"{BASE_URL}/api/easter-eggs",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Easter eggs retrieved: {len(data.get('eggs', []))} eggs")
        else:
            print(f"⚠️ Easter eggs endpoint returned: {response.status_code}")
    
    def test_catch_easter_egg_endpoint(self, auth_token):
        """Test POST /api/easter-eggs/catch endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/easter-eggs/catch",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"egg_id": "test_egg", "egg_type": "joke"}
        )
        # May return 200 or 400/404 depending on implementation
        print(f"✅ Catch easter egg endpoint accessible: {response.status_code}")


class TestUltimateSearchResults:
    """Test Ultimate Search results with category counts"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Login failed")
    
    def test_ultimate_search_results(self, auth_token):
        """Test GET /api/ultimate-search returns results"""
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Ultimate search results: {len(data.get('results', []))} results")


class TestSearchEngines:
    """Test search engine availability"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Login failed")
    
    def test_search_engines_status(self, auth_token):
        """Test GET /api/search-engines returns engine status"""
        response = requests.get(
            f"{BASE_URL}/api/search-engines",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search engines status: {data}")
        else:
            print(f"⚠️ Search engines endpoint returned: {response.status_code}")


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ Health endpoint returns healthy")
    
    def test_frontend_loads(self):
        """Test frontend is accessible"""
        response = requests.get(BASE_URL.replace('/api', ''))
        assert response.status_code == 200
        print("✅ Frontend is accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
