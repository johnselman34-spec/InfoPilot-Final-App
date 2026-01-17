"""
Iteration 48 - Category Management in Settings & Document Type Filtering Tests

Features to test:
1. Category management in Settings page - edit/delete categories
2. Document type filter checkboxes beneath the map on Ultimate Search
3. Filtered results display at bottom-center when filters are active
4. Article types endpoint returns all 13 document types
5. Category CRUD still works from Ultimate Search page
6. Category delete with cascade (deletes subcategories)
7. Admin moderation tab still functional
8. Search and collate functionality not broken
9. Settings page displays category manager when toggled
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infoshare-4.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestArticleTypesEndpoint:
    """Test the /api/article-types endpoint returns all 13 document types"""
    
    def test_article_types_returns_13_types(self):
        """Verify article-types endpoint returns all 13 document types"""
        response = requests.get(f"{BASE_URL}/api/article-types")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "types" in data, "Response should contain 'types' key"
        
        types = data["types"]
        assert len(types) == 13, f"Expected 13 document types, got {len(types)}"
        
        # Verify all expected types are present
        expected_types = [
            "PhD Informative",
            "Personal Report (Organic)",
            "Personal Report (Collected)",
            "News Article",
            "Academic Paper",
            "Government",
            "Wiki",
            "Blog Post",
            "Forum",
            "Video",
            "PDF Document",
            "MS Word Document",
            "Webpage"
        ]
        
        type_names = [t["name"] for t in types]
        for expected in expected_types:
            assert expected in type_names, f"Missing document type: {expected}"
        
        print(f"✅ Article types endpoint returns all 13 types: {type_names}")
    
    def test_article_types_have_required_fields(self):
        """Verify each article type has id, name, and description"""
        response = requests.get(f"{BASE_URL}/api/article-types")
        assert response.status_code == 200
        
        data = response.json()
        for article_type in data["types"]:
            assert "id" in article_type, f"Missing 'id' in {article_type}"
            assert "name" in article_type, f"Missing 'name' in {article_type}"
            assert "description" in article_type, f"Missing 'description' in {article_type}"
        
        print("✅ All article types have required fields (id, name, description)")


class TestSearchEnginesEndpoint:
    """Test the /api/search-engines endpoint"""
    
    def test_search_engines_returns_status(self):
        """Verify search-engines endpoint returns engine status"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "engines" in data, "Response should contain 'engines' key"
        assert "total_available" in data, "Response should contain 'total_available' key"
        
        engines = data["engines"]
        expected_engines = ["serpapi", "bing", "brave", "duckduckgo", "basic"]
        
        for engine in expected_engines:
            assert engine in engines, f"Missing engine: {engine}"
            assert "name" in engines[engine], f"Missing 'name' in {engine}"
            assert "available" in engines[engine], f"Missing 'available' in {engine}"
            assert "description" in engines[engine], f"Missing 'description' in {engine}"
        
        print(f"✅ Search engines endpoint returns status for {len(engines)} engines")


class TestAuthenticationAndCategories:
    """Test authentication and category CRUD operations"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        data = response.json()
        return data.get("token")
    
    def test_login_success(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.status_code}"
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        print(f"✅ Admin login successful for {ADMIN_EMAIL}")
    
    def test_get_categories(self, auth_token):
        """Test fetching categories"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Categories should be a list"
        print(f"✅ Fetched {len(data)} categories")
    
    def test_create_category(self, auth_token):
        """Test creating a new category"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        category_data = {
            "name": "TEST_Iteration48_Category",
            "protocol": "(test OR iteration48) & (category OR testing)",
            "is_public": False
        }
        
        response = requests.post(f"{BASE_URL}/api/categories", 
                                headers=headers, 
                                json=category_data)
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        data = response.json()
        assert "id" in data or "_id" in data, "Response should contain category ID"
        print(f"✅ Created test category: {category_data['name']}")
        
        # Return the category ID for cleanup
        return data.get("id") or data.get("_id")
    
    def test_update_category(self, auth_token):
        """Test updating a category"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a category with proper protocol format
        create_response = requests.post(f"{BASE_URL}/api/categories", 
                                       headers=headers, 
                                       json={
                                           "name": "TEST_Update_Category",
                                           "protocol": "(test or update)",
                                           "is_public": False
                                       })
        
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create category for update test: {create_response.text}")
        
        category_id = create_response.json().get("id") or create_response.json().get("_id")
        
        # Update the category
        update_data = {
            "name": "TEST_Updated_Category_Name",
            "protocol": "(updated or test)",
            "is_public": True,
            "price": 0
        }
        
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}",
                                      headers=headers,
                                      json=update_data)
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        print(f"✅ Updated category {category_id}")
        
        # Cleanup - delete the category
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
    
    def test_delete_category(self, auth_token):
        """Test deleting a category"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a category to delete with proper protocol format
        create_response = requests.post(f"{BASE_URL}/api/categories", 
                                       headers=headers, 
                                       json={
                                           "name": "TEST_Delete_Category",
                                           "protocol": "(test or delete)",
                                           "is_public": False
                                       })
        
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create category for delete test: {create_response.text}")
        
        category_id = create_response.json().get("id") or create_response.json().get("_id")
        
        # Delete the category
        delete_response = requests.delete(f"{BASE_URL}/api/categories/{category_id}",
                                         headers=headers)
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        print(f"✅ Deleted category {category_id}")
    
    def test_cascade_delete_category(self, auth_token):
        """Test cascade delete - deleting parent removes children"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create parent category with proper protocol format
        parent_response = requests.post(f"{BASE_URL}/api/categories", 
                                       headers=headers, 
                                       json={
                                           "name": "TEST_Parent_Cascade",
                                           "protocol": "(parent or cascade)",
                                           "is_public": False
                                       })
        
        if parent_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create parent category: {parent_response.text}")
        
        parent_id = parent_response.json().get("id") or parent_response.json().get("_id")
        
        # Create child category
        child_response = requests.post(f"{BASE_URL}/api/categories", 
                                      headers=headers, 
                                      json={
                                          "name": "TEST_Child_Cascade",
                                          "protocol": "(child or cascade)",
                                          "parent_id": parent_id,
                                          "is_public": False
                                      })
        
        child_id = None
        if child_response.status_code in [200, 201]:
            child_id = child_response.json().get("id") or child_response.json().get("_id")
        
        # Delete parent - should cascade delete child
        delete_response = requests.delete(f"{BASE_URL}/api/categories/{parent_id}",
                                         headers=headers)
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        
        # Verify child is also deleted (should return 404)
        if child_id:
            # Try to get the child category - should fail
            categories = requests.get(f"{BASE_URL}/api/categories", headers=headers).json()
            child_exists = any(c.get("id") == child_id or c.get("_id") == child_id for c in categories)
            assert not child_exists, "Child category should be deleted with parent"
        
        print(f"✅ Cascade delete verified - parent and child removed")


class TestUltimateSearchEndpoints:
    """Test Ultimate Search related endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        
        return response.json().get("token")
    
    def test_ultimate_search_get(self, auth_token):
        """Test GET /api/ultimate-search returns results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ultimate-search", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "results" in data, "Response should contain 'results'"
        assert "total" in data, "Response should contain 'total'"
        assert "filter_applied" in data, "Response should contain 'filter_applied'"
        assert "aggregation_mode" in data, "Response should contain 'aggregation_mode'"
        
        print(f"✅ Ultimate search returned {len(data['results'])} results")
    
    def test_ultimate_search_with_category_filter(self, auth_token):
        """Test Ultimate Search with category filtering"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get categories
        categories = requests.get(f"{BASE_URL}/api/categories", headers=headers).json()
        
        if not categories:
            pytest.skip("No categories available for filtering test")
        
        category_id = categories[0].get("id") or categories[0].get("_id")
        
        # Test with category filter
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search?category_ids={category_id}&aggregation=and_or",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # When filtering, filter_applied should be true
        if category_id:
            assert data.get("filter_applied") == True, "filter_applied should be True when category_ids provided"
        
        print(f"✅ Category filtering works - filter_applied: {data.get('filter_applied')}")
    
    def test_ultimate_search_stats(self, auth_token):
        """Test Ultimate Search stats endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ultimate-search/stats", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "total_results" in data, "Response should contain 'total_results'"
        assert "total_categories" in data, "Response should contain 'total_categories'"
        assert "article_types" in data, "Response should contain 'article_types'"
        
        print(f"✅ Stats: {data['total_results']} results, {data['total_categories']} categories")
    
    def test_ultimate_search_batches(self, auth_token):
        """Test Ultimate Search batches endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ultimate-search/batches", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "batches" in data, "Response should contain 'batches'"
        print(f"✅ Batches endpoint returned {len(data['batches'])} batches")


class TestAdminEndpoints:
    """Test admin-related endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip("Admin authentication failed")
        
        return response.json().get("token")
    
    def test_admin_settings(self, auth_token):
        """Test admin settings endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=headers)
        
        # Admin settings might be public or require auth
        assert response.status_code in [200, 401], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            print("✅ Admin settings endpoint accessible")
    
    def test_admin_stats(self, auth_token):
        """Test admin stats endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Should have basic stats
        assert "users" in data or "total_users" in data, "Should have user count"
        print(f"✅ Admin stats endpoint working")
    
    def test_admin_users_list(self, auth_token):
        """Test admin users list endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # API returns {"users": [...]} or direct list
        users = data.get("users", data) if isinstance(data, dict) else data
        assert isinstance(users, list), "Users should be a list"
        if len(users) > 0:
            user = users[0]
            assert "email" in user or "id" in user, "User should have email or id"
        
        print(f"✅ Admin users list returned {len(users)} users")
    
    def test_admin_moderation_actions(self, auth_token):
        """Test admin moderation actions endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/moderation/actions", headers=headers)
        
        # This endpoint might return 200 with empty list or 404 if no actions
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            # API returns {"actions": [...]} or direct list
            actions = data.get("actions", data) if isinstance(data, dict) else data
            assert isinstance(actions, list), "Moderation actions should be a list"
            print(f"✅ Moderation actions endpoint returned {len(actions)} actions")


class TestSearchFunctionality:
    """Test search and collate functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        
        return response.json().get("token")
    
    def test_search_endpoint(self, auth_token):
        """Test basic search endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/search",
                                headers=headers,
                                json={"query": "test search"})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "results" in data, "Response should contain 'results'"
        print(f"✅ Search endpoint returned {len(data.get('results', []))} results")
    
    def test_database_search_endpoint(self, auth_token):
        """Test database search endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/database-search",
                                headers=headers,
                                json={
                                    "query": "test",
                                    "mode": "smart",
                                    "limit": 10
                                })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "results" in data, "Response should contain 'results'"
        assert "total_in_database" in data, "Response should contain 'total_in_database'"
        print(f"✅ Database search: {len(data.get('results', []))} results from {data.get('total_in_database', 0)} total")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_categories(self):
        """Clean up any test categories created during testing"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code != 200:
            print("⚠️ Could not authenticate for cleanup")
            return
        
        token = response.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all categories
        categories = requests.get(f"{BASE_URL}/api/categories", headers=headers).json()
        
        # Delete test categories
        deleted_count = 0
        for cat in categories:
            name = cat.get("name", "")
            if name.startswith("TEST_"):
                cat_id = cat.get("id") or cat.get("_id")
                delete_response = requests.delete(f"{BASE_URL}/api/categories/{cat_id}", headers=headers)
                if delete_response.status_code == 200:
                    deleted_count += 1
        
        print(f"✅ Cleanup: Deleted {deleted_count} test categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
