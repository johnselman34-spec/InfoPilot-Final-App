"""
Iteration 90 P0 Bug Tests
Tests for:
1. P0-1: Protocol price validation - backend must accept $0 (FREE), $0.20-$24.97, and reject < $0.20 or > $24.97
2. P0-2: Backend price validation endpoint tests (frontend modal close behavior tested via Playwright)
3. P0-3: Category filtering - verify category selection endpoint works
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuthentication:
    """Test authentication for protected endpoints"""
    
    def test_login_admin_success(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"


class TestPriceValidation:
    """
    P0-1: Protocol price validation
    - Must accept $0 (FREE)
    - Must accept $0.20-$24.97
    - Must reject < $0.20 (except $0)
    - Must reject > $24.97
    """
    
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
                "name": "TEST_Iteration90_PriceTest",
                "protocol": "(test or validation)"
            })
        
        if response.status_code in [200, 201]:
            cat = response.json()
            yield cat
            # Cleanup: delete test category
            requests.delete(f"{BASE_URL}/api/categories/{cat['id']}", headers=auth_headers)
        else:
            pytest.skip(f"Failed to create test category: {response.text}")
    
    def test_price_zero_free_accepted(self, auth_headers, test_category):
        """P0-1: Price $0 (FREE) should be accepted"""
        response = requests.put(f"{BASE_URL}/api/categories/{test_category['id']}", 
            headers=auth_headers,
            json={"price": 0})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Price can be 0, null, or not set for FREE
        assert data.get("price") in [0, None], f"Price should be 0 or null for FREE, got {data.get('price')}"
    
    def test_price_minimum_0_20_accepted(self, auth_headers, test_category):
        """P0-1: Price $0.20 (minimum paid) should be accepted"""
        response = requests.put(f"{BASE_URL}/api/categories/{test_category['id']}", 
            headers=auth_headers,
            json={"price": 0.20})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("price") == 0.20, f"Price should be 0.20, got {data.get('price')}"
    
    def test_price_maximum_24_97_accepted(self, auth_headers, test_category):
        """P0-1: Price $24.97 (maximum) should be accepted"""
        response = requests.put(f"{BASE_URL}/api/categories/{test_category['id']}", 
            headers=auth_headers,
            json={"price": 24.97})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("price") == 24.97, f"Price should be 24.97, got {data.get('price')}"
    
    def test_price_mid_range_accepted(self, auth_headers, test_category):
        """P0-1: Price $10.00 (mid-range) should be accepted"""
        response = requests.put(f"{BASE_URL}/api/categories/{test_category['id']}", 
            headers=auth_headers,
            json={"price": 10.00})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("price") == 10.00, f"Price should be 10.00, got {data.get('price')}"
    
    def test_price_below_minimum_rejected(self, auth_headers, test_category):
        """P0-1: Price $0.19 (below minimum) should be rejected"""
        response = requests.put(f"{BASE_URL}/api/categories/{test_category['id']}", 
            headers=auth_headers,
            json={"price": 0.19})
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data, "Error response should have detail"
        assert "0.20" in data.get("detail", "") or "24.97" in data.get("detail", ""), f"Error should mention price range: {data.get('detail')}"
    
    def test_price_above_maximum_rejected(self, auth_headers, test_category):
        """P0-1: Price $25.00 (above maximum) should be rejected"""
        response = requests.put(f"{BASE_URL}/api/categories/{test_category['id']}", 
            headers=auth_headers,
            json={"price": 25.00})
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data, "Error response should have detail"
    
    def test_price_way_above_maximum_rejected(self, auth_headers, test_category):
        """P0-1: Price $100.00 (way above maximum) should be rejected"""
        response = requests.put(f"{BASE_URL}/api/categories/{test_category['id']}", 
            headers=auth_headers,
            json={"price": 100.00})
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
    
    def test_price_0_01_rejected(self, auth_headers, test_category):
        """P0-1: Price $0.01 (too low) should be rejected"""
        response = requests.put(f"{BASE_URL}/api/categories/{test_category['id']}", 
            headers=auth_headers,
            json={"price": 0.01})
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"


class TestCategoriesEndpoint:
    """
    P0-3: Category filtering - verify categories load correctly
    """
    
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
    
    def test_categories_endpoint_returns_list(self, auth_headers):
        """Categories endpoint should return a list"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_categories_have_required_fields(self, auth_headers):
        """Categories should have required fields for filtering"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            cat = data[0]
            assert "id" in cat, "Category should have id"
            assert "name" in cat, "Category should have name"
            # Optional fields
            # result_count, parent_id, is_public, price, etc
    
    def test_admin_has_categories(self, auth_headers):
        """Admin user should have some categories (expected: 18)"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Admin should have categories - at least 1
        assert len(data) >= 1, f"Admin should have at least 1 category, got {len(data)}"
        print(f"Admin has {len(data)} categories")


class TestUltimateSearchEndpoint:
    """
    Test Ultimate Search endpoint for category filtering
    """
    
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
    
    def test_ultimate_search_loads(self, auth_headers):
        """Ultimate search endpoint should return results"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "results" in data, "Response should have 'results' key"
        assert isinstance(data["results"], list), "Results should be a list"
    
    def test_ultimate_search_with_category_filter(self, auth_headers):
        """Ultimate search should accept category_ids filter parameter"""
        # First get categories
        cat_response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        if cat_response.status_code != 200 or len(cat_response.json()) == 0:
            pytest.skip("No categories available for filtering test")
        
        cats = cat_response.json()
        first_cat_id = cats[0]["id"]
        
        # Search with category filter
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search?category_ids={first_cat_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "results" in data, "Response should have 'results' key"
        # filter_applied key should indicate filtering is in use
        # (may be false if no results match the filter)


class TestHealthCheck:
    """Basic health check tests"""
    
    def test_api_health(self):
        """API should be accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
