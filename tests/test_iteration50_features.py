"""
InfoPilot Explorer - Iteration 50 Feature Tests
Tests for:
1. Category Import/Export APIs
2. Category Templates
3. Share to Marketplace
4. Batch Payout System
5. Payout Settings
"""
import pytest
import requests
import os
import json
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://searchmaster-6.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthAndBasics:
    """Basic health checks"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ Health endpoint working")
    
    def test_article_types_endpoint(self):
        """Test article types endpoint"""
        response = requests.get(f"{BASE_URL}/api/article-types")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert len(data["types"]) >= 10
        print(f"✅ Article types endpoint returns {len(data['types'])} types")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"✅ Admin login successful: {data['user'].get('email')}")
        return data["token"]
    
    def test_invalid_login(self):
        """Test invalid login is rejected"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 404]
        print("✅ Invalid login correctly rejected")


class TestCategoryTemplates:
    """Test category templates API"""
    
    def test_get_templates(self):
        """Test GET /api/category-transfer/templates returns 5 templates"""
        response = requests.get(f"{BASE_URL}/api/category-transfer/templates")
        assert response.status_code == 200
        data = response.json()
        
        assert "templates" in data
        assert "total" in data
        assert data["total"] == 5
        
        # Verify template structure
        templates = data["templates"]
        template_ids = [t["id"] for t in templates]
        
        expected_ids = ["research", "news", "business", "tech", "personal"]
        for expected_id in expected_ids:
            assert expected_id in template_ids, f"Missing template: {expected_id}"
        
        # Verify each template has required fields
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "category_count" in template
            assert "categories" in template
            assert len(template["categories"]) > 0
            
            # Verify category structure
            for cat in template["categories"]:
                assert "name" in cat
                assert "protocol" in cat
                assert "level" in cat
        
        print(f"✅ Templates endpoint returns {data['total']} templates: {template_ids}")
        return templates


class TestCategoryExport:
    """Test category export APIs"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_export_categories(self, auth_token):
        """Test GET /api/category-transfer/export"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/category-transfer/export", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert data["success"] == True
        assert "data" in data or "message" in data
        
        if "data" in data:
            export_data = data["data"]
            assert "version" in export_data
            assert "exported_at" in export_data
            assert "categories" in export_data
            assert "metadata" in export_data
            
            print(f"✅ Export endpoint returns {len(export_data.get('categories', []))} categories")
        else:
            print(f"✅ Export endpoint: {data.get('message')}")
    
    def test_export_download(self, auth_token):
        """Test GET /api/category-transfer/export/download returns downloadable JSON"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/category-transfer/export/download", headers=headers)
        
        assert response.status_code == 200
        
        # Check content type is JSON
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type
        
        # Check content-disposition header for download
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition
        assert "infopilot_categories" in content_disposition
        
        # Verify JSON is valid
        data = response.json()
        assert "version" in data
        assert "categories" in data
        
        print(f"✅ Export download returns valid JSON file with {len(data.get('categories', []))} categories")


class TestCategoryImport:
    """Test category import APIs"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_import_categories_skip_strategy(self, auth_token):
        """Test POST /api/category-transfer/import with skip strategy"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        # Create test import data
        import_data = {
            "version": "1.0",
            "categories": [
                {"name": "TEST_Import_Category_1", "protocol": "(test or import) & (category or data)", "level": 0},
                {"name": "TEST_Import_Category_2", "protocol": "(sample or example) & (import or export)", "level": 0}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/category-transfer/import?merge_strategy=skip",
            headers=headers,
            json=import_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert data["success"] == True
        assert "results" in data or "stats" in data
        
        if "stats" in data:
            stats = data["stats"]
            print(f"✅ Import (skip): {stats.get('imported_count', 0)} imported, {stats.get('skipped_count', 0)} skipped")
        else:
            print(f"✅ Import (skip): {data.get('message')}")
    
    def test_import_template(self, auth_token):
        """Test POST /api/category-transfer/import-template/{template_id}"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Import the "tech" template
        response = requests.post(
            f"{BASE_URL}/api/category-transfer/import-template/tech",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert data["success"] == True
        
        if "stats" in data:
            stats = data["stats"]
            print(f"✅ Import template 'tech': {stats.get('imported_count', 0)} imported, {stats.get('skipped_count', 0)} skipped")
        else:
            print(f"✅ Import template 'tech': {data.get('message')}")
    
    def test_import_invalid_template(self, auth_token):
        """Test importing non-existent template returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/category-transfer/import-template/nonexistent",
            headers=headers
        )
        
        assert response.status_code == 404
        print("✅ Invalid template correctly returns 404")
    
    def test_import_invalid_format(self, auth_token):
        """Test importing invalid data returns 400"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        # Missing 'categories' field
        invalid_data = {"version": "1.0"}
        
        response = requests.post(
            f"{BASE_URL}/api/category-transfer/import",
            headers=headers,
            json=invalid_data
        )
        
        assert response.status_code == 400
        print("✅ Invalid import format correctly returns 400")


class TestShareToMarketplace:
    """Test share to marketplace API"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_share_to_marketplace_no_categories(self, auth_token):
        """Test share to marketplace with no categories returns 400"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/category-transfer/share-to-marketplace",
            headers=headers,
            json={"category_ids": [], "name": "Test Bundle", "price": 0}
        )
        
        assert response.status_code == 400
        print("✅ Share to marketplace with no categories correctly returns 400")


class TestBatchPayoutSystem:
    """Test batch payout APIs (admin only)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin authentication failed")
    
    def test_get_payout_batch(self, admin_token):
        """Test GET /api/marketplace/admin/payout-batch"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/marketplace/admin/payout-batch", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "batch_id" in data
        assert "users" in data
        assert "total_users" in data
        assert "total_amount" in data
        assert "min_payout_threshold" in data
        
        print(f"✅ Payout batch: {data['total_users']} users, ${data['total_amount']:.2f} total")
    
    def test_get_payout_settings(self, admin_token):
        """Test GET /api/marketplace/admin/payout-settings"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/marketplace/admin/payout-settings", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "min_payout_threshold" in data
        assert "auto_payout_enabled" in data
        assert "batch_limit" in data
        
        print(f"✅ Payout settings: threshold=${data['min_payout_threshold']}, auto={data['auto_payout_enabled']}")
    
    def test_update_payout_settings(self, admin_token):
        """Test PUT /api/marketplace/admin/payout-settings"""
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/marketplace/admin/payout-settings",
            headers=headers,
            json={"auto_payout_enabled": False, "batch_limit": 100}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert data["success"] == True
        
        print("✅ Payout settings updated successfully")
    
    def test_process_batch_payout_empty(self, admin_token):
        """Test POST /api/marketplace/admin/process-batch-payout with empty batch"""
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/marketplace/admin/process-batch-payout",
            headers=headers,
            json={"batch_id": "TEST_BATCH", "user_ids": []}
        )
        
        assert response.status_code == 400
        print("✅ Empty batch payout correctly returns 400")
    
    def test_payout_batch_unauthorized(self):
        """Test payout batch without admin access returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/marketplace/admin/payout-batch")
        assert response.status_code in [401, 403]
        print("✅ Payout batch correctly requires authentication")


class TestExistingMarketplaceFeatures:
    """Test existing marketplace features still work"""
    
    def test_marketplace_protocols(self):
        """Test GET /api/marketplace/protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        
        assert "protocols" in data
        assert "total" in data
        
        print(f"✅ Marketplace has {data['total']} protocols")
    
    def test_marketplace_categories(self):
        """Test GET /api/marketplace/categories"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        print(f"✅ Marketplace has {len(data['categories'])} categories")
    
    def test_paypal_config(self):
        """Test GET /api/marketplace/paypal-config"""
        response = requests.get(f"{BASE_URL}/api/marketplace/paypal-config")
        assert response.status_code == 200
        data = response.json()
        
        assert "client_id" in data
        assert "currency" in data
        
        print(f"✅ PayPal config: currency={data['currency']}")


class TestAdminFeatures:
    """Test admin features still work"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin authentication failed")
    
    def test_admin_stats(self, admin_token):
        """Test GET /api/admin/stats"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_users" in data or "users" in data
        print(f"✅ Admin stats endpoint working")
    
    def test_admin_revenue_settings(self, admin_token):
        """Test GET /api/marketplace/admin/revenue-settings"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/admin/revenue-settings", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "admin_percent" in data
        assert "creator_percent" in data
        
        print(f"✅ Revenue settings: admin={data['admin_percent']}%, creator={data['creator_percent']}%")
    
    def test_admin_pending_payouts(self, admin_token):
        """Test GET /api/marketplace/admin/payouts"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/admin/payouts", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "ready_for_payout" in data
        assert "min_payout_threshold" in data
        
        print(f"✅ Pending payouts: {len(data['ready_for_payout'])} users ready")


class TestCategoryManagement:
    """Test category CRUD still works"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_get_categories(self, auth_token):
        """Test GET /api/categories"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✅ Categories endpoint returns {len(data)} categories")
    
    def test_create_and_delete_category(self, auth_token):
        """Test category creation and deletion"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        # Create category
        create_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers=headers,
            json={
                "name": "TEST_Iteration50_Category",
                "protocol": "(test or iteration) & (fifty or 50)",
                "is_public": False
            }
        )
        
        assert create_response.status_code in [200, 201]
        created = create_response.json()
        assert "id" in created
        
        category_id = created["id"]
        print(f"✅ Created test category: {category_id}")
        
        # Delete category
        delete_response = requests.delete(
            f"{BASE_URL}/api/categories/{category_id}",
            headers=headers
        )
        
        assert delete_response.status_code == 200
        print(f"✅ Deleted test category: {category_id}")


class TestSearchFeatures:
    """Test search features still work"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_search_engines(self):
        """Test GET /api/search-engines"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200
        data = response.json()
        
        assert "engines" in data
        assert "total_available" in data
        
        print(f"✅ Search engines: {data['total_available']} available")
    
    def test_ultimate_search_stats(self, auth_token):
        """Test GET /api/ultimate-search/stats"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ultimate-search/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_results" in data
        assert "total_categories" in data
        
        print(f"✅ Ultimate search stats: {data['total_results']} results, {data['total_categories']} categories")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_cleanup_test_categories(self, auth_token):
        """Clean up TEST_ prefixed categories"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get all categories
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        if response.status_code != 200:
            print("⚠️ Could not fetch categories for cleanup")
            return
        
        categories = response.json()
        deleted_count = 0
        
        for cat in categories:
            if cat.get("name", "").startswith("TEST_"):
                delete_response = requests.delete(
                    f"{BASE_URL}/api/categories/{cat['id']}",
                    headers=headers
                )
                if delete_response.status_code == 200:
                    deleted_count += 1
        
        print(f"✅ Cleanup: Deleted {deleted_count} test categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
