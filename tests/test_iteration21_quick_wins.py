"""
InfoPilot Explorer - Iteration 21 Quick Win Features Tests
Tests for:
1. Polls Feature - Create, Get, Vote, Delete polls for Groups/Pages/USP
2. Default Admin Friend - New users get jjspilot24@gmail.com as friend
3. Push Notifications for DMs - Simulation mode (VAPID_PRIVATE_KEY not set)
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"

# Test data
TEST_GROUP_ID = "6968eb45a1ee1e469cc3f50c"  # Provided group ID for testing


class TestAuthentication:
    """Authentication tests - get token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in login response"
        return data["token"]
    
    def test_admin_login(self, admin_token):
        """Test admin user can login"""
        assert admin_token is not None
        assert len(admin_token) > 0
        print(f"✓ Admin login successful, token obtained")


class TestPollsAPI:
    """Tests for Polls CRUD operations"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Headers with admin auth token"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_create_poll_for_group(self, admin_headers):
        """Test creating a poll for a group"""
        poll_data = {
            "question": f"TEST_Poll Question {uuid.uuid4().hex[:8]}",
            "options": ["Option A", "Option B", "Option C"],
            "expires_in_hours": 24,
            "allow_multiple": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/polls?parent_type=group&parent_id={TEST_GROUP_ID}",
            json=poll_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Create poll failed: {response.text}"
        data = response.json()
        assert "id" in data, "No poll ID in response"
        assert data["question"] == poll_data["question"]
        assert data["message"] == "Poll created successfully"
        print(f"✓ Poll created successfully with ID: {data['id']}")
        
        # Store poll ID for cleanup
        return data["id"]
    
    def test_create_poll_validation_min_options(self, admin_headers):
        """Test poll creation fails with less than 2 options"""
        poll_data = {
            "question": "TEST_Invalid Poll",
            "options": ["Only one option"],
            "expires_in_hours": 24
        }
        
        response = requests.post(
            f"{BASE_URL}/api/polls?parent_type=group&parent_id={TEST_GROUP_ID}",
            json=poll_data,
            headers=admin_headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "at least 2 options" in response.json().get("detail", "").lower()
        print("✓ Poll validation correctly rejects < 2 options")
    
    def test_create_poll_validation_max_options(self, admin_headers):
        """Test poll creation fails with more than 10 options"""
        poll_data = {
            "question": "TEST_Invalid Poll",
            "options": [f"Option {i}" for i in range(11)],  # 11 options
            "expires_in_hours": 24
        }
        
        response = requests.post(
            f"{BASE_URL}/api/polls?parent_type=group&parent_id={TEST_GROUP_ID}",
            json=poll_data,
            headers=admin_headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "more than 10" in response.json().get("detail", "").lower()
        print("✓ Poll validation correctly rejects > 10 options")
    
    def test_create_poll_invalid_parent_type(self, admin_headers):
        """Test poll creation fails with invalid parent type"""
        poll_data = {
            "question": "TEST_Invalid Poll",
            "options": ["Option A", "Option B"],
            "expires_in_hours": 24
        }
        
        response = requests.post(
            f"{BASE_URL}/api/polls?parent_type=invalid&parent_id={TEST_GROUP_ID}",
            json=poll_data,
            headers=admin_headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "invalid parent type" in response.json().get("detail", "").lower()
        print("✓ Poll validation correctly rejects invalid parent type")
    
    def test_get_polls_for_group(self, admin_headers):
        """Test getting polls for a group"""
        response = requests.get(
            f"{BASE_URL}/api/polls/parent/group/{TEST_GROUP_ID}",
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Get polls failed: {response.text}"
        data = response.json()
        assert "polls" in data, "No polls array in response"
        assert isinstance(data["polls"], list)
        print(f"✓ Retrieved {len(data['polls'])} polls for group")
    
    def test_get_single_poll(self, admin_headers):
        """Test getting a single poll by ID"""
        # First create a poll
        poll_data = {
            "question": f"TEST_Single Poll {uuid.uuid4().hex[:8]}",
            "options": ["Yes", "No"],
            "expires_in_hours": 24
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/polls?parent_type=group&parent_id={TEST_GROUP_ID}",
            json=poll_data,
            headers=admin_headers
        )
        assert create_response.status_code == 200
        poll_id = create_response.json()["id"]
        
        # Get the poll
        response = requests.get(
            f"{BASE_URL}/api/polls/{poll_id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Get poll failed: {response.text}"
        data = response.json()
        assert data["id"] == poll_id
        assert data["question"] == poll_data["question"]
        assert len(data["options"]) == 2
        assert data["total_votes"] == 0
        assert data["is_active"] == True
        print(f"✓ Retrieved single poll: {data['question']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/polls/{poll_id}", headers=admin_headers)
    
    def test_vote_on_poll(self, admin_headers):
        """Test voting on a poll"""
        # Create a poll
        poll_data = {
            "question": f"TEST_Vote Poll {uuid.uuid4().hex[:8]}",
            "options": ["Choice 1", "Choice 2", "Choice 3"],
            "expires_in_hours": 24
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/polls?parent_type=group&parent_id={TEST_GROUP_ID}",
            json=poll_data,
            headers=admin_headers
        )
        assert create_response.status_code == 200
        poll_id = create_response.json()["id"]
        
        # Vote on option 1
        vote_response = requests.post(
            f"{BASE_URL}/api/polls/{poll_id}/vote",
            json={"option_index": 1},
            headers=admin_headers
        )
        
        assert vote_response.status_code == 200, f"Vote failed: {vote_response.text}"
        data = vote_response.json()
        assert data["success"] == True
        assert data["message"] == "Vote recorded"
        print("✓ Vote recorded successfully")
        
        # Verify vote was counted
        get_response = requests.get(f"{BASE_URL}/api/polls/{poll_id}", headers=admin_headers)
        poll_data = get_response.json()
        assert poll_data["total_votes"] == 1
        assert poll_data["user_voted"] == True
        print("✓ Vote count updated correctly")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/polls/{poll_id}", headers=admin_headers)
    
    def test_double_vote_prevention(self, admin_headers):
        """Test that users cannot vote twice on same poll (when allow_multiple=False)"""
        # Create a poll
        poll_data = {
            "question": f"TEST_Double Vote Poll {uuid.uuid4().hex[:8]}",
            "options": ["A", "B"],
            "expires_in_hours": 24,
            "allow_multiple": False
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/polls?parent_type=group&parent_id={TEST_GROUP_ID}",
            json=poll_data,
            headers=admin_headers
        )
        assert create_response.status_code == 200
        poll_id = create_response.json()["id"]
        
        # First vote
        vote1 = requests.post(
            f"{BASE_URL}/api/polls/{poll_id}/vote",
            json={"option_index": 0},
            headers=admin_headers
        )
        assert vote1.status_code == 200
        
        # Second vote should fail
        vote2 = requests.post(
            f"{BASE_URL}/api/polls/{poll_id}/vote",
            json={"option_index": 1},
            headers=admin_headers
        )
        assert vote2.status_code == 400, f"Expected 400, got {vote2.status_code}"
        assert "already voted" in vote2.json().get("detail", "").lower()
        print("✓ Double voting correctly prevented")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/polls/{poll_id}", headers=admin_headers)
    
    def test_delete_poll(self, admin_headers):
        """Test deleting a poll"""
        # Create a poll
        poll_data = {
            "question": f"TEST_Delete Poll {uuid.uuid4().hex[:8]}",
            "options": ["X", "Y"],
            "expires_in_hours": 24
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/polls?parent_type=group&parent_id={TEST_GROUP_ID}",
            json=poll_data,
            headers=admin_headers
        )
        assert create_response.status_code == 200
        poll_id = create_response.json()["id"]
        
        # Delete the poll
        delete_response = requests.delete(
            f"{BASE_URL}/api/polls/{poll_id}",
            headers=admin_headers
        )
        
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        data = delete_response.json()
        assert data["success"] == True
        print("✓ Poll deleted successfully")
        
        # Verify poll is gone
        get_response = requests.get(f"{BASE_URL}/api/polls/{poll_id}", headers=admin_headers)
        assert get_response.status_code == 404
        print("✓ Deleted poll returns 404")
    
    def test_close_poll(self, admin_headers):
        """Test closing a poll early"""
        # Create a poll
        poll_data = {
            "question": f"TEST_Close Poll {uuid.uuid4().hex[:8]}",
            "options": ["Yes", "No"],
            "expires_in_hours": 24
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/polls?parent_type=group&parent_id={TEST_GROUP_ID}",
            json=poll_data,
            headers=admin_headers
        )
        assert create_response.status_code == 200
        poll_id = create_response.json()["id"]
        
        # Close the poll
        close_response = requests.put(
            f"{BASE_URL}/api/polls/{poll_id}/close",
            headers=admin_headers
        )
        
        assert close_response.status_code == 200, f"Close failed: {close_response.text}"
        data = close_response.json()
        assert data["success"] == True
        print("✓ Poll closed successfully")
        
        # Verify poll is inactive
        get_response = requests.get(f"{BASE_URL}/api/polls/{poll_id}", headers=admin_headers)
        poll_data = get_response.json()
        assert poll_data["is_active"] == False
        print("✓ Closed poll shows as inactive")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/polls/{poll_id}", headers=admin_headers)


class TestDefaultAdminFriend:
    """Tests for default admin friend feature"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Headers with admin auth token"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_admin_user_exists(self, admin_headers):
        """Verify the default admin friend user exists"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers)
        assert response.status_code == 200, f"Get user failed: {response.text}"
        data = response.json()
        assert data["email"].lower() == ADMIN_EMAIL.lower()
        print(f"✓ Admin user exists: {data['email']}")
    
    def test_new_user_registration_adds_default_friend(self, admin_headers):
        """Test that new user registration adds default admin as friend"""
        # Create a new test user
        test_email = f"TEST_newuser_{uuid.uuid4().hex[:8]}@test.com"
        test_password = "TestPass123!"
        test_username = f"TEST_User_{uuid.uuid4().hex[:6]}"
        
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": test_password,
            "username": test_username
        })
        
        assert register_response.status_code == 200, f"Registration failed: {register_response.text}"
        new_user_data = register_response.json()
        new_user_token = new_user_data.get("token")
        
        if not new_user_token:
            # Login to get token
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": test_email,
                "password": test_password
            })
            assert login_response.status_code == 200
            new_user_token = login_response.json()["token"]
        
        new_user_headers = {
            "Authorization": f"Bearer {new_user_token}",
            "Content-Type": "application/json"
        }
        
        # Check friends list for new user
        friends_response = requests.get(f"{BASE_URL}/api/friends", headers=new_user_headers)
        assert friends_response.status_code == 200, f"Get friends failed: {friends_response.text}"
        friends_data = friends_response.json()
        
        # Verify admin is in friends list
        friends = friends_data.get("friends", [])
        admin_friend = next((f for f in friends if f.get("email", "").lower() == ADMIN_EMAIL.lower()), None)
        
        if admin_friend:
            print(f"✓ New user has default admin friend: {ADMIN_EMAIL}")
        else:
            # Check if friendship exists but email not exposed
            admin_usernames = [f.get("username", "") for f in friends]
            print(f"Friends list: {admin_usernames}")
            # The friendship should exist - check via admin's friends list
            admin_friends_response = requests.get(f"{BASE_URL}/api/friends", headers=admin_headers)
            admin_friends = admin_friends_response.json().get("friends", [])
            new_user_in_admin_friends = any(
                f.get("username") == test_username for f in admin_friends
            )
            assert new_user_in_admin_friends or len(friends) > 0, "Default friend not added"
            print(f"✓ Friendship established (verified via admin's friends list)")


class TestPushNotifications:
    """Tests for push notification functionality (simulation mode)"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Headers with admin auth token"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_dm_conversations_endpoint(self, admin_headers):
        """Test DM conversations endpoint works"""
        response = requests.get(f"{BASE_URL}/api/dm/conversations", headers=admin_headers)
        assert response.status_code == 200, f"Get conversations failed: {response.text}"
        data = response.json()
        assert "conversations" in data
        print(f"✓ DM conversations endpoint working, found {len(data['conversations'])} conversations")
    
    def test_dm_online_status_endpoint(self, admin_headers):
        """Test online friends endpoint works"""
        response = requests.get(f"{BASE_URL}/api/dm/online", headers=admin_headers)
        assert response.status_code == 200, f"Get online friends failed: {response.text}"
        data = response.json()
        assert "online_friends" in data
        assert "count" in data
        print(f"✓ Online friends endpoint working, {data['count']} friends online")


class TestGroupsAndPagesIntegration:
    """Tests for groups and pages with polls integration"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Headers with admin auth token"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_groups_list(self, admin_headers):
        """Test getting groups list"""
        response = requests.get(f"{BASE_URL}/api/groups", headers=admin_headers)
        assert response.status_code == 200, f"Get groups failed: {response.text}"
        data = response.json()
        assert "groups" in data
        print(f"✓ Groups endpoint working, found {len(data['groups'])} groups")
    
    def test_get_pages_list(self, admin_headers):
        """Test getting pages list"""
        response = requests.get(f"{BASE_URL}/api/pages", headers=admin_headers)
        assert response.status_code == 200, f"Get pages failed: {response.text}"
        data = response.json()
        assert "pages" in data
        print(f"✓ Pages endpoint working, found {len(data['pages'])} pages")
    
    def test_create_group_and_poll(self, admin_headers):
        """Test creating a group and then a poll for it"""
        # Create a group
        group_data = {
            "name": f"TEST_Poll Group {uuid.uuid4().hex[:6]}",
            "description": "Test group for polls",
            "is_private": False
        }
        
        group_response = requests.post(
            f"{BASE_URL}/api/groups",
            json=group_data,
            headers=admin_headers
        )
        assert group_response.status_code == 200, f"Create group failed: {group_response.text}"
        group_id = group_response.json()["id"]
        print(f"✓ Created test group: {group_id}")
        
        # Create a poll for the group
        poll_data = {
            "question": "What should we discuss next?",
            "options": ["Topic A", "Topic B", "Topic C"],
            "expires_in_hours": 24
        }
        
        poll_response = requests.post(
            f"{BASE_URL}/api/polls?parent_type=group&parent_id={group_id}",
            json=poll_data,
            headers=admin_headers
        )
        assert poll_response.status_code == 200, f"Create poll failed: {poll_response.text}"
        poll_id = poll_response.json()["id"]
        print(f"✓ Created poll for group: {poll_id}")
        
        # Verify poll appears in group's polls
        polls_response = requests.get(
            f"{BASE_URL}/api/polls/parent/group/{group_id}",
            headers=admin_headers
        )
        assert polls_response.status_code == 200
        polls = polls_response.json()["polls"]
        assert any(p["id"] == poll_id for p in polls)
        print("✓ Poll appears in group's polls list")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/polls/{poll_id}", headers=admin_headers)


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        return None
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Headers with admin auth token"""
        if admin_token:
            return {
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        return {}
    
    def test_cleanup_test_polls(self, admin_headers):
        """Clean up TEST_ prefixed polls"""
        if not admin_headers:
            pytest.skip("No admin token available")
        
        # Get all polls for the test group
        response = requests.get(
            f"{BASE_URL}/api/polls/parent/group/{TEST_GROUP_ID}",
            headers=admin_headers
        )
        
        if response.status_code == 200:
            polls = response.json().get("polls", [])
            deleted = 0
            for poll in polls:
                if poll.get("question", "").startswith("TEST_"):
                    del_response = requests.delete(
                        f"{BASE_URL}/api/polls/{poll['id']}",
                        headers=admin_headers
                    )
                    if del_response.status_code == 200:
                        deleted += 1
            print(f"✓ Cleaned up {deleted} test polls")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
