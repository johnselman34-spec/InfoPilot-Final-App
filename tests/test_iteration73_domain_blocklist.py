"""
Iteration 73 - Domain Blocklist Management Tests
Tests for the new Domain Blocklist Management feature in Quality Analytics

Features tested:
- GET /api/admin/blocked-domains - List blocked domains
- POST /api/admin/blocked-domains - Add domain to blocklist
- DELETE /api/admin/blocked-domains/{domain} - Remove domain from blocklist
- POST /api/admin/blocked-domains/bulk - Bulk block multiple domains
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


class TestDomainBlocklistAPI:
    """Tests for Domain Blocklist Management API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.admin_token = None
        self.test_domain = f"test-domain-{int(time.time())}.com"
        
    def get_admin_token(self):
        """Get admin authentication token"""
        if self.admin_token:
            return self.admin_token
            
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.admin_token = response.json().get("token")
            return self.admin_token
        return None
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ Health check passed")
    
    def test_admin_login(self):
        """Test admin login"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data.get("user", {}).get("is_admin") == True
        print(f"✅ Admin login successful: {ADMIN_EMAIL}")
    
    def test_get_blocked_domains_requires_auth(self):
        """Test that GET /admin/blocked-domains requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/admin/blocked-domains")
        assert response.status_code == 401
        print("✅ GET blocked-domains correctly requires authentication")
    
    def test_get_blocked_domains_requires_admin(self):
        """Test that GET /admin/blocked-domains requires admin role"""
        # First try to login as test user (non-admin)
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            test_token = login_response.json().get("token")
            response = self.session.get(
                f"{BASE_URL}/api/admin/blocked-domains",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            assert response.status_code == 403
            print("✅ GET blocked-domains correctly requires admin role")
        else:
            pytest.skip("Test user not available - skipping non-admin test")
    
    def test_get_blocked_domains_success(self):
        """Test GET /admin/blocked-domains returns list of blocked domains"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/blocked-domains",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "blocked_domains" in data
        assert "total_blocked" in data
        assert isinstance(data["blocked_domains"], list)
        assert isinstance(data["total_blocked"], int)
        
        # If there are blocked domains, verify structure
        if data["blocked_domains"]:
            domain = data["blocked_domains"][0]
            assert "id" in domain
            assert "domain" in domain
            assert "reason" in domain
            assert "blocked_at" in domain
        
        print(f"✅ GET blocked-domains returned {data['total_blocked']} blocked domains")
    
    def test_add_blocked_domain_requires_auth(self):
        """Test that POST /admin/blocked-domains requires authentication"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/blocked-domains",
            json={"domain": "test.com", "reason": "Test"}
        )
        assert response.status_code == 401
        print("✅ POST blocked-domains correctly requires authentication")
    
    def test_add_blocked_domain_success(self):
        """Test POST /admin/blocked-domains adds domain to blocklist"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/blocked-domains",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "domain": self.test_domain,
                "reason": "Test blocking - low quality",
                "avg_score": 25.5,
                "result_count": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data.get("success") == True
        assert "message" in data
        assert "results_removed" in data
        assert "blocked_domain" in data
        assert data["blocked_domain"]["domain"] == self.test_domain.lower()
        
        print(f"✅ Successfully blocked domain: {self.test_domain}")
    
    def test_add_duplicate_domain_fails(self):
        """Test that adding an already blocked domain fails"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # First add the domain
        self.session.post(
            f"{BASE_URL}/api/admin/blocked-domains",
            headers={"Authorization": f"Bearer {token}"},
            json={"domain": self.test_domain, "reason": "Test"}
        )
        
        # Try to add again
        response = self.session.post(
            f"{BASE_URL}/api/admin/blocked-domains",
            headers={"Authorization": f"Bearer {token}"},
            json={"domain": self.test_domain, "reason": "Test duplicate"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already blocked" in data.get("detail", "").lower()
        
        print("✅ Duplicate domain correctly rejected")
    
    def test_delete_blocked_domain_requires_auth(self):
        """Test that DELETE /admin/blocked-domains/{domain} requires authentication"""
        response = self.session.delete(f"{BASE_URL}/api/admin/blocked-domains/test.com")
        assert response.status_code == 401
        print("✅ DELETE blocked-domains correctly requires authentication")
    
    def test_delete_blocked_domain_success(self):
        """Test DELETE /admin/blocked-domains/{domain} removes domain from blocklist"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # First add a domain to delete
        add_response = self.session.post(
            f"{BASE_URL}/api/admin/blocked-domains",
            headers={"Authorization": f"Bearer {token}"},
            json={"domain": self.test_domain, "reason": "Test for deletion"}
        )
        
        # Now delete it
        response = self.session.delete(
            f"{BASE_URL}/api/admin/blocked-domains/{self.test_domain}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert "removed from blocklist" in data.get("message", "").lower()
        
        print(f"✅ Successfully unblocked domain: {self.test_domain}")
    
    def test_delete_nonexistent_domain_fails(self):
        """Test that deleting a non-existent domain returns 404"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.delete(
            f"{BASE_URL}/api/admin/blocked-domains/nonexistent-domain-xyz123.com",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
        print("✅ Delete non-existent domain correctly returns 404")
    
    def test_bulk_block_domains_requires_auth(self):
        """Test that POST /admin/blocked-domains/bulk requires authentication"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/blocked-domains/bulk",
            json={"domains": [{"domain": "test1.com"}, {"domain": "test2.com"}]}
        )
        assert response.status_code == 401
        print("✅ POST bulk blocked-domains correctly requires authentication")
    
    def test_bulk_block_domains_success(self):
        """Test POST /admin/blocked-domains/bulk blocks multiple domains"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # Create unique test domains
        timestamp = int(time.time())
        test_domains = [
            {"domain": f"bulk-test1-{timestamp}.com", "avg_score": 20, "count": 5, "reason": "Low quality (avg: 20)"},
            {"domain": f"bulk-test2-{timestamp}.com", "avg_score": 15, "count": 3, "reason": "Low quality (avg: 15)"},
            {"domain": f"bulk-test3-{timestamp}.com", "avg_score": 10, "count": 2, "reason": "Low quality (avg: 10)"}
        ]
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/blocked-domains/bulk",
            headers={"Authorization": f"Bearer {token}"},
            json={"domains": test_domains}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data.get("success") == True
        assert "blocked_count" in data
        assert "skipped_count" in data
        assert "total_results_removed" in data
        assert data["blocked_count"] == 3
        
        print(f"✅ Bulk blocked {data['blocked_count']} domains, skipped {data['skipped_count']}")
        
        # Cleanup - unblock the test domains
        for domain_info in test_domains:
            self.session.delete(
                f"{BASE_URL}/api/admin/blocked-domains/{domain_info['domain']}",
                headers={"Authorization": f"Bearer {token}"}
            )
    
    def test_bulk_block_skips_existing(self):
        """Test that bulk block skips already blocked domains"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        timestamp = int(time.time())
        test_domain = f"bulk-skip-test-{timestamp}.com"
        
        # First block a domain
        self.session.post(
            f"{BASE_URL}/api/admin/blocked-domains",
            headers={"Authorization": f"Bearer {token}"},
            json={"domain": test_domain, "reason": "Pre-blocked"}
        )
        
        # Try to bulk block including the already blocked domain
        response = self.session.post(
            f"{BASE_URL}/api/admin/blocked-domains/bulk",
            headers={"Authorization": f"Bearer {token}"},
            json={"domains": [
                {"domain": test_domain, "avg_score": 20},
                {"domain": f"new-domain-{timestamp}.com", "avg_score": 15}
            ]}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["blocked_count"] == 1  # Only the new domain
        assert data["skipped_count"] == 1  # The pre-blocked domain
        
        print(f"✅ Bulk block correctly skipped {data['skipped_count']} existing domains")
        
        # Cleanup
        self.session.delete(
            f"{BASE_URL}/api/admin/blocked-domains/{test_domain}",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.session.delete(
            f"{BASE_URL}/api/admin/blocked-domains/new-domain-{timestamp}.com",
            headers={"Authorization": f"Bearer {token}"}
        )


class TestQualityAnalyticsIntegration:
    """Tests for Quality Analytics integration with Domain Blocklist"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.admin_token = None
        
    def get_admin_token(self):
        """Get admin authentication token"""
        if self.admin_token:
            return self.admin_token
            
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.admin_token = response.json().get("token")
            return self.admin_token
        return None
    
    def test_quality_analytics_endpoint(self):
        """Test that quality analytics endpoint still works"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify key fields
        assert "total_results" in data
        assert "average_score" in data
        assert "distribution" in data
        assert "improvement_opportunities" in data
        
        print(f"✅ Quality analytics returned {data['total_results']} results with avg score {data['average_score']}")
    
    def test_improvement_opportunities_structure(self):
        """Test that improvement opportunities have correct structure for blocking"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        opportunities = data.get("improvement_opportunities", [])
        if opportunities:
            opp = opportunities[0]
            # Verify structure matches what frontend expects for blocking
            assert "domain" in opp
            assert "avg_score" in opp
            assert "count" in opp
            print(f"✅ Improvement opportunities have correct structure: {len(opportunities)} domains")
        else:
            print("ℹ️ No improvement opportunities found (all content meets quality standards)")


class TestPreviousFeaturesStability:
    """Tests to ensure previous features still work"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.admin_token = None
        
    def get_admin_token(self):
        """Get admin authentication token"""
        if self.admin_token:
            return self.admin_token
            
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.admin_token = response.json().get("token")
            return self.admin_token
        return None
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✅ Health endpoint working")
    
    def test_auth_login(self):
        """Test authentication"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        print("✅ Auth login working")
    
    def test_categories_endpoint(self):
        """Test categories endpoint"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        print("✅ Categories endpoint working")
    
    def test_admin_stats_endpoint(self):
        """Test admin stats endpoint"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        print("✅ Admin stats endpoint working")
    
    def test_marketplace_leaderboard(self):
        """Test marketplace leaderboard endpoint"""
        response = self.session.get(f"{BASE_URL}/api/marketplace/leaderboard")
        assert response.status_code == 200
        print("✅ Marketplace leaderboard working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
