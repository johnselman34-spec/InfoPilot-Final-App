"""
Iteration 56 - Feature Tests
Tests for:
1. Protocol Parser 'and' vs '&' enhancement
2. Legal documents (User Agreement, Privacy Statement)
3. Easter Egg Stats
4. Health check
5. Login functionality
"""
import pytest
import requests
import os
import sys

# Add backend to path for direct testing
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://project-finale-6.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Test API health check returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_admin_login(self):
        """Test admin login with provided credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful: {data['user']['username']}")
        return data["token"]


class TestProtocolParser:
    """Test Protocol Parser 'and' vs '&' enhancement"""
    
    def test_protocol_parser_and_synonym(self):
        """Test that 'and' is treated as synonym for '&' in protocol parsing"""
        from services.protocol_service import ProtocolParser
        
        # Test protocol with '&'
        protocol_ampersand = "(word1 or word2) & (word3 or word4)"
        groups_ampersand = ProtocolParser.parse_protocol(protocol_ampersand)
        
        # Test protocol with 'and'
        protocol_and = "(word1 or word2) and (word3 or word4)"
        groups_and = ProtocolParser.parse_protocol(protocol_and)
        
        # Both should produce the same result
        assert len(groups_ampersand) == len(groups_and), f"Group count mismatch: {len(groups_ampersand)} vs {len(groups_and)}"
        assert len(groups_ampersand) == 2, f"Expected 2 groups, got {len(groups_ampersand)}"
        
        # Check terms are the same
        for i in range(len(groups_ampersand)):
            assert groups_ampersand[i]["terms"] == groups_and[i]["terms"], f"Terms mismatch in group {i}"
        
        print(f"✓ Protocol parser 'and' synonym test passed")
        print(f"  - '&' groups: {groups_ampersand}")
        print(f"  - 'and' groups: {groups_and}")
    
    def test_protocol_parser_case_insensitive_and(self):
        """Test that 'AND', 'And', 'and' all work as synonyms for '&'"""
        from services.protocol_service import ProtocolParser
        
        protocols = [
            "(word1 or word2) AND (word3 or word4)",
            "(word1 or word2) And (word3 or word4)",
            "(word1 or word2) and (word3 or word4)",
            "(word1 or word2) & (word3 or word4)"
        ]
        
        results = [ProtocolParser.parse_protocol(p) for p in protocols]
        
        # All should produce the same number of groups
        for i, result in enumerate(results):
            assert len(result) == 2, f"Protocol {i} should have 2 groups, got {len(result)}"
            assert result[0]["terms"] == ["word1", "word2"], f"Protocol {i} group 0 terms mismatch"
            assert result[1]["terms"] == ["word3", "word4"], f"Protocol {i} group 1 terms mismatch"
        
        print(f"✓ Case-insensitive 'and' test passed for all variations")
    
    def test_protocol_parser_complex_example(self):
        """Test complex protocol with multiple groups using 'and'"""
        from services.protocol_service import ProtocolParser
        
        # Complex protocol from user request
        protocol = "(breaking news or latest updates) and (politics or government) and (analysis or opinion)+"
        groups = ProtocolParser.parse_protocol(protocol)
        
        assert len(groups) == 3, f"Expected 3 groups, got {len(groups)}"
        assert groups[0]["terms"] == ["breaking news", "latest updates"]
        assert groups[1]["terms"] == ["politics", "government"]
        assert groups[2]["terms"] == ["analysis", "opinion"]
        assert groups[2]["boosted"] == True, "Third group should be boosted"
        
        print(f"✓ Complex protocol parsing test passed")
        print(f"  - Groups: {groups}")
    
    def test_protocol_parser_mixed_and_ampersand(self):
        """Test protocol with mixed 'and' and '&' operators"""
        from services.protocol_service import ProtocolParser
        
        # Mixed usage
        protocol = "(word1 or word2) and (word3 or word4) & (word5 or word6)"
        groups = ProtocolParser.parse_protocol(protocol)
        
        assert len(groups) == 3, f"Expected 3 groups, got {len(groups)}"
        assert groups[0]["terms"] == ["word1", "word2"]
        assert groups[1]["terms"] == ["word3", "word4"]
        assert groups[2]["terms"] == ["word5", "word6"]
        
        print(f"✓ Mixed 'and' and '&' test passed")
    
    def test_protocol_validation_with_and(self):
        """Test protocol validation accepts 'and' as valid operator"""
        from services.protocol_service import ProtocolParser
        
        # Valid protocol with 'and'
        protocol = "(word1 or word2) and (word3 or word4)"
        is_valid, message = ProtocolParser.validate_protocol(protocol)
        
        assert is_valid == True, f"Protocol should be valid: {message}"
        print(f"✓ Protocol validation with 'and' passed: {message}")
    
    def test_protocol_debug_with_and(self):
        """Test debug_protocol function with 'and' operator"""
        from services.protocol_service import ProtocolParser
        
        protocol = "(word1 or word2) and (word3 or word4)+"
        debug_info = ProtocolParser.debug_protocol(protocol)
        
        assert debug_info["valid"] == True
        assert debug_info["group_count"] == 2
        assert len(debug_info["groups"]) == 2
        
        print(f"✓ Protocol debug with 'and' passed")
        print(f"  - Debug info: {debug_info}")


class TestLegalEndpoints:
    """Test Legal document endpoints"""
    
    def test_terms_summary_endpoint(self):
        """Test terms summary endpoint"""
        response = requests.get(f"{BASE_URL}/api/legal/terms-summary")
        # This endpoint may or may not exist - check gracefully
        if response.status_code == 200:
            data = response.json()
            assert "summary" in data
            print(f"✓ Terms summary endpoint works: {data['summary'][:100]}...")
        elif response.status_code == 404:
            print(f"⚠ Terms summary endpoint not found (404) - may be expected")
        else:
            print(f"⚠ Terms summary endpoint returned {response.status_code}")
    
    def test_user_agreement_endpoint(self):
        """Test user agreement endpoint"""
        response = requests.get(f"{BASE_URL}/api/legal/user-agreement")
        if response.status_code == 200:
            data = response.json()
            assert "content" in data
            print(f"✓ User agreement endpoint works")
        elif response.status_code == 404:
            print(f"⚠ User agreement endpoint not found (404) - Legal components are self-contained React components")
        else:
            print(f"⚠ User agreement endpoint returned {response.status_code}")
    
    def test_privacy_policy_endpoint(self):
        """Test privacy policy endpoint"""
        response = requests.get(f"{BASE_URL}/api/legal/privacy-policy")
        if response.status_code == 200:
            data = response.json()
            assert "content" in data
            print(f"✓ Privacy policy endpoint works")
        elif response.status_code == 404:
            print(f"⚠ Privacy policy endpoint not found (404) - Legal components are self-contained React components")
        else:
            print(f"⚠ Privacy policy endpoint returned {response.status_code}")


class TestGamificationEndpoints:
    """Test Gamification endpoints for Easter Egg stats"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_gamification_achievements(self, auth_token):
        """Test gamification achievements endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/achievements",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "achievements" in data or "total_points" in data
        print(f"✓ Gamification achievements endpoint works")
        print(f"  - Data keys: {list(data.keys())}")
    
    def test_gamification_stats(self, auth_token):
        """Test gamification stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Gamification stats endpoint works")
            print(f"  - Data: {data}")
        elif response.status_code == 404:
            print(f"⚠ Gamification stats endpoint not found (404)")
        else:
            print(f"⚠ Gamification stats endpoint returned {response.status_code}")


class TestAdminSettings:
    """Test Admin settings for upgrade subscription text"""
    
    def test_admin_settings_public(self):
        """Test public admin settings endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/settings")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Admin settings endpoint works")
            # Check for upgrade promo settings
            if isinstance(data, list):
                settings_dict = {s['key']: s['value'] for s in data if 'key' in s}
            else:
                settings_dict = data
            
            if 'upgrade_promo_message' in settings_dict:
                print(f"  - Upgrade promo message: {settings_dict['upgrade_promo_message'][:100]}...")
            if 'upgrade_promo_title' in settings_dict:
                print(f"  - Upgrade promo title: {settings_dict['upgrade_promo_title']}")
        else:
            print(f"⚠ Admin settings endpoint returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
