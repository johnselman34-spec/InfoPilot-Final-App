"""
Iteration 15 - Research Database & Global Database Page Tests
Tests for:
1. Research Database API endpoints
2. Admin resource management
3. Trending topics
4. Top contributors leaderboard
5. Map data
6. Stats endpoint
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestAuthSetup:
    """Authentication setup tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get regular user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        pytest.skip(f"User authentication failed: {response.status_code} - {response.text}")
    
    def test_admin_login(self, admin_token):
        """Test admin can login successfully"""
        assert admin_token is not None
        assert len(admin_token) > 0
        print(f"✓ Admin login successful, token length: {len(admin_token)}")
    
    def test_user_login(self, user_token):
        """Test regular user can login successfully"""
        assert user_token is not None
        assert len(user_token) > 0
        print(f"✓ User login successful, token length: {len(user_token)}")


class TestResearchDatabaseResources:
    """Tests for /api/research-database/resources endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get regular user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("User authentication failed")
    
    def test_get_resources_authenticated(self, user_token):
        """Test GET /api/research-database/resources with authentication"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/api/research-database/resources", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        assert "total" in data
        assert "page" in data
        assert "total_pages" in data
        assert "categories" in data
        assert isinstance(data["resources"], list)
        assert isinstance(data["categories"], list)
        print(f"✓ GET resources: {data['total']} total resources, {len(data['categories'])} categories")
    
    def test_get_resources_unauthenticated(self):
        """Test GET /api/research-database/resources without authentication"""
        response = requests.get(f"{BASE_URL}/api/research-database/resources")
        # Should require authentication
        assert response.status_code in [401, 403]
        print(f"✓ Unauthenticated request correctly rejected: {response.status_code}")
    
    def test_get_resources_with_category_filter(self, user_token):
        """Test GET /api/research-database/resources with category filter"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/api/research-database/resources?category=Science", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        # All returned resources should be in Science category
        for resource in data["resources"]:
            assert resource.get("category") == "Science"
        print(f"✓ Category filter works: {len(data['resources'])} Science resources")
    
    def test_get_resources_with_search(self, user_token):
        """Test GET /api/research-database/resources with search query"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/api/research-database/resources?search=research", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        print(f"✓ Search filter works: {len(data['resources'])} results for 'research'")
    
    def test_create_resource_admin(self, admin_token):
        """Test POST /api/research-database/resources (admin only)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resource_data = {
            "title": f"TEST_Resource_{uuid.uuid4().hex[:8]}",
            "description": "Test research resource for automated testing",
            "url": "https://example.com/test-resource",
            "category": "Science",
            "tags": ["test", "automation", "research"],
            "location": "United States",
            "lat": 40.7128,
            "lng": -74.0060,
            "featured": True
        }
        
        response = requests.post(f"{BASE_URL}/api/research-database/resources", 
                                json=resource_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == resource_data["title"]
        assert data["category"] == "Science"
        assert data["featured"] == True
        print(f"✓ Admin created resource: {data['id']}")
        
        # Cleanup - delete the test resource
        delete_response = requests.delete(f"{BASE_URL}/api/research-database/resources/{data['id']}", 
                                         headers=headers)
        assert delete_response.status_code == 200
        print(f"✓ Test resource cleaned up")
    
    def test_create_resource_non_admin_forbidden(self, user_token):
        """Test POST /api/research-database/resources fails for non-admin"""
        headers = {"Authorization": f"Bearer {user_token}"}
        resource_data = {
            "title": "TEST_Unauthorized_Resource",
            "description": "This should fail",
            "url": "https://example.com/fail",
            "category": "Science",
            "tags": ["test"]
        }
        
        response = requests.post(f"{BASE_URL}/api/research-database/resources", 
                                json=resource_data, headers=headers)
        
        assert response.status_code == 403
        print(f"✓ Non-admin correctly forbidden from creating resources")
    
    def test_delete_resource_admin(self, admin_token):
        """Test DELETE /api/research-database/resources/{id} (admin only)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First create a resource to delete
        resource_data = {
            "title": f"TEST_ToDelete_{uuid.uuid4().hex[:8]}",
            "description": "Resource to be deleted",
            "url": "https://example.com/delete-me",
            "category": "Technology",
            "tags": ["delete", "test"]
        }
        
        create_response = requests.post(f"{BASE_URL}/api/research-database/resources", 
                                       json=resource_data, headers=headers)
        assert create_response.status_code == 200
        resource_id = create_response.json()["id"]
        
        # Now delete it
        delete_response = requests.delete(f"{BASE_URL}/api/research-database/resources/{resource_id}", 
                                         headers=headers)
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["success"] == True
        print(f"✓ Admin deleted resource: {resource_id}")
        
        # Verify it's gone - should return empty or not found
        get_response = requests.get(f"{BASE_URL}/api/research-database/resources?search={resource_data['title']}", 
                                   headers=headers)
        assert get_response.status_code == 200
        assert len(get_response.json()["resources"]) == 0
        print(f"✓ Verified resource is deleted")


class TestResearchDatabaseTrending:
    """Tests for /api/research-database/trending endpoint"""
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("User authentication failed")
    
    def test_get_trending_topics(self, user_token):
        """Test GET /api/research-database/trending"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/api/research-database/trending", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "trending_hashtags" in data
        assert "trending_categories" in data
        assert isinstance(data["trending_hashtags"], list)
        assert isinstance(data["trending_categories"], list)
        print(f"✓ Trending: {len(data['trending_hashtags'])} hashtags, {len(data['trending_categories'])} categories")
        
        # Verify hashtag structure if any exist
        if data["trending_hashtags"]:
            hashtag = data["trending_hashtags"][0]
            assert "tag" in hashtag
            assert "count" in hashtag
            print(f"  Top hashtag: {hashtag['tag']} ({hashtag['count']} occurrences)")
        
        # Verify category structure if any exist
        if data["trending_categories"]:
            category = data["trending_categories"][0]
            assert "id" in category
            assert "name" in category
            assert "count" in category
            print(f"  Top category: {category['name']} ({category['count']} results)")


class TestResearchDatabaseContributors:
    """Tests for /api/research-database/contributors endpoint"""
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("User authentication failed")
    
    def test_get_top_contributors(self, user_token):
        """Test GET /api/research-database/contributors"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/api/research-database/contributors", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "contributors" in data
        assert isinstance(data["contributors"], list)
        print(f"✓ Contributors: {len(data['contributors'])} top contributors")
        
        # Verify contributor structure if any exist
        if data["contributors"]:
            contributor = data["contributors"][0]
            assert "rank" in contributor
            assert "user_id" in contributor
            assert "username" in contributor
            assert "protocol_count" in contributor
            assert "total_copies" in contributor
            print(f"  #1 Contributor: {contributor['username']} - {contributor['protocol_count']} protocols, {contributor['total_copies']} copies")


class TestResearchDatabaseMapData:
    """Tests for /api/research-database/map-data endpoint"""
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("User authentication failed")
    
    def test_get_map_data(self, user_token):
        """Test GET /api/research-database/map-data"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/api/research-database/map-data", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        assert "research_hotspots" in data
        assert "total_resources" in data
        assert "total_hotspots" in data
        assert isinstance(data["resources"], list)
        assert isinstance(data["research_hotspots"], list)
        print(f"✓ Map data: {data['total_resources']} resources, {data['total_hotspots']} hotspots")
        
        # Verify hotspot structure if any exist
        if data["research_hotspots"]:
            hotspot = data["research_hotspots"][0]
            assert "name" in hotspot
            assert "lat" in hotspot
            assert "lng" in hotspot
            assert "count" in hotspot
            print(f"  Sample hotspot: {hotspot['name']} ({hotspot['count']} results)")


class TestResearchDatabaseStats:
    """Tests for /api/research-database/stats endpoint"""
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("User authentication failed")
    
    def test_get_stats(self, user_token):
        """Test GET /api/research-database/stats"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/api/research-database/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_resources" in data
        assert "total_results" in data
        assert "total_public_protocols" in data
        assert "total_users" in data
        assert "category_distribution" in data
        
        assert isinstance(data["total_resources"], int)
        assert isinstance(data["total_results"], int)
        assert isinstance(data["total_public_protocols"], int)
        assert isinstance(data["total_users"], int)
        assert isinstance(data["category_distribution"], list)
        
        print(f"✓ Stats: {data['total_resources']} resources, {data['total_results']} results, {data['total_public_protocols']} protocols, {data['total_users']} users")


class TestAdminAccess:
    """Tests for admin access verification"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_admin_user_has_admin_flag(self, admin_token):
        """Test that admin user has is_admin flag set"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("is_admin") == True or data.get("role") == "admin"
        print(f"✓ Admin user verified: {data.get('username')} is_admin={data.get('is_admin')}")
    
    def test_admin_can_access_admin_settings(self, admin_token):
        """Test admin can access admin settings endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "results_per_page" in data
        print(f"✓ Admin can access settings: results_per_page={data.get('results_per_page')}")


class TestResourceViewIncrement:
    """Tests for resource view increment endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("User authentication failed")
    
    def test_increment_view_count(self, admin_token, user_token):
        """Test POST /api/research-database/resources/{id}/view"""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # First create a resource
        resource_data = {
            "title": f"TEST_ViewCount_{uuid.uuid4().hex[:8]}",
            "description": "Resource for view count testing",
            "url": "https://example.com/view-test",
            "category": "Technology",
            "tags": ["test", "views"]
        }
        
        create_response = requests.post(f"{BASE_URL}/api/research-database/resources", 
                                       json=resource_data, headers=admin_headers)
        assert create_response.status_code == 200
        resource_id = create_response.json()["id"]
        initial_views = create_response.json().get("views", 0)
        
        # Increment view count
        view_response = requests.post(f"{BASE_URL}/api/research-database/resources/{resource_id}/view", 
                                     headers=user_headers)
        assert view_response.status_code == 200
        assert view_response.json()["success"] == True
        print(f"✓ View count incremented for resource: {resource_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/research-database/resources/{resource_id}", headers=admin_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
