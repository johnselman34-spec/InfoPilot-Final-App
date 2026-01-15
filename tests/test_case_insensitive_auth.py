"""
Case-Insensitive Email Authentication Tests
Tests for: Google OAuth, Regular Login, Registration - all with case-insensitive email matching

Bug Fix Being Tested:
- Network Error when new Google OAuth users try to create categories due to case-sensitive email lookup
- Fix: MongoDB regex with $options: 'i' for case-insensitive matching in:
  1. /api/auth/google (Google OAuth)
  2. /api/auth/login (Regular login)
  3. /api/auth/register (Registration duplicate check)
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = "https://infoexplore.preview.emergentagent.com"

# Test credentials from main agent
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"
TEST_GOOGLE_EMAIL = "turbomentor33@gmail.com"
TEST_GOOGLE_ID = "test_google_id_123"
TEST_GOOGLE_NAME = "Test User"


class TestHealthCheck:
    """Verify API is running before auth tests"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")


class TestCaseInsensitiveLogin:
    """Test case-insensitive email matching for regular login"""
    
    def test_login_lowercase_email(self):
        """Test login with lowercase email (original case)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "john@infojet.com",
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == "john@infojet.com"
        print(f"✓ Login with lowercase email successful")
    
    def test_login_uppercase_email(self):
        """Test login with UPPERCASE email"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "JOHN@INFOJET.COM",
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login with uppercase failed: {response.text}"
        data = response.json()
        assert "token" in data
        # The returned email should be the original stored email
        assert data["user"]["email"].lower() == "john@infojet.com"
        print(f"✓ Login with UPPERCASE email successful - returned email: {data['user']['email']}")
    
    def test_login_mixed_case_email(self):
        """Test login with MixedCase email"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "John@InfoJet.Com",
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login with mixed case failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["email"].lower() == "john@infojet.com"
        print(f"✓ Login with MixedCase email successful - returned email: {data['user']['email']}")
    
    def test_login_random_case_email(self):
        """Test login with random case variations"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jOhN@iNfOjEt.CoM",
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login with random case failed: {response.text}"
        data = response.json()
        assert "token" in data
        print(f"✓ Login with random case email successful")
    
    def test_login_wrong_password_still_fails(self):
        """Verify wrong password still fails regardless of email case"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "JOHN@INFOJET.COM",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, "Should fail with wrong password"
        print(f"✓ Wrong password correctly rejected even with case-insensitive email")


class TestCaseInsensitiveGoogleAuth:
    """Test case-insensitive email matching for Google OAuth"""
    
    def test_google_auth_creates_new_user(self):
        """Test Google auth creates new user with unique email"""
        unique_email = f"test_google_{uuid.uuid4().hex[:8]}@gmail.com"
        unique_google_id = f"google_id_{uuid.uuid4().hex[:12]}"
        
        response = requests.post(f"{BASE_URL}/api/auth/google", json={
            "email": unique_email,
            "google_id": unique_google_id,
            "name": "Test Google User",
            "picture": "https://example.com/pic.jpg"
        })
        assert response.status_code == 200, f"Google auth failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == unique_email
        print(f"✓ Google auth created new user: {unique_email}")
        return data["token"], unique_email
    
    def test_google_auth_finds_existing_user_case_insensitive(self):
        """Test Google auth finds existing user with different email case"""
        # First create a user with lowercase email
        unique_suffix = uuid.uuid4().hex[:8]
        original_email = f"testuser_{unique_suffix}@gmail.com"
        google_id = f"google_id_{unique_suffix}"
        
        # Create user with lowercase email
        response1 = requests.post(f"{BASE_URL}/api/auth/google", json={
            "email": original_email,
            "google_id": google_id,
            "name": "Test User",
            "picture": None
        })
        assert response1.status_code == 200, f"First Google auth failed: {response1.text}"
        user_id_1 = response1.json()["user"]["id"]
        print(f"✓ Created user with email: {original_email}, ID: {user_id_1}")
        
        # Now try to auth with UPPERCASE email - should find the same user
        uppercase_email = original_email.upper()
        response2 = requests.post(f"{BASE_URL}/api/auth/google", json={
            "email": uppercase_email,
            "google_id": f"different_google_id_{unique_suffix}",  # Different google_id
            "name": "Test User",
            "picture": None
        })
        assert response2.status_code == 200, f"Second Google auth failed: {response2.text}"
        user_id_2 = response2.json()["user"]["id"]
        
        # Should be the SAME user (case-insensitive match)
        assert user_id_1 == user_id_2, f"Expected same user ID but got {user_id_1} vs {user_id_2}"
        print(f"✓ Google auth with UPPERCASE email found same user: {user_id_2}")
    
    def test_google_auth_mixed_case_email(self):
        """Test Google auth with mixed case email finds existing user"""
        unique_suffix = uuid.uuid4().hex[:8]
        original_email = f"mixedcase_{unique_suffix}@gmail.com"
        google_id = f"google_mixed_{unique_suffix}"
        
        # Create user
        response1 = requests.post(f"{BASE_URL}/api/auth/google", json={
            "email": original_email,
            "google_id": google_id,
            "name": "Mixed Case User",
            "picture": None
        })
        assert response1.status_code == 200
        user_id_1 = response1.json()["user"]["id"]
        
        # Auth with MixedCase email
        mixed_email = f"MixedCase_{unique_suffix}@Gmail.Com"
        response2 = requests.post(f"{BASE_URL}/api/auth/google", json={
            "email": mixed_email,
            "google_id": f"another_google_id_{unique_suffix}",
            "name": "Mixed Case User",
            "picture": None
        })
        assert response2.status_code == 200
        user_id_2 = response2.json()["user"]["id"]
        
        assert user_id_1 == user_id_2, "Should find same user with mixed case email"
        print(f"✓ Google auth with MixedCase email found same user")


class TestCaseInsensitiveRegistration:
    """Test case-insensitive email duplicate check during registration"""
    
    def test_register_new_user(self):
        """Test registering a new user"""
        unique_suffix = uuid.uuid4().hex[:8]
        email = f"newuser_{unique_suffix}@test.com"
        username = f"newuser_{unique_suffix}"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "username": username,
            "password": "testpass123"
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == email
        print(f"✓ Registered new user: {email}")
        return data["token"]
    
    def test_register_duplicate_email_lowercase(self):
        """Test that duplicate email (lowercase) is rejected"""
        unique_suffix = uuid.uuid4().hex[:8]
        email = f"duplicate_{unique_suffix}@test.com"
        
        # First registration
        response1 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "username": f"user1_{unique_suffix}",
            "password": "testpass123"
        })
        assert response1.status_code == 200
        
        # Second registration with same email
        response2 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "username": f"user2_{unique_suffix}",
            "password": "testpass123"
        })
        assert response2.status_code == 400, "Should reject duplicate email"
        assert "already exists" in response2.json().get("detail", "").lower()
        print(f"✓ Duplicate lowercase email correctly rejected")
    
    def test_register_duplicate_email_uppercase(self):
        """Test that duplicate email (UPPERCASE) is rejected - case insensitive check"""
        unique_suffix = uuid.uuid4().hex[:8]
        email_lower = f"casetest_{unique_suffix}@test.com"
        email_upper = f"CASETEST_{unique_suffix}@TEST.COM"
        
        # First registration with lowercase
        response1 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email_lower,
            "username": f"caseuser1_{unique_suffix}",
            "password": "testpass123"
        })
        assert response1.status_code == 200
        print(f"✓ Registered user with lowercase email: {email_lower}")
        
        # Second registration with UPPERCASE - should be rejected
        response2 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email_upper,
            "username": f"caseuser2_{unique_suffix}",
            "password": "testpass123"
        })
        assert response2.status_code == 400, f"Should reject UPPERCASE duplicate email, got: {response2.status_code}"
        assert "already exists" in response2.json().get("detail", "").lower()
        print(f"✓ Duplicate UPPERCASE email correctly rejected: {email_upper}")
    
    def test_register_duplicate_email_mixed_case(self):
        """Test that duplicate email (MixedCase) is rejected"""
        unique_suffix = uuid.uuid4().hex[:8]
        email_original = f"mixeddup_{unique_suffix}@test.com"
        email_mixed = f"MixedDup_{unique_suffix}@Test.Com"
        
        # First registration
        response1 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email_original,
            "username": f"mixeduser1_{unique_suffix}",
            "password": "testpass123"
        })
        assert response1.status_code == 200
        
        # Second registration with mixed case - should be rejected
        response2 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email_mixed,
            "username": f"mixeduser2_{unique_suffix}",
            "password": "testpass123"
        })
        assert response2.status_code == 400, "Should reject MixedCase duplicate email"
        print(f"✓ Duplicate MixedCase email correctly rejected")


class TestGoogleAuthCategoryCreation:
    """Test the original bug: Google OAuth user creating categories"""
    
    def test_google_auth_then_create_category(self):
        """Test that Google OAuth user can create categories (original bug scenario)"""
        unique_suffix = uuid.uuid4().hex[:8]
        email = f"googlecat_{unique_suffix}@gmail.com"
        google_id = f"google_cat_{unique_suffix}"
        
        # Step 1: Google OAuth login
        auth_response = requests.post(f"{BASE_URL}/api/auth/google", json={
            "email": email,
            "google_id": google_id,
            "name": "Category Test User",
            "picture": None
        })
        assert auth_response.status_code == 200, f"Google auth failed: {auth_response.text}"
        token = auth_response.json()["token"]
        print(f"✓ Google OAuth successful for: {email}")
        
        # Step 2: Create a category (this was failing with Network Error before the fix)
        category_response = requests.post(
            f"{BASE_URL}/api/categories",
            json={
                "name": f"TEST_Category_{unique_suffix}",
                "protocol": "(test or example)",
                "is_public": False
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert category_response.status_code == 200, f"Category creation failed: {category_response.text}"
        category_data = category_response.json()
        assert "id" in category_data
        print(f"✓ Category created successfully: {category_data['name']}")
        
        # Step 3: Verify category exists
        get_response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 200
        categories = get_response.json()
        assert any(c["name"] == f"TEST_Category_{unique_suffix}" for c in categories)
        print(f"✓ Category verified in user's category list")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/categories/{category_data['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"✓ Test category cleaned up")
    
    def test_google_auth_uppercase_then_operations(self):
        """Test Google OAuth with uppercase email then perform CRUD operations"""
        unique_suffix = uuid.uuid4().hex[:8]
        email_lower = f"uppergoogle_{unique_suffix}@gmail.com"
        email_upper = email_lower.upper()
        google_id = f"google_upper_{unique_suffix}"
        
        # First auth with lowercase
        response1 = requests.post(f"{BASE_URL}/api/auth/google", json={
            "email": email_lower,
            "google_id": google_id,
            "name": "Upper Test User",
            "picture": None
        })
        assert response1.status_code == 200
        token1 = response1.json()["token"]
        user_id = response1.json()["user"]["id"]
        
        # Create a category with first token
        cat_response = requests.post(
            f"{BASE_URL}/api/categories",
            json={
                "name": f"TEST_UpperCat_{unique_suffix}",
                "protocol": "(upper or test)",
                "is_public": False
            },
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert cat_response.status_code == 200
        cat_id = cat_response.json()["id"]
        print(f"✓ Created category with lowercase email auth")
        
        # Now auth with UPPERCASE email - should get same user
        response2 = requests.post(f"{BASE_URL}/api/auth/google", json={
            "email": email_upper,
            "google_id": f"different_{google_id}",
            "name": "Upper Test User",
            "picture": None
        })
        assert response2.status_code == 200
        token2 = response2.json()["token"]
        user_id_2 = response2.json()["user"]["id"]
        
        assert user_id == user_id_2, "Should be same user"
        print(f"✓ UPPERCASE email auth returned same user")
        
        # Verify can see the category created earlier
        get_response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert get_response.status_code == 200
        categories = get_response.json()
        assert any(c["id"] == cat_id for c in categories), "Should see category created with other token"
        print(f"✓ Can access categories with UPPERCASE email auth token")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/categories/{cat_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )


class TestTokenValidation:
    """Test that tokens work correctly after case-insensitive auth"""
    
    def test_token_from_case_insensitive_login_works(self):
        """Test that token from case-insensitive login works for protected endpoints"""
        # Login with uppercase email
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "JOHN@INFOJET.COM",
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Use token to access protected endpoint
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["email"].lower() == "john@infojet.com"
        print(f"✓ Token from case-insensitive login works for /auth/me")
        
        # Test another protected endpoint
        categories_response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert categories_response.status_code == 200
        print(f"✓ Token works for /categories endpoint")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
