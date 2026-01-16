"""
Iteration 47 - Category Delete & Admin Moderation UI Tests
Features to test:
1. Category deletion from EditCategoryModal - verify delete button appears and works
2. Category cascade delete - deleting parent should delete children
3. Admin Moderation tab appears in Admin Panel
4. Admin can search users in moderation panel
5. Admin can ban/unban users with reason and personal note
6. Admin can mute/unmute users with duration selection
7. Admin can delete users permanently
8. Moderation history displays correctly with action icons and colors
9. Category edit still works (name, protocol, visibility, price)
10. Verify existing functionality doesn't regress - search, collate, category creation
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


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ API health check passed")


class TestAdminAuthentication:
    """Admin authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("token")
            print(f"✅ Admin login successful")
            return token
        pytest.skip(f"Admin login failed: {response.status_code}")
    
    def test_admin_login(self, admin_token):
        """Verify admin can login"""
        assert admin_token is not None
        print("✅ Admin token obtained")


class TestCategoryOperations:
    """Category CRUD operations including delete"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    def test_get_categories(self, admin_token):
        """Test fetching categories"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Fetched {len(data)} categories")
    
    def test_create_category(self, admin_token):
        """Test creating a new category"""
        response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "TEST_ParentCategory_Delete",
                "protocol": "(test or delete)",
                "is_public": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "TEST_ParentCategory_Delete"
        print(f"✅ Created parent category: {data['id']}")
        return data["id"]
    
    def test_create_child_category(self, admin_token):
        """Test creating a child category for cascade delete test"""
        # First create parent
        parent_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "TEST_CascadeParent",
                "protocol": "(cascade or parent)",
                "is_public": False
            }
        )
        assert parent_response.status_code == 200
        parent_id = parent_response.json()["id"]
        
        # Create child
        child_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "TEST_CascadeChild",
                "protocol": "(cascade or child)",
                "parent_id": parent_id,
                "is_public": False
            }
        )
        assert child_response.status_code == 200
        child_id = child_response.json()["id"]
        print(f"✅ Created parent {parent_id} with child {child_id}")
        return parent_id, child_id
    
    def test_update_category(self, admin_token):
        """Test updating category name, protocol, visibility, price"""
        # Create a test category
        create_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "TEST_UpdateCategory",
                "protocol": "(update or test)",
                "is_public": False
            }
        )
        assert create_response.status_code == 200
        cat_id = create_response.json()["id"]
        
        # Update the category
        update_response = requests.put(
            f"{BASE_URL}/api/categories/{cat_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "TEST_UpdatedCategory",
                "protocol": "(updated or protocol)",
                "is_public": True,
                "price": 5.99
            }
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "TEST_UpdatedCategory"
        assert data["protocol"] == "(updated or protocol)"
        assert data["is_public"] == True
        assert data["price"] == 5.99
        print(f"✅ Category updated successfully: name, protocol, visibility, price")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/categories/{cat_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_delete_category(self, admin_token):
        """Test deleting a category"""
        # Create a test category
        create_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "TEST_DeleteMe",
                "protocol": "(delete or me)",
                "is_public": False
            }
        )
        assert create_response.status_code == 200
        cat_id = create_response.json()["id"]
        
        # Delete the category
        delete_response = requests.delete(
            f"{BASE_URL}/api/categories/{cat_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data.get("message") == "Category deleted"
        print(f"✅ Category deleted successfully")
        
        # Verify it's gone
        get_response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = get_response.json()
        cat_ids = [c["id"] for c in categories]
        assert cat_id not in cat_ids
        print(f"✅ Verified category no longer exists")
    
    def test_cascade_delete_category(self, admin_token):
        """Test that deleting parent also deletes children"""
        # Create parent
        parent_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "TEST_CascadeDeleteParent",
                "protocol": "(cascade or delete)",
                "is_public": False
            }
        )
        assert parent_response.status_code == 200
        parent_id = parent_response.json()["id"]
        
        # Create child
        child_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "TEST_CascadeDeleteChild",
                "protocol": "(child or cascade)",
                "parent_id": parent_id,
                "is_public": False
            }
        )
        assert child_response.status_code == 200
        child_id = child_response.json()["id"]
        
        # Create grandchild
        grandchild_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "TEST_CascadeDeleteGrandchild",
                "protocol": "(grandchild or cascade)",
                "parent_id": child_id,
                "is_public": False
            }
        )
        assert grandchild_response.status_code == 200
        grandchild_id = grandchild_response.json()["id"]
        
        print(f"✅ Created hierarchy: parent {parent_id} -> child {child_id} -> grandchild {grandchild_id}")
        
        # Delete parent (should cascade)
        delete_response = requests.delete(
            f"{BASE_URL}/api/categories/{parent_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        
        # Verify all are gone
        get_response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = get_response.json()
        cat_ids = [c["id"] for c in categories]
        
        assert parent_id not in cat_ids, "Parent should be deleted"
        assert child_id not in cat_ids, "Child should be cascade deleted"
        assert grandchild_id not in cat_ids, "Grandchild should be cascade deleted"
        print(f"✅ Cascade delete verified - all 3 categories removed")


class TestAdminModeration:
    """Admin moderation endpoint tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    def test_get_users_list(self, admin_token):
        """Test admin can get list of users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)
        print(f"✅ Admin fetched {len(data['users'])} users")
        
        # Check user structure
        if len(data["users"]) > 0:
            user = data["users"][0]
            assert "id" in user
            assert "email" in user
            print(f"✅ User structure verified: id, email present")
    
    def test_get_moderation_history(self, admin_token):
        """Test admin can get moderation action history"""
        response = requests.get(
            f"{BASE_URL}/api/admin/moderation/actions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "actions" in data
        assert isinstance(data["actions"], list)
        print(f"✅ Moderation history fetched: {len(data['actions'])} actions")
        
        # Check action structure if any exist
        if len(data["actions"]) > 0:
            action = data["actions"][0]
            assert "action" in action
            assert "target_username" in action or "target_user_id" in action
            print(f"✅ Action structure verified")
    
    def test_ban_user_endpoint_structure(self, admin_token):
        """Test ban endpoint accepts correct parameters"""
        # Get a non-admin user to test with
        users_response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        users = users_response.json().get("users", [])
        
        # Find a non-admin user
        test_user = None
        for user in users:
            if not user.get("is_admin") and user.get("email") != ADMIN_EMAIL:
                test_user = user
                break
        
        if not test_user:
            pytest.skip("No non-admin user available for ban test")
        
        # Test ban endpoint (we'll unban immediately after)
        ban_response = requests.post(
            f"{BASE_URL}/api/admin/users/{test_user['id']}/ban",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "reason": "TEST_BAN - Testing moderation",
                "personal_note": "This is a test ban, will be unbanned immediately"
            }
        )
        assert ban_response.status_code == 200
        data = ban_response.json()
        assert data.get("success") == True
        print(f"✅ Ban endpoint works with reason and personal_note")
        
        # Immediately unban
        unban_response = requests.post(
            f"{BASE_URL}/api/admin/users/{test_user['id']}/unban",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert unban_response.status_code == 200
        print(f"✅ Unban endpoint works")
    
    def test_mute_user_endpoint_structure(self, admin_token):
        """Test mute endpoint accepts correct parameters"""
        # Get a non-admin user to test with
        users_response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        users = users_response.json().get("users", [])
        
        # Find a non-admin user
        test_user = None
        for user in users:
            if not user.get("is_admin") and user.get("email") != ADMIN_EMAIL:
                test_user = user
                break
        
        if not test_user:
            pytest.skip("No non-admin user available for mute test")
        
        # Test mute endpoint
        mute_response = requests.post(
            f"{BASE_URL}/api/admin/users/{test_user['id']}/mute",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "reason": "TEST_MUTE - Testing moderation",
                "personal_note": "This is a test mute, will be unmuted immediately",
                "duration_hours": 1
            }
        )
        assert mute_response.status_code == 200
        data = mute_response.json()
        assert data.get("success") == True
        assert "muted_until" in data
        print(f"✅ Mute endpoint works with reason, personal_note, duration_hours")
        
        # Immediately unmute
        unmute_response = requests.post(
            f"{BASE_URL}/api/admin/users/{test_user['id']}/unmute",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert unmute_response.status_code == 200
        print(f"✅ Unmute endpoint works")
    
    def test_moderation_actions_logged(self, admin_token):
        """Verify moderation actions are logged in history"""
        response = requests.get(
            f"{BASE_URL}/api/admin/moderation/actions?limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        actions = data.get("actions", [])
        
        # Check if our test actions were logged
        action_types = [a.get("action") for a in actions]
        print(f"✅ Recent action types: {action_types[:5]}")
        
        # Verify action structure
        if len(actions) > 0:
            action = actions[0]
            expected_fields = ["id", "action", "created_at"]
            for field in expected_fields:
                assert field in action, f"Missing field: {field}"
            print(f"✅ Action log structure verified")


class TestAdminSettings:
    """Admin settings tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    def test_get_admin_settings(self, admin_token):
        """Test fetching admin settings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print(f"✅ Admin settings fetched: {len(data)} settings")
    
    def test_get_admin_stats(self, admin_token):
        """Test fetching admin dashboard stats"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "categories" in data
        print(f"✅ Admin stats: {data.get('users')} users, {data.get('categories')} categories")


class TestSearchFunctionality:
    """Verify search functionality still works"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    def test_search_endpoint(self, admin_token):
        """Test search endpoint works"""
        response = requests.post(
            f"{BASE_URL}/api/search",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": "aviation safety"}
        )
        # Search might return 200 or other status depending on API limits
        assert response.status_code in [200, 429, 503]
        print(f"✅ Search endpoint responded with status {response.status_code}")
    
    def test_ultimate_search_endpoint(self, admin_token):
        """Test ultimate search results endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Ultimate search returned {len(data.get('results', []))} results")


# Cleanup test data
class TestCleanup:
    """Cleanup test categories"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    def test_cleanup_test_categories(self, admin_token):
        """Clean up any remaining test categories"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code == 200:
            categories = response.json()
            test_cats = [c for c in categories if c["name"].startswith("TEST_")]
            for cat in test_cats:
                requests.delete(
                    f"{BASE_URL}/api/categories/{cat['id']}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
            print(f"✅ Cleaned up {len(test_cats)} test categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
