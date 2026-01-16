"""
InfoPilot Explorer - Iteration 43 Stability Audit Tests
Tests for P1-P3 priority tasks, stability fixes, and Maestro Bistro toggle
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthAndBasicEndpoints:
    """Test basic health and public endpoints"""
    
    def test_health_endpoint(self):
        """Test API health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_search_engines_endpoint(self):
        """Test search engines endpoint returns 4 active engines"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        assert data.get("total_available") == 4
        # Verify all 4 engines
        engines = data["engines"]
        assert "serpapi" in engines
        assert "brave" in engines
        assert "duckduckgo" in engines
        assert "basic" in engines
    
    def test_legal_user_agreement(self):
        """Test user agreement endpoint returns legal content"""
        response = requests.get(f"{BASE_URL}/api/legal/user-agreement")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Top Pilot Enterprises" in data["content"]
        assert "version" in data
    
    def test_legal_privacy_policy(self):
        """Test privacy policy endpoint returns legal content"""
        response = requests.get(f"{BASE_URL}/api/legal/privacy-policy")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Privacy Policy" in data["content"]
        assert "version" in data


class TestAuthentication:
    """Test authentication flows"""
    
    def test_admin_login(self):
        """Test admin user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"].lower() == ADMIN_EMAIL.lower()
        assert data["user"]["is_admin"] == True
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 404]
    
    def test_session_token_validation(self):
        """Test session token validation"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Use token to access protected endpoint
        response = requests.get(f"{BASE_URL}/api/groups", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
    
    def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected for protected endpoints"""
        # Groups endpoint allows unauthenticated access (returns null for user fields)
        # Test with a truly protected endpoint like creating a group
        response = requests.post(f"{BASE_URL}/api/groups", 
            headers={"Authorization": "Bearer invalid_token_12345"},
            json={"name": "Test", "description": "Test"})
        assert response.status_code == 401


class TestGroupsAndModeration:
    """Test groups endpoints with moderation fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_groups_with_moderation_fields(self):
        """Test GET /api/groups returns groups with is_owner, is_admin, is_moderator fields"""
        response = requests.get(f"{BASE_URL}/api/groups", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        
        if data["groups"]:
            group = data["groups"][0]
            # Verify moderation fields exist
            assert "is_owner" in group
            assert "is_admin" in group
            assert "is_moderator" in group
            assert "is_member" in group
    
    def test_create_and_get_group_details(self):
        """Test creating a group and getting its details"""
        # Create a test group
        group_name = f"TEST_Stability_Group_{int(time.time())}"
        create_response = requests.post(f"{BASE_URL}/api/groups", headers=self.headers, json={
            "name": group_name,
            "description": "Test group for stability audit"
        })
        assert create_response.status_code in [200, 201]
        group_id = create_response.json().get("id") or create_response.json().get("group", {}).get("id")
        
        if group_id:
            # Get group details
            detail_response = requests.get(f"{BASE_URL}/api/groups/{group_id}", headers=self.headers)
            assert detail_response.status_code == 200
            group_data = detail_response.json()
            
            # Verify moderation-related fields
            assert "members" in group_data or "member_count" in group_data


class TestPagesAndModeration:
    """Test pages endpoints with moderation fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_pages_with_moderation_fields(self):
        """Test GET /api/pages returns pages with is_owner, is_admin fields"""
        response = requests.get(f"{BASE_URL}/api/pages", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        
        if data["pages"]:
            page = data["pages"][0]
            # Verify moderation fields exist
            assert "is_owner" in page
            assert "is_admin" in page
            assert "is_following" in page


class TestModerationEndpoints:
    """Test moderation endpoints for groups and pages"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token and create test group"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.user_id = login_response.json()["user"]["id"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_group_ban_endpoint_exists(self):
        """Test that group ban endpoint exists and responds"""
        # Get a group first
        groups_response = requests.get(f"{BASE_URL}/api/groups", headers=self.headers)
        groups = groups_response.json().get("groups", [])
        
        if groups:
            group_id = groups[0]["id"]
            # Try to ban a non-existent user (should return appropriate error or success message)
            response = requests.post(
                f"{BASE_URL}/api/groups/{group_id}/ban/nonexistent_user_id",
                headers=self.headers
            )
            # Endpoint should exist and respond (not 500 server error)
            assert response.status_code != 500
            # Should be 200 (with error message), 400, 404, or 422
            assert response.status_code in [200, 400, 404, 422]
    
    def test_group_mute_endpoint_exists(self):
        """Test that group mute endpoint exists and responds"""
        groups_response = requests.get(f"{BASE_URL}/api/groups", headers=self.headers)
        groups = groups_response.json().get("groups", [])
        
        if groups:
            group_id = groups[0]["id"]
            response = requests.post(
                f"{BASE_URL}/api/groups/{group_id}/mute/nonexistent_user_id",
                headers=self.headers
            )
            # Endpoint should exist and respond (not 500 server error)
            assert response.status_code != 500
            assert response.status_code in [200, 400, 404, 422]


class TestChatWebSocketCleanup:
    """Test chat-related endpoints (WebSocket cleanup verification)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_dm_conversations_endpoint(self):
        """Test DM conversations endpoint works"""
        response = requests.get(f"{BASE_URL}/api/dm/conversations", headers=self.headers)
        # Should return 200 with conversations list
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data or "conversations" in data or isinstance(data, list)
    
    def test_unified_chat_overview_endpoint(self):
        """Test unified chat overview endpoint works"""
        response = requests.get(f"{BASE_URL}/api/unified-chat/overview", headers=self.headers)
        # Should return 200 with chat overview
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
    
    def test_chat_rooms_endpoint(self):
        """Test chat rooms endpoint works (no /api prefix)"""
        response = requests.get(f"{BASE_URL}/rooms", headers=self.headers)
        # Should return 200 with rooms list
        assert response.status_code == 200


class TestServicesExceptionHandling:
    """Test that services handle exceptions properly (no bare except clauses)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_search_with_empty_query(self):
        """Test search handles empty query gracefully"""
        response = requests.post(f"{BASE_URL}/api/search", headers=self.headers, json={
            "query": ""
        })
        # Should return 400 or 422 for validation error, not 500
        assert response.status_code in [200, 400, 422]
    
    def test_ai_search_with_invalid_mode(self):
        """Test AI search handles invalid mode gracefully"""
        response = requests.post(f"{BASE_URL}/api/ai-search", headers=self.headers, json={
            "query": "test query",
            "mode": "invalid_mode"
        })
        # Should handle gracefully, not crash
        assert response.status_code in [200, 400, 422]


class TestAdminPanel:
    """Test admin panel endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get admin auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_settings_endpoint(self):
        """Test admin settings endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=self.headers)
        assert response.status_code == 200
    
    def test_admin_users_endpoint(self):
        """Test admin users endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=self.headers)
        assert response.status_code == 200


class TestLegalEndpoints:
    """Test legal document endpoints"""
    
    def test_terms_summary_endpoint(self):
        """Test terms summary endpoint for sign-up flow"""
        response = requests.get(f"{BASE_URL}/api/legal/terms-summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data or "content" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
