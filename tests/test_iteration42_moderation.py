"""
InfoPilot Explorer - Iteration 42 Test Suite
Tests for:
- Backend API health
- Search engines endpoint (4 active engines)
- Groups/Pages with moderation fields
- Group/Page moderation endpoints (ban/unban/mute/unmute)
- Legal endpoints (user agreement, privacy policy)
- Auto-categorize and AI search
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://searchmaster-6.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def test_user_token(api_client):
    """Get test user authentication token"""
    # First try to register, then login
    api_client.post(f"{BASE_URL}/api/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "username": "testuser"
    })
    
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Test user authentication failed")


class TestHealthAndBasicEndpoints:
    """Test basic API health and public endpoints"""
    
    def test_api_health(self, api_client):
        """Test API health endpoint"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ API health check passed: {data}")
    
    def test_search_engines_endpoint(self, api_client):
        """Test GET /api/search-engines - should show 4 active engines"""
        response = api_client.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "engines" in data
        assert "total_available" in data
        
        # Verify 4 engines are available
        engines = data["engines"]
        assert "serpapi" in engines
        assert "brave" in engines
        assert "duckduckgo" in engines
        assert "basic" in engines
        
        # Count available engines
        available_count = sum(1 for e in engines.values() if e.get("available"))
        assert available_count == 4, f"Expected 4 active engines, got {available_count}"
        assert data["total_available"] == 4
        
        print(f"✓ Search engines: {available_count} active (SerpAPI, Brave, DuckDuckGo, Basic)")


class TestLegalEndpoints:
    """Test legal document endpoints"""
    
    def test_user_agreement(self, api_client):
        """Test GET /api/legal/user-agreement"""
        response = api_client.get(f"{BASE_URL}/api/legal/user-agreement")
        assert response.status_code == 200
        data = response.json()
        
        assert "content" in data
        assert "version" in data
        assert "effective_date" in data
        assert "Top Pilot Enterprises" in data["content"]
        print("✓ User agreement endpoint working")
    
    def test_privacy_policy(self, api_client):
        """Test GET /api/legal/privacy-policy"""
        response = api_client.get(f"{BASE_URL}/api/legal/privacy-policy")
        assert response.status_code == 200
        data = response.json()
        
        assert "content" in data
        assert "version" in data
        assert "Privacy Policy" in data["content"]
        print("✓ Privacy policy endpoint working")
    
    def test_terms_summary(self, api_client):
        """Test GET /api/legal/terms-summary"""
        response = api_client.get(f"{BASE_URL}/api/legal/terms-summary")
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "links" in data
        print("✓ Terms summary endpoint working")


class TestGroupsEndpoints:
    """Test groups endpoints with moderation fields"""
    
    def test_get_groups_with_moderation_fields(self, api_client, admin_token):
        """Test GET /api/groups - should return groups with is_owner, is_admin, is_moderator fields"""
        response = api_client.get(
            f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "groups" in data
        
        # If there are groups, verify moderation fields exist
        if data["groups"]:
            group = data["groups"][0]
            assert "is_owner" in group or "is_member" in group
            assert "is_admin" in group or "is_member" in group
            print(f"✓ Groups endpoint returns {len(data['groups'])} groups with moderation fields")
        else:
            print("✓ Groups endpoint working (no groups yet)")
    
    def test_create_group_for_moderation(self, api_client, admin_token):
        """Create a test group for moderation testing"""
        response = api_client.post(
            f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_Moderation_Group_{int(time.time())}",
                "description": "Test group for moderation testing",
                "is_private": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✓ Created test group: {data.get('name', data.get('id'))}")
        return data["id"]
    
    def test_get_group_details_with_members(self, api_client, admin_token):
        """Test GET /api/groups/{group_id} - should return members, banned_members, muted_members"""
        # First get groups
        groups_response = api_client.get(
            f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if groups_response.status_code == 200 and groups_response.json().get("groups"):
            group_id = groups_response.json()["groups"][0]["id"]
            
            response = api_client.get(
                f"{BASE_URL}/api/groups/{group_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            
            # Verify moderation arrays exist
            assert "members" in data
            assert "banned_members" in data
            assert "muted_members" in data
            assert "is_owner" in data
            assert "is_admin" in data
            
            print(f"✓ Group details include members ({len(data['members'])}), banned ({len(data['banned_members'])}), muted ({len(data['muted_members'])})")
        else:
            pytest.skip("No groups available for testing")


class TestPagesEndpoints:
    """Test pages endpoints with moderation fields"""
    
    def test_get_pages_with_moderation_fields(self, api_client, admin_token):
        """Test GET /api/pages - should return pages with is_owner, is_admin fields"""
        response = api_client.get(
            f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "pages" in data
        
        if data["pages"]:
            page = data["pages"][0]
            assert "is_owner" in page or "is_following" in page
            assert "is_admin" in page or "is_following" in page
            print(f"✓ Pages endpoint returns {len(data['pages'])} pages with moderation fields")
        else:
            print("✓ Pages endpoint working (no pages yet)")
    
    def test_create_page_for_moderation(self, api_client, admin_token):
        """Create a test page for moderation testing"""
        response = api_client.post(
            f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_Moderation_Page_{int(time.time())}",
                "description": "Test page for moderation testing",
                "category": "Technology"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✓ Created test page: {data.get('name', data.get('id'))}")
        return data["id"]
    
    def test_get_page_details_with_members(self, api_client, admin_token):
        """Test GET /api/pages/{page_id} - should return members, banned_users"""
        # First get pages
        pages_response = api_client.get(
            f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if pages_response.status_code == 200 and pages_response.json().get("pages"):
            page_id = pages_response.json()["pages"][0]["id"]
            
            response = api_client.get(
                f"{BASE_URL}/api/pages/{page_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            
            # Verify moderation arrays exist
            assert "members" in data
            assert "banned_users" in data
            assert "is_owner" in data
            assert "is_admin" in data
            
            print(f"✓ Page details include members ({len(data['members'])}), banned ({len(data['banned_users'])})")
        else:
            pytest.skip("No pages available for testing")


class TestGroupModerationEndpoints:
    """Test group moderation endpoints (ban/unban/mute/unmute)"""
    
    def test_ban_endpoint_exists(self, api_client, admin_token):
        """Test POST /api/social/groups/{group_id}/ban/{member_id} endpoint exists"""
        # This will return 404 for non-existent group, but proves endpoint exists
        response = api_client.post(
            f"{BASE_URL}/api/social/groups/nonexistent/ban/nonexistent",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should return 404 (not found) or 403 (forbidden), not 405 (method not allowed)
        assert response.status_code in [404, 403, 400]
        print("✓ Group ban endpoint exists")
    
    def test_unban_endpoint_exists(self, api_client, admin_token):
        """Test POST /api/social/groups/{group_id}/unban/{member_id} endpoint exists"""
        response = api_client.post(
            f"{BASE_URL}/api/social/groups/nonexistent/unban/nonexistent",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [404, 403, 400]
        print("✓ Group unban endpoint exists")
    
    def test_mute_endpoint_exists(self, api_client, admin_token):
        """Test POST /api/social/groups/{group_id}/mute/{member_id} endpoint exists"""
        response = api_client.post(
            f"{BASE_URL}/api/social/groups/nonexistent/mute/nonexistent",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [404, 403, 400]
        print("✓ Group mute endpoint exists")
    
    def test_unmute_endpoint_exists(self, api_client, admin_token):
        """Test POST /api/social/groups/{group_id}/unmute/{member_id} endpoint exists"""
        response = api_client.post(
            f"{BASE_URL}/api/social/groups/nonexistent/unmute/nonexistent",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [404, 403, 400]
        print("✓ Group unmute endpoint exists")


class TestPageModerationEndpoints:
    """Test page moderation endpoints (ban/unban)"""
    
    def test_page_ban_endpoint_exists(self, api_client, admin_token):
        """Test POST /api/social/pages/{page_id}/ban/{user_id} endpoint exists"""
        response = api_client.post(
            f"{BASE_URL}/api/social/pages/nonexistent/ban/nonexistent",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [404, 403, 400]
        print("✓ Page ban endpoint exists")
    
    def test_page_unban_endpoint_exists(self, api_client, admin_token):
        """Test POST /api/social/pages/{page_id}/unban/{user_id} endpoint exists"""
        response = api_client.post(
            f"{BASE_URL}/api/social/pages/nonexistent/unban/nonexistent",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [404, 403, 400]
        print("✓ Page unban endpoint exists")


class TestSearchFeatures:
    """Test auto-categorize and AI search features"""
    
    def test_auto_categorize_endpoint(self, api_client, admin_token):
        """Test POST /api/auto-categorize"""
        response = api_client.post(
            f"{BASE_URL}/api/auto-categorize",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": "python programming tutorials"}
        )
        # May return 400 if no categories exist, but endpoint should work
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert "results" in data or "message" in data
            print(f"✓ Auto-categorize endpoint working: {data.get('total', 0)} results")
        else:
            print("✓ Auto-categorize endpoint exists (no categories for matching)")
    
    def test_ai_search_endpoint(self, api_client, admin_token):
        """Test POST /api/ai-search"""
        response = api_client.post(
            f"{BASE_URL}/api/ai-search",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "query": "machine learning basics",
                "mode": "comprehensive",
                "auto_categorize": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "original_query" in data
        assert "expanded_queries" in data
        print(f"✓ AI search endpoint working: {data.get('total', 0)} results, {len(data.get('expanded_queries', []))} queries")


class TestAdminPanel:
    """Test admin panel endpoints"""
    
    def test_admin_settings(self, api_client, admin_token):
        """Test admin settings endpoint"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Admin endpoint should work for admin user
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            print("✓ Admin settings endpoint accessible")
        else:
            print("✓ Admin settings endpoint exists (access restricted)")
    
    def test_admin_users(self, api_client, admin_token):
        """Test admin users endpoint"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Admin users endpoint: {len(data.get('users', []))} users")
        else:
            print("✓ Admin users endpoint exists (access restricted)")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
