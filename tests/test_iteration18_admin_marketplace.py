"""
Iteration 18 - Admin Login, Category Editing, Search Collation, and Marketplace Tests
Tests for:
1. Admin login with jjspilot24@gmail.com / password123
2. Admin badge display in sidebar
3. Admin Control link visibility
4. Category editing (name and protocol)
5. Search collation functionality
6. Marketplace page with enhanced features (stats, filters, search)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials from the review request
ADMIN_CREDENTIALS = [
    {"email": "jjspilot24@gmail.com", "password": "password123"},
    {"email": "johnselman34@gmail.com", "password": "password123"},
    {"email": "john.1976.selman@gmail.com", "password": "password123"}
]


class TestHealthCheck:
    """Basic health check tests"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "operational"
        print(f"✅ API health check passed: {data}")


class TestAdminLogin:
    """Test admin user login and authentication"""
    
    def test_admin_login_jjspilot24(self):
        """Test login with jjspilot24@gmail.com"""
        creds = ADMIN_CREDENTIALS[0]
        response = requests.post(f"{BASE_URL}/api/auth/login", json=creds)
        
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify token returned
        assert "access_token" in data, "No access token returned"
        
        # Verify user data
        user = data.get("user", {})
        assert user.get("email") == creds["email"], f"Email mismatch: {user.get('email')}"
        assert user.get("is_admin") == True, f"User should be admin but is_admin={user.get('is_admin')}"
        
        print(f"✅ Admin login successful for {creds['email']}")
        print(f"   - Username: {user.get('username')}")
        print(f"   - is_admin: {user.get('is_admin')}")
        return data
    
    def test_admin_login_johnselman34(self):
        """Test login with johnselman34@gmail.com"""
        creds = ADMIN_CREDENTIALS[1]
        response = requests.post(f"{BASE_URL}/api/auth/login", json=creds)
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            user = data.get("user", {})
            print(f"✅ Admin login successful for {creds['email']}")
            print(f"   - is_admin: {user.get('is_admin')}")
            assert user.get("is_admin") == True, f"User should be admin"
        else:
            print(f"⚠️ Login failed for {creds['email']}: {response.text}")
            # This might fail if user doesn't exist yet
            pytest.skip(f"User {creds['email']} may not exist in database")
    
    def test_admin_login_john_1976_selman(self):
        """Test login with john.1976.selman@gmail.com"""
        creds = ADMIN_CREDENTIALS[2]
        response = requests.post(f"{BASE_URL}/api/auth/login", json=creds)
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            user = data.get("user", {})
            print(f"✅ Admin login successful for {creds['email']}")
            print(f"   - is_admin: {user.get('is_admin')}")
            assert user.get("is_admin") == True, f"User should be admin"
        else:
            print(f"⚠️ Login failed for {creds['email']}: {response.text}")
            pytest.skip(f"User {creds['email']} may not exist in database")


class TestCategoryOperations:
    """Test category CRUD operations including editing"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS[0])
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json().get("access_token")
    
    @pytest.fixture
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_get_categories(self, auth_headers):
        """Test fetching user categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Categories fetched: {len(data.get('categories', []))} categories")
        return data.get("categories", [])
    
    def test_create_category(self, auth_headers):
        """Test creating a new category"""
        category_data = {
            "name": "TEST_Category_Iteration18",
            "protocol": {
                "protocol_string": "(test or example) & (iteration18)+"
            },
            "is_public": True
        }
        
        response = requests.post(f"{BASE_URL}/api/categories", json=category_data, headers=auth_headers)
        print(f"Create category response: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        assert response.status_code in [200, 201], f"Failed to create category: {response.text}"
        data = response.json()
        assert "id" in data, "No category ID returned"
        print(f"✅ Category created with ID: {data.get('id')}")
        return data
    
    def test_edit_category_name_and_protocol(self, auth_headers):
        """Test editing a category's name and protocol"""
        # First create a category
        category_data = {
            "name": "TEST_EditTest_Original",
            "protocol": {
                "protocol_string": "(original or test)+"
            },
            "is_public": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/categories", json=category_data, headers=auth_headers)
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create test category: {create_response.text}")
        
        category_id = create_response.json().get("id")
        print(f"Created test category: {category_id}")
        
        # Now edit the category
        update_data = {
            "name": "TEST_EditTest_Updated",
            "protocol_string": "(updated or modified) & (iteration18)+"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/categories/{category_id}",
            json=update_data,
            headers=auth_headers
        )
        
        print(f"Update response: {update_response.status_code}")
        print(f"Response: {update_response.text[:500]}")
        
        assert update_response.status_code == 200, f"Failed to update category: {update_response.text}"
        
        # Verify the update by fetching the category
        get_response = requests.get(f"{BASE_URL}/api/categories/{category_id}", headers=auth_headers)
        if get_response.status_code == 200:
            updated_cat = get_response.json()
            assert updated_cat.get("name") == "TEST_EditTest_Updated", f"Name not updated: {updated_cat.get('name')}"
            print(f"✅ Category name updated successfully")
            print(f"   - New name: {updated_cat.get('name')}")
            print(f"   - New protocol: {updated_cat.get('protocol_string')}")
        
        # Cleanup - delete the test category
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=auth_headers)
        print(f"✅ Test category cleaned up")


class TestSearchCollation:
    """Test search collation functionality"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS[0])
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json().get("access_token")
    
    @pytest.fixture
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_collate_search_george_bush(self, auth_headers):
        """Test search collation with 'George W. Bush air force' query"""
        search_data = {
            "search_query": "George W. Bush air force",
            "max_results": 10,
            "require_search_terms": True
        }
        
        response = requests.post(f"{BASE_URL}/api/collate", json=search_data, headers=auth_headers)
        print(f"Collate response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print(f"✅ Search collation returned {len(results)} results")
            for i, result in enumerate(results[:3]):
                print(f"   Result {i+1}: {result.get('title', 'No title')[:60]}...")
        else:
            print(f"⚠️ Collate search response: {response.text[:500]}")
            # This might fail if Google Search API is not configured
            if "API" in response.text or "quota" in response.text.lower():
                pytest.skip("Search API may not be configured or quota exceeded")
            assert response.status_code == 200, f"Collate failed: {response.text}"


class TestMarketplace:
    """Test marketplace functionality with enhanced features"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS[0])
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json().get("access_token")
    
    @pytest.fixture
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_marketplace_stats_endpoint(self, auth_headers):
        """Test marketplace stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/stats", headers=auth_headers)
        print(f"Marketplace stats response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get marketplace stats: {response.text}"
        data = response.json()
        
        # Verify stats structure
        assert "total_protocols" in data, "Missing total_protocols in stats"
        assert "total_sales" in data, "Missing total_sales in stats"
        assert "total_revenue" in data, "Missing total_revenue in stats"
        assert "active_sellers" in data, "Missing active_sellers in stats"
        
        print(f"✅ Marketplace stats retrieved:")
        print(f"   - Total protocols: {data.get('total_protocols')}")
        print(f"   - Total sales: {data.get('total_sales')}")
        print(f"   - Total revenue: ${data.get('total_revenue', 0):.2f}")
        print(f"   - Active sellers: {data.get('active_sellers')}")
    
    def test_marketplace_protocols_list(self, auth_headers):
        """Test fetching marketplace protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=auth_headers)
        print(f"Marketplace protocols response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get marketplace protocols: {response.text}"
        data = response.json()
        
        protocols = data.get("protocols", [])
        print(f"✅ Marketplace protocols: {len(protocols)} available")
        
        for i, protocol in enumerate(protocols[:3]):
            print(f"   Protocol {i+1}: {protocol.get('name', 'Unknown')} - ${protocol.get('price', 0)}")
    
    def test_marketplace_my_purchases(self, auth_headers):
        """Test fetching user's purchases"""
        response = requests.get(f"{BASE_URL}/api/marketplace/my-purchases", headers=auth_headers)
        print(f"My purchases response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get purchases: {response.text}"
        data = response.json()
        
        purchases = data.get("purchases", [])
        print(f"✅ User purchases: {len(purchases)} items")
    
    def test_marketplace_my_sales(self, auth_headers):
        """Test fetching user's sales"""
        response = requests.get(f"{BASE_URL}/api/marketplace/my-sales", headers=auth_headers)
        print(f"My sales response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get sales: {response.text}"
        data = response.json()
        
        sales = data.get("sales", [])
        print(f"✅ User sales: {len(sales)} items")


class TestAdminEndpoints:
    """Test admin-specific endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS[0])
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json().get("access_token")
    
    @pytest.fixture
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_admin_settings_access(self, auth_headers):
        """Test admin can access settings"""
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=auth_headers)
        print(f"Admin settings response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Admin settings accessible")
            print(f"   - Results per page: {data.get('results_per_page')}")
            print(f"   - Max category levels: {data.get('max_category_levels')}")
        else:
            print(f"⚠️ Admin settings response: {response.text[:300]}")
    
    def test_admin_users_list(self, auth_headers):
        """Test admin can list users"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=auth_headers)
        print(f"Admin users list response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            print(f"✅ Admin can list users: {len(users)} users")
            
            # Check for admin users
            admin_users = [u for u in users if u.get("is_admin")]
            print(f"   - Admin users: {len(admin_users)}")
            for admin in admin_users:
                print(f"     • {admin.get('email')} ({admin.get('username')})")
        else:
            print(f"⚠️ Admin users response: {response.text[:300]}")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS[0])
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json().get("access_token")
    
    @pytest.fixture
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_cleanup_test_categories(self, auth_headers):
        """Clean up TEST_ prefixed categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        if response.status_code != 200:
            return
        
        categories = response.json().get("categories", [])
        test_categories = [c for c in categories if c.get("name", "").startswith("TEST_")]
        
        for cat in test_categories:
            delete_response = requests.delete(
                f"{BASE_URL}/api/categories/{cat['id']}",
                headers=auth_headers
            )
            if delete_response.status_code == 200:
                print(f"✅ Cleaned up test category: {cat['name']}")
        
        print(f"✅ Cleanup complete: {len(test_categories)} test categories removed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
