"""
InfoPilot Explorer API Tests - Social Features (Iteration 7)
Tests for: 
- REACTIONS: Facebook-style reactions (like, love, haha, wow, sad, angry) on posts
- COMMENTS: Comments with nested replies on posts
- UPDATES: Updates section on Ultimate Search page
- GROUPS: Create group, create post, view posts with reactions/comments
- PAGES: Create page, create post, view posts with reactions/comments
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://explorer-app-3.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"

# Reaction types
REACTION_TYPES = ["like", "love", "haha", "wow", "sad", "angry"]


class TestAuthentication:
    """Authentication tests"""
    
    def test_login_with_admin_credentials(self):
        """Test login with john@infojet.com / password123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True


class TestGroupsWithReactionsAndComments:
    """Groups feature tests with reactions and comments"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_create_group(self, auth_token):
        """Test creating a group"""
        unique_name = f"TEST_Social_Group_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test group for social features",
                "privacy": "public"
            })
        assert response.status_code == 200, f"Create group failed: {response.text}"
        data = response.json()
        assert data["group"]["name"] == unique_name
        assert data["group"]["privacy"] == "public"
        return data["group"]["id"]
    
    def test_create_post_in_group(self, auth_token):
        """Test creating a post in a group"""
        # First create a group
        unique_name = f"TEST_Post_Group_{uuid.uuid4().hex[:6]}"
        group_response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test group for posts",
                "privacy": "public"
            })
        group_id = group_response.json()["group"]["id"]
        
        # Create a post in the group
        post_content = f"Test post content {uuid.uuid4().hex[:6]}"
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "content": post_content
            })
        assert post_response.status_code == 200, f"Create post failed: {post_response.text}"
        data = post_response.json()
        assert data["post"]["content"] == post_content
        return group_id, data["post"]["id"]
    
    def test_add_reaction_to_group_post(self, auth_token):
        """Test adding reactions to a group post"""
        # Create group and post
        unique_name = f"TEST_Reaction_Group_{uuid.uuid4().hex[:6]}"
        group_response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test group for reactions",
                "privacy": "public"
            })
        group_id = group_response.json()["group"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Test post for reactions"})
        post_id = post_response.json()["post"]["id"]
        
        # Add a "like" reaction
        reaction_response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/reactions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"reaction_type": "like"})
        assert reaction_response.status_code == 200, f"Add reaction failed: {reaction_response.text}"
        data = reaction_response.json()
        assert data["user_reaction"] == "like"
        assert "reaction_counts" in data
    
    def test_add_all_reaction_types(self, auth_token):
        """Test adding all 6 reaction types (like, love, haha, wow, sad, angry)"""
        # Create group and post
        unique_name = f"TEST_AllReactions_Group_{uuid.uuid4().hex[:6]}"
        group_response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test group for all reactions",
                "privacy": "public"
            })
        group_id = group_response.json()["group"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Test post for all reactions"})
        post_id = post_response.json()["post"]["id"]
        
        # Test each reaction type
        for reaction_type in REACTION_TYPES:
            reaction_response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/reactions",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={"reaction_type": reaction_type})
            assert reaction_response.status_code == 200, f"Add {reaction_type} reaction failed: {reaction_response.text}"
            data = reaction_response.json()
            assert data["user_reaction"] == reaction_type, f"Expected {reaction_type}, got {data['user_reaction']}"
    
    def test_add_comment_to_group_post(self, auth_token):
        """Test adding a comment to a group post"""
        # Create group and post
        unique_name = f"TEST_Comment_Group_{uuid.uuid4().hex[:6]}"
        group_response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test group for comments",
                "privacy": "public"
            })
        group_id = group_response.json()["group"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Test post for comments"})
        post_id = post_response.json()["post"]["id"]
        
        # Add a comment
        comment_content = f"Test comment {uuid.uuid4().hex[:6]}"
        comment_response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": comment_content})
        assert comment_response.status_code == 200, f"Add comment failed: {comment_response.text}"
        data = comment_response.json()
        assert data["comment"]["content"] == comment_content
    
    def test_add_reply_to_comment(self, auth_token):
        """Test adding a reply to a comment (nested comments)"""
        # Create group and post
        unique_name = f"TEST_Reply_Group_{uuid.uuid4().hex[:6]}"
        group_response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test group for replies",
                "privacy": "public"
            })
        group_id = group_response.json()["group"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Test post for replies"})
        post_id = post_response.json()["post"]["id"]
        
        # Add a parent comment
        parent_comment_response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Parent comment"})
        parent_comment_id = parent_comment_response.json()["comment"]["id"]
        
        # Add a reply to the parent comment
        reply_content = f"Reply to parent {uuid.uuid4().hex[:6]}"
        reply_response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": reply_content, "parent_id": parent_comment_id})
        assert reply_response.status_code == 200, f"Add reply failed: {reply_response.text}"
        data = reply_response.json()
        assert data["comment"]["content"] == reply_content
        assert data["comment"]["parent_id"] == parent_comment_id
    
    def test_get_comments_with_nested_structure(self, auth_token):
        """Test getting comments returns nested structure"""
        # Create group and post
        unique_name = f"TEST_Nested_Group_{uuid.uuid4().hex[:6]}"
        group_response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test group for nested comments",
                "privacy": "public"
            })
        group_id = group_response.json()["group"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Test post for nested comments"})
        post_id = post_response.json()["post"]["id"]
        
        # Add parent comment
        parent_response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Parent comment"})
        parent_id = parent_response.json()["comment"]["id"]
        
        # Add reply
        requests.post(f"{BASE_URL}/api/posts/group/{post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Reply comment", "parent_id": parent_id})
        
        # Get comments
        get_response = requests.get(f"{BASE_URL}/api/posts/group/{post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert get_response.status_code == 200, f"Get comments failed: {get_response.text}"
        data = get_response.json()
        assert "comments" in data
        assert "total_count" in data
        assert data["total_count"] >= 2


class TestPagesWithReactionsAndComments:
    """Pages feature tests with reactions and comments"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_create_page(self, auth_token):
        """Test creating a page"""
        unique_name = f"TEST_Social_Page_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test page for social features",
                "category": "Business"
            })
        assert response.status_code == 200, f"Create page failed: {response.text}"
        data = response.json()
        assert data["page"]["name"] == unique_name
        assert data["page"]["category"] == "Business"
    
    def test_create_post_on_page(self, auth_token):
        """Test creating a post on a page"""
        # First create a page
        unique_name = f"TEST_Post_Page_{uuid.uuid4().hex[:6]}"
        page_response = requests.post(f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test page for posts",
                "category": "Community"
            })
        page_id = page_response.json()["page"]["id"]
        
        # Create a post on the page
        post_content = f"Test page post content {uuid.uuid4().hex[:6]}"
        post_response = requests.post(f"{BASE_URL}/api/pages/{page_id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "content": post_content
            })
        assert post_response.status_code == 200, f"Create post failed: {post_response.text}"
        data = post_response.json()
        assert data["post"]["content"] == post_content
    
    def test_add_reaction_to_page_post(self, auth_token):
        """Test adding reactions to a page post"""
        # Create page and post
        unique_name = f"TEST_PageReaction_{uuid.uuid4().hex[:6]}"
        page_response = requests.post(f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test page for reactions",
                "category": "Entertainment"
            })
        page_id = page_response.json()["page"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/pages/{page_id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Test page post for reactions"})
        post_id = post_response.json()["post"]["id"]
        
        # Add a "love" reaction
        reaction_response = requests.post(f"{BASE_URL}/api/posts/page/{post_id}/reactions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"reaction_type": "love"})
        assert reaction_response.status_code == 200, f"Add reaction failed: {reaction_response.text}"
        data = reaction_response.json()
        assert data["user_reaction"] == "love"
    
    def test_add_comment_to_page_post(self, auth_token):
        """Test adding a comment to a page post"""
        # Create page and post
        unique_name = f"TEST_PageComment_{uuid.uuid4().hex[:6]}"
        page_response = requests.post(f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test page for comments",
                "category": "General"
            })
        page_id = page_response.json()["page"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/pages/{page_id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Test page post for comments"})
        post_id = post_response.json()["post"]["id"]
        
        # Add a comment
        comment_content = f"Test page comment {uuid.uuid4().hex[:6]}"
        comment_response = requests.post(f"{BASE_URL}/api/posts/page/{post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": comment_content})
        assert comment_response.status_code == 200, f"Add comment failed: {comment_response.text}"
        data = comment_response.json()
        assert data["comment"]["content"] == comment_content


class TestUpdatesSection:
    """Updates section tests (Ultimate Search page)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_updates(self, auth_token):
        """Test getting updates from Ultimate Search page"""
        response = requests.get(f"{BASE_URL}/api/updates",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200, f"Get updates failed: {response.text}"
        data = response.json()
        assert "updates" in data
    
    def test_post_update(self, auth_token):
        """Test posting an update on Ultimate Search page"""
        update_content = f"Test update {uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/updates",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": update_content})
        assert response.status_code == 200, f"Post update failed: {response.text}"
        data = response.json()
        assert data["update"]["content"] == update_content
        return data["update"]["id"]
    
    def test_add_reaction_to_update(self, auth_token):
        """Test adding a reaction to an update"""
        # Create an update
        update_content = f"Test update for reaction {uuid.uuid4().hex[:6]}"
        update_response = requests.post(f"{BASE_URL}/api/updates",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": update_content})
        update_id = update_response.json()["update"]["id"]
        
        # Add a "haha" reaction
        reaction_response = requests.post(f"{BASE_URL}/api/posts/update/{update_id}/reactions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"reaction_type": "haha"})
        assert reaction_response.status_code == 200, f"Add reaction failed: {reaction_response.text}"
        data = reaction_response.json()
        assert data["user_reaction"] == "haha"
    
    def test_add_comment_to_update(self, auth_token):
        """Test adding a comment to an update"""
        # Create an update
        update_content = f"Test update for comment {uuid.uuid4().hex[:6]}"
        update_response = requests.post(f"{BASE_URL}/api/updates",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": update_content})
        update_id = update_response.json()["update"]["id"]
        
        # Add a comment
        comment_content = f"Test update comment {uuid.uuid4().hex[:6]}"
        comment_response = requests.post(f"{BASE_URL}/api/posts/update/{update_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": comment_content})
        assert comment_response.status_code == 200, f"Add comment failed: {comment_response.text}"
        data = comment_response.json()
        assert data["comment"]["content"] == comment_content
    
    def test_delete_update(self, auth_token):
        """Test deleting an update"""
        # Create an update
        update_content = f"Test update to delete {uuid.uuid4().hex[:6]}"
        update_response = requests.post(f"{BASE_URL}/api/updates",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": update_content})
        update_id = update_response.json()["update"]["id"]
        
        # Delete the update
        delete_response = requests.delete(f"{BASE_URL}/api/updates/{update_id}",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert delete_response.status_code == 200, f"Delete update failed: {delete_response.text}"


class TestUltimateSearchPageRename:
    """Ultimate Search page rename functionality"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_page_settings(self, auth_token):
        """Test getting Ultimate Search page settings"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/page-settings",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200, f"Get settings failed: {response.text}"
        data = response.json()
        assert "page_name" in data
    
    def test_rename_page(self, auth_token):
        """Test renaming Ultimate Search page"""
        new_name = f"My Custom Search {uuid.uuid4().hex[:4]}"
        response = requests.put(f"{BASE_URL}/api/ultimate-search/page-settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"page_name": new_name})
        assert response.status_code == 200, f"Rename page failed: {response.text}"
        data = response.json()
        assert data["settings"]["page_name"] == new_name


class TestReactionRemoval:
    """Test removing reactions"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_remove_reaction(self, auth_token):
        """Test removing a reaction from a post"""
        # Create group and post
        unique_name = f"TEST_RemoveReaction_{uuid.uuid4().hex[:6]}"
        group_response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test group for removing reactions",
                "privacy": "public"
            })
        group_id = group_response.json()["group"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Test post for removing reactions"})
        post_id = post_response.json()["post"]["id"]
        
        # Add a reaction
        requests.post(f"{BASE_URL}/api/posts/group/{post_id}/reactions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"reaction_type": "like"})
        
        # Remove the reaction
        remove_response = requests.delete(f"{BASE_URL}/api/posts/group/{post_id}/reactions",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert remove_response.status_code == 200, f"Remove reaction failed: {remove_response.text}"
        data = remove_response.json()
        assert data["message"] == "Reaction removed"


class TestCommentDeletion:
    """Test deleting comments"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_delete_comment(self, auth_token):
        """Test deleting a comment"""
        # Create group and post
        unique_name = f"TEST_DeleteComment_{uuid.uuid4().hex[:6]}"
        group_response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test group for deleting comments",
                "privacy": "public"
            })
        group_id = group_response.json()["group"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Test post for deleting comments"})
        post_id = post_response.json()["post"]["id"]
        
        # Add a comment
        comment_response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Comment to delete"})
        comment_id = comment_response.json()["comment"]["id"]
        
        # Delete the comment
        delete_response = requests.delete(f"{BASE_URL}/api/comments/{comment_id}",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert delete_response.status_code == 200, f"Delete comment failed: {delete_response.text}"


class TestInvalidReactionType:
    """Test invalid reaction type handling"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_invalid_reaction_type_rejected(self, auth_token):
        """Test that invalid reaction types are rejected"""
        # Create group and post
        unique_name = f"TEST_InvalidReaction_{uuid.uuid4().hex[:6]}"
        group_response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test group for invalid reactions",
                "privacy": "public"
            })
        group_id = group_response.json()["group"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Test post for invalid reactions"})
        post_id = post_response.json()["post"]["id"]
        
        # Try to add an invalid reaction type
        reaction_response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/reactions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"reaction_type": "invalid_type"})
        assert reaction_response.status_code == 400, f"Expected 400, got {reaction_response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
