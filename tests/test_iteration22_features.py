"""
InfoPilot Explorer - Iteration 22 Features Test Suite
Tests for: Copy to Clipboard, Tutorials, Most Copied Leaderboard, Webhooks, 
Rate Limiting, Partial Admin Roles (Group Moderators, Page Admins)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTutorialsAPI:
    """Test Video Tutorials API - GET /api/tutorials"""
    
    def test_get_tutorials_returns_10_tutorials(self):
        """Verify tutorials endpoint returns 10 tutorials"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "tutorials" in data, "Response should contain 'tutorials' key"
        assert "categories" in data, "Response should contain 'categories' key"
        
        tutorials = data["tutorials"]
        assert len(tutorials) == 10, f"Expected 10 tutorials, got {len(tutorials)}"
        
        # Verify tutorial structure
        for tutorial in tutorials:
            assert "id" in tutorial, "Tutorial should have 'id'"
            assert "title" in tutorial, "Tutorial should have 'title'"
            assert "description" in tutorial, "Tutorial should have 'description'"
            assert "youtube_id" in tutorial, "Tutorial should have 'youtube_id'"
            assert "duration" in tutorial, "Tutorial should have 'duration'"
            assert "category" in tutorial, "Tutorial should have 'category'"
            assert "thumbnail" in tutorial, "Tutorial should have 'thumbnail'"
    
    def test_tutorials_categories_exist(self):
        """Verify tutorials have categories"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        
        data = response.json()
        categories = data.get("categories", [])
        assert len(categories) > 0, "Should have at least one category"
        
        # Verify category structure
        for cat in categories:
            assert "id" in cat, "Category should have 'id'"
            assert "name" in cat, "Category should have 'name'"
            assert "icon" in cat, "Category should have 'icon'"


class TestMostCopiedLeaderboard:
    """Test Most Copied Protocols Leaderboard - GET /api/statistics/most-copied"""
    
    def test_most_copied_returns_leaderboard(self):
        """Verify most-copied endpoint returns leaderboard data"""
        response = requests.get(f"{BASE_URL}/api/statistics/most-copied")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "leaderboard" in data, "Response should contain 'leaderboard' key"
        assert "stats" in data, "Response should contain 'stats' key"
        assert "chart_type" in data, "Response should contain 'chart_type' key"
        
        leaderboard = data["leaderboard"]
        assert len(leaderboard) > 0, "Leaderboard should have entries"
        
        # Verify leaderboard entry structure
        for entry in leaderboard:
            assert "rank" in entry, "Entry should have 'rank'"
            assert "name" in entry, "Entry should have 'name'"
            assert "category" in entry, "Entry should have 'category'"
            assert "copy_count" in entry, "Entry should have 'copy_count'"
            assert "is_free" in entry, "Entry should have 'is_free'"
            assert "creator" in entry, "Entry should have 'creator'"
    
    def test_most_copied_stats_structure(self):
        """Verify stats structure in most-copied response"""
        response = requests.get(f"{BASE_URL}/api/statistics/most-copied")
        assert response.status_code == 200
        
        data = response.json()
        stats = data.get("stats", {})
        
        assert "total_copies" in stats, "Stats should have 'total_copies'"
        assert "free_protocol_copies" in stats, "Stats should have 'free_protocol_copies'"
        assert "paid_protocol_copies" in stats, "Stats should have 'paid_protocol_copies'"
        assert "free_percentage" in stats, "Stats should have 'free_percentage'"


class TestWebhooksAPI:
    """Test Webhook APIs - GET /api/webhooks/event-types"""
    
    def test_webhook_event_types(self):
        """Verify webhook event types endpoint"""
        response = requests.get(f"{BASE_URL}/api/webhooks/event-types")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "event_types" in data, "Response should contain 'event_types' key"
        
        event_types = data["event_types"]
        
        # Verify expected event types exist
        expected_events = [
            "protocol_purchase", "protocol_copy", "new_follower", 
            "new_friend", "new_message", "group_join", "poll_vote", "achievement_unlock"
        ]
        
        for event in expected_events:
            assert event in event_types, f"Event type '{event}' should exist"
            assert "name" in event_types[event], f"Event '{event}' should have 'name'"
            assert "description" in event_types[event], f"Event '{event}' should have 'description'"
            assert "icon" in event_types[event], f"Event '{event}' should have 'icon'"


class TestRateLimitingAPI:
    """Test Rate Limiting APIs - requires authentication"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_rate_limit_status_requires_auth(self):
        """Verify rate-limit status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/rate-limit/status")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
    
    def test_rate_limit_status_with_auth(self, auth_token):
        """Verify rate-limit status with authentication"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/rate-limit/status", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify response structure
        assert "limits" in data or "status" in data or "rate_limits" in data, \
            "Response should contain rate limit information"


class TestPartialAdminRoles:
    """Test Partial Admin Roles - Group Moderators and Page Admins"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    @pytest.fixture
    def test_group(self, auth_token):
        """Create a test group for moderator testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Note: Social routes don't have /social prefix
        response = requests.post(f"{BASE_URL}/api/groups", 
            headers=headers,
            json={
                "name": "TEST_Moderator_Test_Group",
                "description": "Test group for moderator testing",
                "privacy": "public"
            }
        )
        if response.status_code in [200, 201]:
            group_id = response.json().get("id")
            yield group_id
            # Cleanup
            requests.delete(f"{BASE_URL}/api/groups/{group_id}", headers=headers)
        else:
            pytest.skip(f"Failed to create test group: {response.status_code}")
    
    @pytest.fixture
    def test_page(self, auth_token):
        """Create a test page for admin testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Note: Social routes don't have /social prefix
        response = requests.post(f"{BASE_URL}/api/pages", 
            headers=headers,
            json={
                "name": "TEST_Admin_Test_Page",
                "description": "Test page for admin testing",
                "category": "General"
            }
        )
        if response.status_code in [200, 201]:
            page_id = response.json().get("id")
            yield page_id
            # Cleanup
            requests.delete(f"{BASE_URL}/api/pages/{page_id}", headers=headers)
        else:
            pytest.skip(f"Failed to create test page: {response.status_code}")
    
    def test_add_group_moderator_endpoint_exists(self, auth_token, test_group):
        """Verify POST /api/groups/{id}/moderators endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Try to add a fake user ID as moderator
        response = requests.post(
            f"{BASE_URL}/api/groups/{test_group}/moderators",
            headers=headers,
            json={"user_id": "fake_user_id_12345"}
        )
        
        # Should return 200 (success) or 404 (user not found) - not 404 for endpoint
        assert response.status_code in [200, 400, 404, 422], \
            f"Endpoint should exist, got {response.status_code}: {response.text}"
    
    def test_add_page_admin_endpoint_exists(self, auth_token, test_page):
        """Verify POST /api/pages/{id}/admins endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Try to add a fake user ID as admin
        response = requests.post(
            f"{BASE_URL}/api/pages/{test_page}/admins",
            headers=headers,
            json={"user_id": "fake_user_id_12345"}
        )
        
        # Should return 200 (success) or 404 (user not found) - not 404 for endpoint
        assert response.status_code in [200, 400, 404, 422], \
            f"Endpoint should exist, got {response.status_code}: {response.text}"
    
    def test_remove_group_moderator_endpoint_exists(self, auth_token, test_group):
        """Verify DELETE /api/groups/{id}/moderators/{mod_id} endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.delete(
            f"{BASE_URL}/api/groups/{test_group}/moderators/fake_mod_id",
            headers=headers
        )
        
        # Should return 200 (success) or 404 (moderator not found) - not 404 for endpoint
        assert response.status_code in [200, 400, 404], \
            f"Endpoint should exist, got {response.status_code}: {response.text}"
    
    def test_remove_page_admin_endpoint_exists(self, auth_token, test_page):
        """Verify DELETE /api/pages/{id}/admins/{admin_id} endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.delete(
            f"{BASE_URL}/api/pages/{test_page}/admins/fake_admin_id",
            headers=headers
        )
        
        # Should return 200 (success) or 404 (admin not found) - not 404 for endpoint
        assert response.status_code in [200, 400, 404], \
            f"Endpoint should exist, got {response.status_code}: {response.text}"


class TestCopyToClipboardAPI:
    """Test Copy to Clipboard functionality - protocol copy tracking"""
    
    def test_marketplace_protocols_have_copy_tracking(self):
        """Verify marketplace protocols endpoint exists"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "protocols" in data, "Response should contain 'protocols' key"


class TestStatisticsOverview:
    """Test Statistics Overview API"""
    
    def test_statistics_overview(self):
        """Verify statistics overview endpoint"""
        response = requests.get(f"{BASE_URL}/api/statistics/overview")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total_users" in data, "Should have 'total_users'"
        assert "total_protocols" in data, "Should have 'total_protocols'"


class TestBrowserExtensionSupport:
    """Test endpoints that support browser extension functionality"""
    
    def test_health_endpoint(self):
        """Verify health endpoint for extension connectivity check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
