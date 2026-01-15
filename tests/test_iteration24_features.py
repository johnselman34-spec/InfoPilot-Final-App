"""
InfoPilot Explorer - Iteration 24 Feature Tests
Tests for:
1. AI-Powered Protocol Suggestions (GET /api/ai/suggestions)
2. Poll Statistics API (GET /api/polls/user/statistics)
3. Admin Poll Statistics API (GET /api/polls/admin/statistics)
4. Admin Poll List API (GET /api/polls/admin/all)
5. Admin Poll Update API (PUT /api/polls/admin/{poll_id})
6. Admin Poll Delete API (DELETE /api/polls/admin/{poll_id})
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestAuthentication:
    """Authentication tests for getting tokens"""
    
    def test_admin_login(self):
        """Test admin user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    def test_regular_user_login_or_register(self):
        """Test regular user login or register"""
        # Try login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        
        # If login fails, try to register
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "username": "testuser"
        })
        if response.status_code in [200, 201]:
            return response.json().get("token")
        
        # If both fail, skip tests requiring regular user
        pytest.skip("Could not login or register test user")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Admin login failed - skipping admin tests")
    return response.json()["token"]


@pytest.fixture(scope="module")
def user_token():
    """Get regular user authentication token"""
    # Try login first
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["token"]
    
    # Try register
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "username": "testuser"
    })
    if response.status_code in [200, 201]:
        return response.json().get("token")
    
    pytest.skip("Could not get user token")


class TestAISuggestions:
    """Tests for AI-Powered Protocol Suggestions"""
    
    def test_ai_suggestions_requires_auth(self):
        """Test that AI suggestions endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/ai/suggestions")
        assert response.status_code == 401, "Should require authentication"
    
    def test_ai_suggestions_returns_data(self, admin_token):
        """Test AI suggestions endpoint returns proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/ai/suggestions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"AI suggestions failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "suggestions" in data, "Missing 'suggestions' field"
        assert "message" in data, "Missing 'message' field"
        assert "ai_powered" in data, "Missing 'ai_powered' field"
        
        # Suggestions should be a list (may be empty if no marketplace protocols)
        assert isinstance(data["suggestions"], list), "Suggestions should be a list"
    
    def test_ai_suggestions_with_limit(self, admin_token):
        """Test AI suggestions with custom limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/ai/suggestions?limit=3",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) <= 3, "Should respect limit parameter"
    
    def test_ai_suggestions_refresh(self, admin_token):
        """Test AI suggestions refresh endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai/suggestions/refresh",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"AI suggestions refresh failed: {response.text}"
        data = response.json()
        assert "suggestions" in data


class TestUserPollStatistics:
    """Tests for User Poll Statistics API"""
    
    def test_user_poll_stats_requires_auth(self):
        """Test that user poll statistics requires authentication"""
        response = requests.get(f"{BASE_URL}/api/polls/user/statistics")
        assert response.status_code == 401, "Should require authentication"
    
    def test_user_poll_stats_returns_data(self, admin_token):
        """Test user poll statistics returns proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/polls/user/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"User poll stats failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "polls_created" in data, "Missing 'polls_created' field"
        assert "active_polls" in data, "Missing 'active_polls' field"
        assert "total_votes_received" in data, "Missing 'total_votes_received' field"
        assert "polls_voted_on" in data, "Missing 'polls_voted_on' field"
        assert "avg_votes_per_poll" in data, "Missing 'avg_votes_per_poll' field"
        
        # Values should be numbers
        assert isinstance(data["polls_created"], int), "polls_created should be int"
        assert isinstance(data["active_polls"], int), "active_polls should be int"
        assert isinstance(data["total_votes_received"], int), "total_votes_received should be int"
        assert isinstance(data["polls_voted_on"], int), "polls_voted_on should be int"


class TestAdminPollStatistics:
    """Tests for Admin Poll Statistics API"""
    
    def test_admin_poll_stats_requires_auth(self):
        """Test that admin poll statistics requires authentication"""
        response = requests.get(f"{BASE_URL}/api/polls/admin/statistics")
        assert response.status_code == 401, "Should require authentication"
    
    def test_admin_poll_stats_requires_admin(self, user_token):
        """Test that admin poll statistics requires admin role"""
        response = requests.get(
            f"{BASE_URL}/api/polls/admin/statistics",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        # Should be 403 Forbidden for non-admin users
        assert response.status_code == 403, f"Should require admin role, got {response.status_code}"
    
    def test_admin_poll_stats_returns_data(self, admin_token):
        """Test admin poll statistics returns proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/polls/admin/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Admin poll stats failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_polls" in data, "Missing 'total_polls' field"
        assert "active_polls" in data, "Missing 'active_polls' field"
        assert "closed_polls" in data, "Missing 'closed_polls' field"
        assert "expired_polls" in data, "Missing 'expired_polls' field"
        assert "total_votes" in data, "Missing 'total_votes' field"
        assert "polls_by_type" in data, "Missing 'polls_by_type' field"
        assert "most_active_polls" in data, "Missing 'most_active_polls' field"
        assert "polls_this_week" in data, "Missing 'polls_this_week' field"
        assert "avg_votes_per_poll" in data, "Missing 'avg_votes_per_poll' field"


class TestAdminPollList:
    """Tests for Admin Poll List API"""
    
    def test_admin_poll_list_requires_auth(self):
        """Test that admin poll list requires authentication"""
        response = requests.get(f"{BASE_URL}/api/polls/admin/all")
        assert response.status_code == 401, "Should require authentication"
    
    def test_admin_poll_list_requires_admin(self, user_token):
        """Test that admin poll list requires admin role"""
        response = requests.get(
            f"{BASE_URL}/api/polls/admin/all",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403, f"Should require admin role, got {response.status_code}"
    
    def test_admin_poll_list_returns_data(self, admin_token):
        """Test admin poll list returns proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/polls/admin/all",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Admin poll list failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "polls" in data, "Missing 'polls' field"
        assert "total" in data, "Missing 'total' field"
        assert "page" in data, "Missing 'page' field"
        assert "pages" in data, "Missing 'pages' field"
        
        # Polls should be a list
        assert isinstance(data["polls"], list), "Polls should be a list"
    
    def test_admin_poll_list_pagination(self, admin_token):
        """Test admin poll list pagination"""
        response = requests.get(
            f"{BASE_URL}/api/polls/admin/all?page=1&limit=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["polls"]) <= 5, "Should respect limit parameter"
    
    def test_admin_poll_list_status_filter(self, admin_token):
        """Test admin poll list with status filter"""
        for status in ['active', 'closed', 'expired']:
            response = requests.get(
                f"{BASE_URL}/api/polls/admin/all?status={status}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200, f"Status filter '{status}' failed: {response.text}"


class TestAdminPollManagement:
    """Tests for Admin Poll Update and Delete APIs"""
    
    @pytest.fixture
    def test_poll_id(self, admin_token):
        """Create a test poll for management tests"""
        # First, we need a parent entity (group, page, or usp)
        # For USP, we can use the admin's own user ID
        
        # Get admin user info
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code != 200:
            pytest.skip("Could not get admin user info")
        
        user_id = response.json().get("id")
        
        # Create a test poll
        response = requests.post(
            f"{BASE_URL}/api/polls?parent_type=usp&parent_id={user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "question": "TEST_POLL: What is your favorite feature?",
                "options": ["Option A", "Option B", "Option C"],
                "expires_in_hours": 24,
                "allow_multiple": False
            }
        )
        
        if response.status_code not in [200, 201]:
            pytest.skip(f"Could not create test poll: {response.text}")
        
        poll_id = response.json().get("id")
        yield poll_id
        
        # Cleanup - delete the test poll
        requests.delete(
            f"{BASE_URL}/api/polls/admin/{poll_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_admin_poll_update_requires_admin(self, user_token, test_poll_id):
        """Test that admin poll update requires admin role"""
        if not test_poll_id:
            pytest.skip("No test poll available")
        
        response = requests.put(
            f"{BASE_URL}/api/polls/admin/{test_poll_id}?is_active=false",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403, f"Should require admin role, got {response.status_code}"
    
    def test_admin_poll_update(self, admin_token, test_poll_id):
        """Test admin can update poll settings"""
        if not test_poll_id:
            pytest.skip("No test poll available")
        
        response = requests.put(
            f"{BASE_URL}/api/polls/admin/{test_poll_id}?question=Updated%20Question",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Admin poll update failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Update should succeed"
    
    def test_admin_poll_delete_requires_admin(self, user_token, test_poll_id):
        """Test that admin poll delete requires admin role"""
        if not test_poll_id:
            pytest.skip("No test poll available")
        
        response = requests.delete(
            f"{BASE_URL}/api/polls/admin/{test_poll_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403, f"Should require admin role, got {response.status_code}"


class TestExistingPollEndpoints:
    """Tests for existing poll endpoints to ensure they still work"""
    
    def test_get_poll_by_id(self, admin_token):
        """Test getting a poll by ID (if any exist)"""
        # First get list of polls
        response = requests.get(
            f"{BASE_URL}/api/polls/admin/all?limit=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code != 200:
            pytest.skip("Could not get poll list")
        
        polls = response.json().get("polls", [])
        if not polls:
            pytest.skip("No polls exist to test")
        
        poll_id = polls[0]["id"]
        
        # Get single poll
        response = requests.get(
            f"{BASE_URL}/api/polls/{poll_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Get poll failed: {response.text}"
        data = response.json()
        assert "question" in data
        assert "options" in data


class TestBookPromoBanner:
    """Tests for enhanced Book Promo Banner with urgency messaging"""
    
    def test_book_promo_endpoint(self):
        """Test book promo endpoint returns data"""
        response = requests.get(f"{BASE_URL}/api/book-promo")
        assert response.status_code == 200, f"Book promo failed: {response.text}"
        data = response.json()
        
        # Verify book promo data structure
        assert "title" in data, "Missing 'title' field"
        assert "author" in data, "Missing 'author' field"
        assert "amazon_url" in data, "Missing 'amazon_url' field"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
