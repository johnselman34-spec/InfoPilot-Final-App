"""
Iteration 74 - Automatic Domain Scoring Feature Tests
Tests for domain scoring analysis, domain alerts, and alert actions.

Features tested:
- POST /api/admin/domain-scoring/run - Run domain scoring analysis
- GET /api/admin/domain-alerts - Get list of domain alerts
- POST /api/admin/domain-alerts/{id}/dismiss - Dismiss an alert
- POST /api/admin/domain-alerts/{id}/block - Block domain from alert
- DELETE /api/admin/domain-alerts/clear-dismissed - Clear dismissed alerts
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestDomainScoringAPI:
    """Test suite for Automatic Domain Scoring feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.admin_token = None
        self.test_alert_id = None
    
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
    
    def get_auth_headers(self, token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    # ==================== Health Check ====================
    
    def test_01_health_check(self):
        """Test API health endpoint"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ Health check passed")
    
    # ==================== Authentication ====================
    
    def test_02_admin_login(self):
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
    
    # ==================== Domain Scoring Run ====================
    
    def test_03_run_domain_scoring_requires_auth(self):
        """Test that domain scoring requires authentication"""
        response = self.session.post(f"{BASE_URL}/api/admin/domain-scoring/run")
        assert response.status_code == 401 or response.status_code == 403
        print("✅ Domain scoring requires authentication")
    
    def test_04_run_domain_scoring_success(self):
        """Test running domain scoring analysis"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/run",
            headers=self.get_auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data.get("success") == True
        assert "alerts_created" in data
        assert "alerts_updated" in data
        assert "summary" in data
        assert "thresholds" in data
        
        # Verify summary structure
        summary = data.get("summary", {})
        assert "total_alerts" in summary
        assert "critical" in summary
        assert "warning" in summary
        assert "watch" in summary
        
        # Verify thresholds
        thresholds = data.get("thresholds", {})
        assert "critical" in thresholds
        assert "warning" in thresholds
        assert "watch" in thresholds
        
        print(f"✅ Domain scoring run successful:")
        print(f"   - Alerts created: {data.get('alerts_created')}")
        print(f"   - Alerts updated: {data.get('alerts_updated')}")
        print(f"   - Total alerts: {summary.get('total_alerts')}")
        print(f"   - Critical: {summary.get('critical')}, Warning: {summary.get('warning')}, Watch: {summary.get('watch')}")
    
    # ==================== Get Domain Alerts ====================
    
    def test_05_get_domain_alerts_requires_auth(self):
        """Test that getting domain alerts requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/admin/domain-alerts")
        assert response.status_code == 401 or response.status_code == 403
        print("✅ Get domain alerts requires authentication")
    
    def test_06_get_domain_alerts_success(self):
        """Test getting domain alerts list"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/domain-alerts",
            headers=self.get_auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "alerts" in data
        assert "summary" in data
        assert isinstance(data["alerts"], list)
        
        # Verify summary structure
        summary = data.get("summary", {})
        assert "total" in summary
        assert "critical" in summary
        assert "warning" in summary
        assert "watch" in summary
        
        # If there are alerts, verify alert structure
        if len(data["alerts"]) > 0:
            alert = data["alerts"][0]
            assert "id" in alert
            assert "domain" in alert
            assert "alert_level" in alert
            assert "avg_score" in alert
            assert "result_count" in alert
            
            # Store alert ID for later tests
            self.__class__.test_alert_id = alert["id"]
            
            print(f"✅ Get domain alerts successful: {len(data['alerts'])} alerts found")
            print(f"   - First alert: {alert['domain']} ({alert['alert_level']}, score: {alert['avg_score']})")
        else:
            print("✅ Get domain alerts successful: No alerts (all domains meet quality standards)")
    
    def test_07_get_domain_alerts_with_filter(self):
        """Test getting domain alerts with alert_level filter"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # Test filtering by watch level
        response = self.session.get(
            f"{BASE_URL}/api/admin/domain-alerts?alert_level=watch",
            headers=self.get_auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned alerts should be watch level
        for alert in data.get("alerts", []):
            assert alert["alert_level"] == "watch"
        
        print(f"✅ Get domain alerts with filter successful: {len(data.get('alerts', []))} watch alerts")
    
    def test_08_get_domain_alerts_include_dismissed(self):
        """Test getting domain alerts including dismissed"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/domain-alerts?include_dismissed=true",
            headers=self.get_auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        print(f"✅ Get domain alerts with dismissed successful: {len(data.get('alerts', []))} total alerts")
    
    # ==================== Dismiss Alert ====================
    
    def test_09_dismiss_alert_requires_auth(self):
        """Test that dismissing alert requires authentication"""
        response = self.session.post(f"{BASE_URL}/api/admin/domain-alerts/fake-id/dismiss")
        assert response.status_code == 401 or response.status_code == 403
        print("✅ Dismiss alert requires authentication")
    
    def test_10_dismiss_alert_invalid_id(self):
        """Test dismissing alert with invalid ID"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-alerts/invalid-id/dismiss",
            headers=self.get_auth_headers(token)
        )
        
        # Should return 400 (invalid ObjectId) or 404 (not found)
        assert response.status_code in [400, 404]
        print("✅ Dismiss alert with invalid ID handled correctly")
    
    def test_11_dismiss_alert_success(self):
        """Test dismissing a domain alert"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # First get an alert to dismiss
        response = self.session.get(
            f"{BASE_URL}/api/admin/domain-alerts",
            headers=self.get_auth_headers(token)
        )
        
        assert response.status_code == 200
        alerts = response.json().get("alerts", [])
        
        if len(alerts) == 0:
            pytest.skip("No alerts available to dismiss")
        
        alert_id = alerts[0]["id"]
        alert_domain = alerts[0]["domain"]
        
        # Dismiss the alert
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-alerts/{alert_id}/dismiss",
            headers=self.get_auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        
        print(f"✅ Dismiss alert successful: {alert_domain}")
    
    # ==================== Block From Alert ====================
    
    def test_12_block_from_alert_requires_auth(self):
        """Test that blocking from alert requires authentication"""
        response = self.session.post(f"{BASE_URL}/api/admin/domain-alerts/fake-id/block")
        assert response.status_code == 401 or response.status_code == 403
        print("✅ Block from alert requires authentication")
    
    def test_13_block_from_alert_invalid_id(self):
        """Test blocking from alert with invalid ID"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-alerts/invalid-id/block",
            headers=self.get_auth_headers(token)
        )
        
        # Should return 400 (invalid ObjectId) or 404 (not found)
        assert response.status_code in [400, 404]
        print("✅ Block from alert with invalid ID handled correctly")
    
    def test_14_block_from_alert_success(self):
        """Test blocking domain from an alert"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # First get an alert to block
        response = self.session.get(
            f"{BASE_URL}/api/admin/domain-alerts",
            headers=self.get_auth_headers(token)
        )
        
        assert response.status_code == 200
        alerts = response.json().get("alerts", [])
        
        if len(alerts) == 0:
            pytest.skip("No alerts available to block")
        
        alert_id = alerts[0]["id"]
        alert_domain = alerts[0]["domain"]
        
        # Block from the alert
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-alerts/{alert_id}/block",
            headers=self.get_auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "results_removed" in data or "message" in data
        
        print(f"✅ Block from alert successful: {alert_domain}")
        if "results_removed" in data:
            print(f"   - Results removed: {data.get('results_removed')}")
    
    # ==================== Clear Dismissed Alerts ====================
    
    def test_15_clear_dismissed_requires_auth(self):
        """Test that clearing dismissed alerts requires authentication"""
        response = self.session.delete(f"{BASE_URL}/api/admin/domain-alerts/clear-dismissed")
        assert response.status_code == 401 or response.status_code == 403
        print("✅ Clear dismissed alerts requires authentication")
    
    def test_16_clear_dismissed_success(self):
        """Test clearing dismissed alerts"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.delete(
            f"{BASE_URL}/api/admin/domain-alerts/clear-dismissed",
            headers=self.get_auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "deleted_count" in data
        
        print(f"✅ Clear dismissed alerts successful: {data.get('deleted_count')} alerts cleared")
    
    # ==================== Previous Features Stability ====================
    
    def test_17_blocked_domains_api_still_works(self):
        """Test that blocked domains API still works"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/blocked-domains",
            headers=self.get_auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "blocked_domains" in data
        print(f"✅ Blocked domains API works: {len(data.get('blocked_domains', []))} domains blocked")
    
    def test_18_quality_analytics_api_still_works(self):
        """Test that quality analytics API still works"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers=self.get_auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "average_score" in data
        assert "total_results" in data
        print(f"✅ Quality analytics API works: avg score {data.get('average_score')}, {data.get('total_results')} results")
    
    def test_19_admin_stats_api_still_works(self):
        """Test that admin stats API still works"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/stats",
            headers=self.get_auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.json()
        # Admin stats returns 'users' not 'total_users'
        assert "users" in data or "categories" in data
        print(f"✅ Admin stats API works: {data.get('users', 'N/A')} users, {data.get('categories', 'N/A')} categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
