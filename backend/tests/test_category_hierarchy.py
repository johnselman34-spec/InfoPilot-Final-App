"""
InfoPilot Explorer - Category Hierarchy Stability Tests
Comprehensive test suite for nested category CRUD operations
"""
import pytest
import asyncio
from datetime import datetime
from bson import ObjectId

# Test configuration
BASE_URL = "http://localhost:8001/api"
TEST_ADMIN_EMAIL = "jjspilot24@gmail.com"
TEST_ADMIN_PASSWORD = "InfoPilot2024!"


class TestCategoryHierarchy:
    """Test suite for category hierarchy stability"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        import requests
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_create_parent_category(self, admin_token):
        """Test creating a top-level category"""
        import requests
        response = requests.post(
            f"{BASE_URL}/categories",
            json={
                "name": "Test Parent Category",
                "protocol": "weather AND forecast",
                "is_public": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Parent Category"
        assert data["level"] == 0
        assert data["parent_id"] is None
        return data["id"]
    
    def test_create_subcategory(self, admin_token):
        """Test creating a subcategory under a parent"""
        import requests
        
        # First create parent
        parent_response = requests.post(
            f"{BASE_URL}/categories",
            json={
                "name": "Parent for Subcategory Test",
                "protocol": "sports AND news",
                "is_public": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert parent_response.status_code == 200
        parent_id = parent_response.json()["id"]
        
        # Create subcategory
        sub_response = requests.post(
            f"{BASE_URL}/categories",
            json={
                "name": "Test Subcategory",
                "protocol": "basketball OR football",
                "is_public": True,
                "parent_id": parent_id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert sub_response.status_code == 200
        sub_data = sub_response.json()
        assert sub_data["parent_id"] == parent_id
        assert sub_data["level"] == 1
        
        # Cleanup
        requests.delete(f"{BASE_URL}/categories/{sub_data['id']}", headers={"Authorization": f"Bearer {admin_token}"})
        requests.delete(f"{BASE_URL}/categories/{parent_id}", headers={"Authorization": f"Bearer {admin_token}"})
    
    def test_create_deep_hierarchy(self, admin_token):
        """Test creating a 3-level deep hierarchy"""
        import requests
        
        # Level 0 - Parent
        l0_response = requests.post(
            f"{BASE_URL}/categories",
            json={
                "name": "Level 0 Category",
                "protocol": "technology",
                "is_public": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert l0_response.status_code == 200
        l0_id = l0_response.json()["id"]
        
        # Level 1 - Child
        l1_response = requests.post(
            f"{BASE_URL}/categories",
            json={
                "name": "Level 1 Category",
                "protocol": "programming",
                "is_public": True,
                "parent_id": l0_id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert l1_response.status_code == 200
        l1_id = l1_response.json()["id"]
        assert l1_response.json()["level"] == 1
        
        # Level 2 - Grandchild
        l2_response = requests.post(
            f"{BASE_URL}/categories",
            json={
                "name": "Level 2 Category",
                "protocol": "python",
                "is_public": True,
                "parent_id": l1_id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert l2_response.status_code == 200
        l2_id = l2_response.json()["id"]
        assert l2_response.json()["level"] == 2
        
        # Cleanup (delete from bottom up)
        requests.delete(f"{BASE_URL}/categories/{l2_id}", headers={"Authorization": f"Bearer {admin_token}"})
        requests.delete(f"{BASE_URL}/categories/{l1_id}", headers={"Authorization": f"Bearer {admin_token}"})
        requests.delete(f"{BASE_URL}/categories/{l0_id}", headers={"Authorization": f"Bearer {admin_token}"})
    
    def test_delete_parent_cascades_to_children(self, admin_token):
        """Test that deleting a parent also deletes all children"""
        import requests
        
        # Create parent
        parent_response = requests.post(
            f"{BASE_URL}/categories",
            json={
                "name": "Parent to Delete",
                "protocol": "test cascade",
                "is_public": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        parent_id = parent_response.json()["id"]
        
        # Create child
        child_response = requests.post(
            f"{BASE_URL}/categories",
            json={
                "name": "Child to Cascade Delete",
                "protocol": "cascade child",
                "is_public": True,
                "parent_id": parent_id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        child_id = child_response.json()["id"]
        
        # Delete parent
        delete_response = requests.delete(
            f"{BASE_URL}/categories/{parent_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        
        # Verify child was also deleted
        categories = requests.get(
            f"{BASE_URL}/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        ).json()
        
        child_exists = any(cat["id"] == child_id for cat in categories)
        assert not child_exists, "Child category should have been deleted with parent"
    
    def test_edit_category_name_and_protocol(self, admin_token):
        """Test editing category name and protocol"""
        import requests
        
        # Create category
        create_response = requests.post(
            f"{BASE_URL}/categories",
            json={
                "name": "Original Name",
                "protocol": "original protocol",
                "is_public": False
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        cat_id = create_response.json()["id"]
        
        # Edit category
        edit_response = requests.put(
            f"{BASE_URL}/categories/{cat_id}",
            json={
                "name": "Updated Name",
                "protocol": "updated protocol",
                "is_public": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert edit_response.status_code == 200
        updated = edit_response.json()
        assert updated["name"] == "Updated Name"
        assert updated["protocol"] == "updated protocol"
        assert updated["is_public"] == True
        
        # Cleanup
        requests.delete(f"{BASE_URL}/categories/{cat_id}", headers={"Authorization": f"Bearer {admin_token}"})
    
    def test_category_result_count_included(self, admin_token):
        """Test that result_count is included in category response"""
        import requests
        
        # Create category
        create_response = requests.post(
            f"{BASE_URL}/categories",
            json={
                "name": "Count Test Category",
                "protocol": "count test",
                "is_public": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        cat_id = create_response.json()["id"]
        
        # Fetch categories and check for result_count
        categories = requests.get(
            f"{BASE_URL}/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        ).json()
        
        count_cat = next((cat for cat in categories if cat["id"] == cat_id), None)
        assert count_cat is not None
        assert "result_count" in count_cat
        assert "subcategory_count" in count_cat
        
        # Cleanup
        requests.delete(f"{BASE_URL}/categories/{cat_id}", headers={"Authorization": f"Bearer {admin_token}"})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
