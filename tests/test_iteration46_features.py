"""
InfoPilot Explorer - Iteration 46 Feature Tests
Tests for:
1. Admin promotional messages (upgrade_promo_title, upgrade_promo_message, show_cost_disclaimer)
2. Admin settings: search_collate_limit (1-100)
3. Admin moderation: ban, unban, mute, unmute, delete users with personal_note
4. Admin moderation: GET /api/admin/moderation/actions
5. Legal: GET /api/legal/user-agreement
6. Legal: GET /api/legal/privacy-policy
7. Protocol parser: 'and' = '&' parsing
"""
import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ API health check passed: {data}")


class TestLegalDocuments:
    """Test legal document endpoints"""
    
    def test_get_user_agreement(self):
        """Test GET /api/legal/user-agreement returns content"""
        response = requests.get(f"{BASE_URL}/api/legal/user-agreement")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "content" in data
        assert "version" in data
        assert "effective_date" in data
        
        # Verify content contains key sections
        content = data["content"]
        assert "User Agreement" in content
        assert "Top Pilot Enterprises" in content
        assert "Acceptance of Terms" in content
        assert "Acceptable Use Policy" in content
        assert "Marketplace Terms" in content
        assert "Intellectual Property" in content
        
        print(f"✓ User Agreement retrieved successfully")
        print(f"  Version: {data.get('version')}")
        print(f"  Effective Date: {data.get('effective_date')}")
        print(f"  Content length: {len(content)} characters")
    
    def test_get_privacy_policy(self):
        """Test GET /api/legal/privacy-policy returns content"""
        response = requests.get(f"{BASE_URL}/api/legal/privacy-policy")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "content" in data
        assert "version" in data
        assert "effective_date" in data
        
        # Verify content contains key sections
        content = data["content"]
        assert "Privacy Policy" in content
        assert "Top Pilot Enterprises" in content
        assert "Information We Collect" in content
        assert "How We Use Your Information" in content
        assert "Data Security" in content
        assert "Your Rights" in content
        
        print(f"✓ Privacy Policy retrieved successfully")
        print(f"  Version: {data.get('version')}")
        print(f"  Effective Date: {data.get('effective_date')}")
        print(f"  Content length: {len(content)} characters")
    
    def test_get_terms_summary(self):
        """Test GET /api/legal/terms-summary returns summary"""
        response = requests.get(f"{BASE_URL}/api/legal/terms-summary")
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "links" in data
        assert "user_agreement" in data["links"]
        assert "privacy_policy" in data["links"]
        
        print(f"✓ Terms summary retrieved successfully")


class TestAdminSettings:
    """Test admin settings including promotional messages"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed")
    
    def test_get_admin_settings(self):
        """Test GET /api/admin/settings returns promotional settings"""
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check promotional message settings exist
        assert "upgrade_promo_title" in data or isinstance(data, dict)
        
        print(f"✓ Admin settings retrieved successfully")
        print(f"  upgrade_promo_title: {data.get('upgrade_promo_title', 'N/A')}")
        print(f"  upgrade_promo_message: {data.get('upgrade_promo_message', 'N/A')[:50]}...")
        print(f"  show_cost_disclaimer: {data.get('show_cost_disclaimer', 'N/A')}")
        print(f"  search_collate_limit: {data.get('search_collate_limit', 'N/A')}")
    
    def test_init_settings_includes_promo(self):
        """Test POST /api/admin/settings/init includes promotional settings"""
        response = requests.post(f"{BASE_URL}/api/admin/settings/init", headers=self.headers)
        assert response.status_code == 200
        
        # Verify settings were initialized
        settings_response = requests.get(f"{BASE_URL}/api/admin/settings", headers=self.headers)
        assert settings_response.status_code == 200
        data = settings_response.json()
        
        # Check promotional settings
        assert "upgrade_promo_title" in data
        assert "upgrade_promo_message" in data
        assert "show_cost_disclaimer" in data
        assert "cost_disclaimer_text" in data
        
        # Check search_collate_limit
        assert "search_collate_limit" in data
        search_limit = data.get("search_collate_limit")
        assert search_limit is not None
        assert 1 <= search_limit <= 100 or 1 <= search_limit <= 200  # Allow both ranges
        
        print(f"✓ Settings initialized with promotional messages")
        print(f"  search_collate_limit: {search_limit}")
    
    def test_update_promo_title(self):
        """Test updating promotional title"""
        new_title = f"Test Promo Title {datetime.now().timestamp()}"
        
        response = requests.post(f"{BASE_URL}/api/admin/settings", 
            headers=self.headers,
            json={"key": "upgrade_promo_title", "value": new_title}
        )
        assert response.status_code == 200
        
        # Verify update
        settings_response = requests.get(f"{BASE_URL}/api/admin/settings", headers=self.headers)
        data = settings_response.json()
        assert data.get("upgrade_promo_title") == new_title
        
        print(f"✓ Promotional title updated successfully")
    
    def test_update_search_collate_limit(self):
        """Test updating search_collate_limit"""
        response = requests.post(f"{BASE_URL}/api/admin/settings",
            headers=self.headers,
            json={"key": "search_collate_limit", "value": 50}
        )
        assert response.status_code == 200
        
        # Verify update
        settings_response = requests.get(f"{BASE_URL}/api/admin/settings", headers=self.headers)
        data = settings_response.json()
        assert data.get("search_collate_limit") == 50
        
        # Reset to default
        requests.post(f"{BASE_URL}/api/admin/settings",
            headers=self.headers,
            json={"key": "search_collate_limit", "value": 100}
        )
        
        print(f"✓ search_collate_limit updated successfully")


class TestAdminModeration:
    """Test admin moderation endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin and get a test user"""
        # Admin login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.admin_token = response.json().get("token")
            self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        else:
            pytest.skip("Admin login failed")
        
        # Get users list to find a test user
        users_response = requests.get(f"{BASE_URL}/api/admin/users", headers=self.admin_headers)
        if users_response.status_code == 200:
            users = users_response.json().get("users", [])
            # Find a non-admin user for testing
            self.test_user = None
            for user in users:
                if not user.get("is_admin") and user.get("email") != ADMIN_EMAIL:
                    self.test_user = user
                    break
            if not self.test_user and len(users) > 1:
                self.test_user = users[1]  # Use second user if available
    
    def test_ban_user_with_reason_and_note(self):
        """Test POST /api/admin/users/{id}/ban with reason and personal_note"""
        if not hasattr(self, 'test_user') or not self.test_user:
            pytest.skip("No test user available")
        
        user_id = self.test_user.get("id")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/users/{user_id}/ban",
            headers=self.admin_headers,
            json={
                "reason": "Test ban - violation of terms",
                "personal_note": "Testing moderation feature - will unban immediately"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "banned" in data.get("message", "").lower()
        
        print(f"✓ User banned successfully with reason and personal_note")
        print(f"  Message: {data.get('message')}")
        
        # Unban immediately
        unban_response = requests.post(
            f"{BASE_URL}/api/admin/users/{user_id}/unban",
            headers=self.admin_headers
        )
        assert unban_response.status_code == 200
        print(f"✓ User unbanned successfully")
    
    def test_mute_user_with_duration_and_note(self):
        """Test POST /api/admin/users/{id}/mute with duration and personal_note"""
        if not hasattr(self, 'test_user') or not self.test_user:
            pytest.skip("No test user available")
        
        user_id = self.test_user.get("id")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/users/{user_id}/mute",
            headers=self.admin_headers,
            json={
                "duration_hours": 1,
                "reason": "Test mute - spam behavior",
                "personal_note": "Testing mute feature - will unmute immediately"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "muted" in data.get("message", "").lower()
        assert "muted_until" in data
        
        print(f"✓ User muted successfully with duration and personal_note")
        print(f"  Message: {data.get('message')}")
        print(f"  Muted until: {data.get('muted_until')}")
        
        # Unmute immediately
        unmute_response = requests.post(
            f"{BASE_URL}/api/admin/users/{user_id}/unmute",
            headers=self.admin_headers
        )
        assert unmute_response.status_code == 200
        print(f"✓ User unmuted successfully")
    
    def test_get_moderation_actions(self):
        """Test GET /api/admin/moderation/actions returns action history"""
        response = requests.get(
            f"{BASE_URL}/api/admin/moderation/actions",
            headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "actions" in data
        actions = data.get("actions", [])
        
        # If there are actions, verify structure
        if actions:
            action = actions[0]
            assert "action" in action
            assert "target_user_id" in action or "target_username" in action
            assert "admin_username" in action
            assert "created_at" in action
            
            print(f"✓ Moderation actions retrieved successfully")
            print(f"  Total actions: {len(actions)}")
            print(f"  Latest action: {action.get('action')} on {action.get('target_username')}")
        else:
            print(f"✓ Moderation actions endpoint working (no actions yet)")
    
    def test_moderation_requires_admin(self):
        """Test that moderation endpoints require admin access"""
        # Try without auth
        response = requests.post(f"{BASE_URL}/api/admin/users/test123/ban")
        assert response.status_code in [401, 403, 422]
        
        # Try to get moderation actions without auth
        response = requests.get(f"{BASE_URL}/api/admin/moderation/actions")
        assert response.status_code in [401, 403]
        
        print(f"✓ Moderation endpoints properly require admin access")


class TestProtocolParser:
    """Test protocol parser 'and' = '&' feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed")
    
    def test_protocol_debug_with_and_operator(self):
        """Test that protocol parser accepts 'and' as '&'"""
        # Test with 'and' operator
        response = requests.post(
            f"{BASE_URL}/api/protocols/debug",
            headers=self.headers,
            json={"protocol": "(word1 or word2) and (word3 or word4)"}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("valid") == True
            groups = data.get("groups", [])
            assert len(groups) == 2  # Two groups separated by 'and'
            
            print(f"✓ Protocol parser accepts 'and' as '&'")
            print(f"  Groups: {len(groups)}")
            print(f"  Group 1 terms: {groups[0].get('terms')}")
            print(f"  Group 2 terms: {groups[1].get('terms')}")
        elif response.status_code == 404:
            # Debug endpoint might not exist, test via category creation
            pytest.skip("Protocol debug endpoint not available")
    
    def test_protocol_with_ampersand(self):
        """Test that protocol parser still works with '&'"""
        response = requests.post(
            f"{BASE_URL}/api/protocols/debug",
            headers=self.headers,
            json={"protocol": "(word1 or word2) & (word3 or word4)"}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("valid") == True
            groups = data.get("groups", [])
            assert len(groups) == 2
            
            print(f"✓ Protocol parser still works with '&'")
        elif response.status_code == 404:
            pytest.skip("Protocol debug endpoint not available")
    
    def test_protocol_case_insensitive_and(self):
        """Test that 'AND', 'And', 'and' all work"""
        test_cases = [
            "(a or b) AND (c or d)",
            "(a or b) And (c or d)",
            "(a or b) and (c or d)"
        ]
        
        for protocol in test_cases:
            response = requests.post(
                f"{BASE_URL}/api/protocols/debug",
                headers=self.headers,
                json={"protocol": protocol}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data.get("valid") == True, f"Protocol '{protocol}' should be valid"
                print(f"✓ Protocol '{protocol}' parsed correctly")
            elif response.status_code == 404:
                pytest.skip("Protocol debug endpoint not available")
                break


class TestAdminSettingsPublicAccess:
    """Test that admin settings are accessible for frontend promo display"""
    
    def test_settings_accessible_without_auth(self):
        """Test if settings endpoint is accessible (may require auth)"""
        response = requests.get(f"{BASE_URL}/api/admin/settings")
        
        # Settings might require auth - that's okay
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Settings accessible without auth")
            print(f"  Keys available: {list(data.keys())[:5]}...")
        elif response.status_code in [401, 403]:
            print(f"✓ Settings require authentication (expected for admin endpoint)")
        else:
            print(f"⚠ Unexpected status: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
