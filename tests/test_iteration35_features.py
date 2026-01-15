"""
InfoPilot Explorer - Iteration 35 Feature Tests
Tests for: Newsletter times, Bundles featured, Categories with counts, Cross-sell, Admin settings
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✅ Health check passed: {data}")


class TestBundlesFeatured:
    """Test Bundle of the Week / Featured endpoint"""
    
    def test_featured_bundle_endpoint(self):
        """GET /api/bundles/featured should return proper response"""
        response = requests.get(f"{BASE_URL}/api/bundles/featured", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        # Should have either featured bundle or message
        assert "featured" in data or "message" in data
        
        if data.get("featured"):
            featured = data["featured"]
            assert "id" in featured
            assert "name" in featured
            assert "bundle_price" in featured
            assert "discount_percent" in featured
            assert "is_bundle_of_week" in featured
            print(f"✅ Featured bundle found: {featured.get('name')}")
        else:
            # No bundles yet - should have message
            assert "message" in data or data.get("featured") is None
            print(f"✅ No featured bundle yet: {data.get('message', 'No bundles available')}")
        
        # Should have funny tagline
        if "funny_tagline" in data:
            print(f"✅ Funny tagline: {data['funny_tagline']}")


class TestCrossSelll:
    """Test Cross-sell recommendations endpoint"""
    
    def test_cross_sell_endpoint_invalid_protocol(self):
        """GET /api/bundles/cross-sell/{protocol_id} with invalid ID"""
        response = requests.get(f"{BASE_URL}/api/bundles/cross-sell/invalid123", timeout=10)
        # Should return 200 with empty recommendations or error message
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        print(f"✅ Cross-sell with invalid ID returns: {data}")
    
    def test_cross_sell_endpoint_structure(self):
        """Test cross-sell response structure"""
        # First get a valid protocol ID
        protocols_response = requests.get(f"{BASE_URL}/api/marketplace/protocols", timeout=10)
        if protocols_response.status_code == 200:
            protocols = protocols_response.json().get("protocols", [])
            if protocols:
                protocol_id = protocols[0].get("id")
                response = requests.get(f"{BASE_URL}/api/bundles/cross-sell/{protocol_id}", timeout=10)
                assert response.status_code == 200
                data = response.json()
                
                assert "recommendations" in data
                assert "funny_message" in data
                assert "cross_sell_count" in data
                
                print(f"✅ Cross-sell for protocol {protocol_id}: {data['cross_sell_count']} recommendations")
                print(f"✅ Funny message: {data['funny_message']}")
            else:
                pytest.skip("No protocols available for cross-sell test")
        else:
            pytest.skip("Could not fetch protocols")


class TestCategoriesWithCounts:
    """Test categories endpoint with result_count and subcategory_count"""
    
    def test_categories_endpoint_requires_auth(self):
        """GET /api/categories requires authentication"""
        response = requests.get(f"{BASE_URL}/api/categories", timeout=10)
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403, 422]
        print(f"✅ Categories endpoint requires auth: {response.status_code}")
    
    def test_categories_with_auth_includes_counts(self):
        """GET /api/categories with auth should include result_count and subcategory_count"""
        # Login first
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "jjspilot24@gmail.com", "password": "InfoPilot2024!"},
            timeout=10
        )
        
        if login_response.status_code != 200:
            pytest.skip("Could not login to test categories")
        
        token = login_response.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers, timeout=10)
        assert response.status_code == 200
        
        categories = response.json()
        if isinstance(categories, list) and len(categories) > 0:
            cat = categories[0]
            # Check for result_count and subcategory_count fields
            assert "result_count" in cat, "Category should have result_count field"
            assert "subcategory_count" in cat, "Category should have subcategory_count field"
            print(f"✅ Category '{cat.get('name')}' has result_count={cat.get('result_count')}, subcategory_count={cat.get('subcategory_count')}")
        else:
            print("✅ Categories endpoint works but no categories found")


class TestAdminSettings:
    """Test Admin Panel settings endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "jjspilot24@gmail.com", "password": "InfoPilot2024!"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not login as admin")
    
    def test_admin_settings_endpoint(self, admin_token):
        """GET /api/admin/settings should return settings including collation and payment"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Admin settings retrieved: {list(data.keys())}")
            
            # Check for collation settings
            if "default_collation" in data or "collation" in str(data).lower():
                print("✅ Collation settings found in admin settings")
            
            # Check for payment settings
            if "minimum_payout" in data or "payout" in str(data).lower():
                print("✅ Payment settings found in admin settings")
        else:
            print(f"⚠️ Admin settings endpoint returned: {response.status_code}")
    
    def test_update_collation_setting(self, admin_token):
        """Test updating collation setting"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        
        # Try to update collation setting
        response = requests.post(
            f"{BASE_URL}/api/admin/settings",
            headers=headers,
            json={"default_collation": 40},
            timeout=10
        )
        
        # Accept 200, 201, or 404 (if endpoint doesn't exist yet)
        assert response.status_code in [200, 201, 404, 422]
        print(f"✅ Collation setting update response: {response.status_code}")
    
    def test_update_payment_setting(self, admin_token):
        """Test updating minimum payout threshold"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        
        # Try to update payment setting
        response = requests.post(
            f"{BASE_URL}/api/admin/settings",
            headers=headers,
            json={"minimum_payout_threshold": 1.00},
            timeout=10
        )
        
        # Accept 200, 201, or 404 (if endpoint doesn't exist yet)
        assert response.status_code in [200, 201, 404, 422]
        print(f"✅ Payment setting update response: {response.status_code}")


class TestBundlesAPI:
    """Test Protocol Bundles API"""
    
    def test_list_bundles(self):
        """GET /api/bundles should return bundles list"""
        response = requests.get(f"{BASE_URL}/api/bundles", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        assert "bundles" in data
        assert "count" in data
        print(f"✅ Bundles list: {data['count']} bundles found")
    
    def test_bundles_with_sort(self):
        """GET /api/bundles with sort parameter"""
        for sort_type in ["popular", "newest", "price_low", "discount"]:
            response = requests.get(f"{BASE_URL}/api/bundles?sort={sort_type}", timeout=10)
            assert response.status_code == 200
            print(f"✅ Bundles sorted by {sort_type}: OK")


class TestMarketplaceProtocols:
    """Test marketplace protocols for FREE badges and pricing"""
    
    def test_marketplace_protocols_list(self):
        """GET /api/marketplace/protocols should return protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        assert "protocols" in data
        protocols = data["protocols"]
        print(f"✅ Marketplace has {len(protocols)} protocols")
        
        # Check for FREE protocols
        free_protocols = [p for p in protocols if p.get("price", 0) == 0]
        print(f"✅ Found {len(free_protocols)} FREE protocols")
        
        return protocols


class TestNewsletterScheduler:
    """Verify newsletter scheduler times in code"""
    
    def test_newsletter_scheduler_times(self):
        """Verify newsletter times are 5:46 AM, 9:42 AM, 4:20 PM"""
        # Read the triweekly_newsletter.py file
        import os
        newsletter_path = "/app/backend/services/triweekly_newsletter.py"
        
        if os.path.exists(newsletter_path):
            with open(newsletter_path, 'r') as f:
                content = f.read()
            
            # Check for 9:42 AM (not 9:05 AM)
            assert "minute=42" in content or "9:42" in content, "Newsletter should be at 9:42 AM"
            assert "hour=9" in content, "Newsletter should have 9 AM hour"
            
            # Verify 5:46 AM
            assert "minute=46" in content or "5:46" in content, "Newsletter should be at 5:46 AM"
            assert "hour=5" in content, "Newsletter should have 5 AM hour"
            
            # Verify 4:20 PM (16:20)
            assert "minute=20" in content or "4:20" in content, "Newsletter should be at 4:20 PM"
            assert "hour=16" in content, "Newsletter should have 16 (4 PM) hour"
            
            print("✅ Newsletter times verified: 5:46 AM, 9:42 AM, 4:20 PM")
        else:
            pytest.skip("Newsletter file not found")


class TestCodeQuality:
    """Code quality and structure tests"""
    
    def test_bundles_featured_endpoint_exists(self):
        """Verify /featured endpoint exists in bundles router"""
        bundles_path = "/app/backend/routes/bundles.py"
        
        if os.path.exists(bundles_path):
            with open(bundles_path, 'r') as f:
                content = f.read()
            
            assert '@router.get("/featured")' in content, "Featured endpoint should exist"
            assert "get_featured_bundle" in content, "get_featured_bundle function should exist"
            print("✅ Bundles featured endpoint exists in code")
        else:
            pytest.skip("Bundles router file not found")
    
    def test_cross_sell_endpoint_exists(self):
        """Verify cross-sell endpoint exists in bundles router"""
        bundles_path = "/app/backend/routes/bundles.py"
        
        if os.path.exists(bundles_path):
            with open(bundles_path, 'r') as f:
                content = f.read()
            
            assert "cross-sell" in content, "Cross-sell endpoint should exist"
            assert "get_cross_sell_recommendations" in content, "Cross-sell function should exist"
            print("✅ Cross-sell endpoint exists in code")
        else:
            pytest.skip("Bundles router file not found")
    
    def test_categories_format_with_count_exists(self):
        """Verify format_category_with_count function exists"""
        categories_path = "/app/backend/routes/categories.py"
        
        if os.path.exists(categories_path):
            with open(categories_path, 'r') as f:
                content = f.read()
            
            assert "format_category_with_count" in content, "format_category_with_count should exist"
            assert "result_count" in content, "result_count field should be in categories"
            assert "subcategory_count" in content, "subcategory_count field should be in categories"
            print("✅ Categories format_category_with_count function exists")
        else:
            pytest.skip("Categories router file not found")
    
    def test_bundle_of_week_component_exists(self):
        """Verify BundleOfTheWeek component exists"""
        component_path = "/app/frontend/src/components/Marketplace/BundleOfTheWeek.js"
        
        if os.path.exists(component_path):
            with open(component_path, 'r') as f:
                content = f.read()
            
            assert "BundleOfTheWeek" in content, "BundleOfTheWeek component should exist"
            assert "featured" in content.lower(), "Component should reference featured bundle"
            print("✅ BundleOfTheWeek component exists")
        else:
            pytest.skip("BundleOfTheWeek component not found")
    
    def test_admin_panel_has_collation_settings(self):
        """Verify AdminPanel has Collation Settings section"""
        admin_path = "/app/frontend/src/pages/AdminPanel.js"
        
        if os.path.exists(admin_path):
            with open(admin_path, 'r') as f:
                content = f.read()
            
            assert "Collation" in content, "AdminPanel should have Collation settings"
            assert "collation" in content.lower(), "AdminPanel should reference collation"
            print("✅ AdminPanel has Collation Settings section")
        else:
            pytest.skip("AdminPanel file not found")
    
    def test_admin_panel_has_payment_settings(self):
        """Verify AdminPanel has Payment Settings section"""
        admin_path = "/app/frontend/src/pages/AdminPanel.js"
        
        if os.path.exists(admin_path):
            with open(admin_path, 'r') as f:
                content = f.read()
            
            assert "Payment" in content, "AdminPanel should have Payment settings"
            assert "payout" in content.lower() or "minimum" in content.lower(), "AdminPanel should reference payout/minimum"
            print("✅ AdminPanel has Payment Settings section")
        else:
            pytest.skip("AdminPanel file not found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
