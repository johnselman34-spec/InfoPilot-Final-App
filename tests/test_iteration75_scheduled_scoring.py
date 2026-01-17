"""
Iteration 75 - Scheduled Auto-Scoring Feature Tests
Tests for:
- GET /api/admin/domain-scoring/schedule - Get schedule config
- POST /api/admin/domain-scoring/schedule - Update schedule settings
- POST /api/admin/domain-scoring/test-email - Send test notification
- Previous domain scoring features continue to work
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


class TestScheduledAutoScoring:
    """Tests for Scheduled Auto-Scoring feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.admin_token = None
        self.test_token = None
    
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
    
    def get_test_token(self):
        """Get non-admin test user token"""
        if self.test_token:
            return self.test_token
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            self.test_token = response.json().get("token")
            return self.test_token
        return None
    
    # ============== Health Check ==============
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ Health check passed")
    
    # ============== GET Schedule Config Tests ==============
    
    def test_get_schedule_config_success(self):
        """Test GET /api/admin/domain-scoring/schedule returns config"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "enabled" in data
        assert "schedule" in data
        assert "run_hour" in data
        assert "email_notifications" in data
        assert "notification_emails" in data
        assert "last_run" in data
        assert "next_run" in data
        
        # Verify data types
        assert isinstance(data["enabled"], bool)
        assert data["schedule"] in ["hourly", "daily", "weekly"]
        assert isinstance(data["run_hour"], int)
        assert 0 <= data["run_hour"] <= 23
        assert isinstance(data["email_notifications"], bool)
        assert isinstance(data["notification_emails"], list)
        
        print(f"✅ GET schedule config: enabled={data['enabled']}, schedule={data['schedule']}, hour={data['run_hour']}")
    
    def test_get_schedule_config_unauthorized(self):
        """Test GET schedule config without auth returns 401"""
        response = self.session.get(f"{BASE_URL}/api/admin/domain-scoring/schedule")
        assert response.status_code == 401
        print("✅ GET schedule config without auth returns 401")
    
    def test_get_schedule_config_non_admin(self):
        """Test GET schedule config with non-admin user returns 403"""
        token = self.get_test_token()
        if not token:
            pytest.skip("Test user not available")
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        print("✅ GET schedule config with non-admin returns 403")
    
    # ============== POST Schedule Config Tests ==============
    
    def test_update_schedule_enable(self):
        """Test POST /api/admin/domain-scoring/schedule to enable scheduling"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "enabled": True,
                "schedule": "daily",
                "run_hour": 8,
                "email_notifications": True,
                "notification_emails": ["jjspilot24@gmail.com"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert "message" in data
        assert "config" in data
        assert data["config"]["enabled"] == True
        assert data["config"]["schedule"] == "daily"
        assert data["config"]["run_hour"] == 8
        
        print(f"✅ Schedule enabled: {data['message']}")
    
    def test_update_schedule_disable(self):
        """Test POST /api/admin/domain-scoring/schedule to disable scheduling"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "enabled": False,
                "schedule": "daily",
                "run_hour": 6,
                "email_notifications": False,
                "notification_emails": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert data["config"]["enabled"] == False
        
        print(f"✅ Schedule disabled: {data['message']}")
    
    def test_update_schedule_weekly(self):
        """Test updating schedule to weekly frequency"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "enabled": True,
                "schedule": "weekly",
                "run_hour": 10,
                "email_notifications": True,
                "notification_emails": ["jjspilot24@gmail.com"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["config"]["schedule"] == "weekly"
        assert data["config"]["run_hour"] == 10
        
        print(f"✅ Schedule set to weekly at 10:00 UTC")
    
    def test_update_schedule_hourly(self):
        """Test updating schedule to hourly frequency (for testing)"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "enabled": True,
                "schedule": "hourly",
                "run_hour": 0,
                "email_notifications": False,
                "notification_emails": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["config"]["schedule"] == "hourly"
        
        print(f"✅ Schedule set to hourly")
    
    def test_update_schedule_invalid_schedule(self):
        """Test POST schedule with invalid schedule value returns 400"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "enabled": True,
                "schedule": "monthly",  # Invalid
                "run_hour": 6,
                "email_notifications": True,
                "notification_emails": []
            }
        )
        
        assert response.status_code == 400
        print("✅ Invalid schedule value returns 400")
    
    def test_update_schedule_invalid_hour(self):
        """Test POST schedule with invalid run_hour returns 400"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "enabled": True,
                "schedule": "daily",
                "run_hour": 25,  # Invalid - must be 0-23
                "email_notifications": True,
                "notification_emails": []
            }
        )
        
        assert response.status_code == 400
        print("✅ Invalid run_hour returns 400")
    
    def test_update_schedule_unauthorized(self):
        """Test POST schedule without auth returns 401"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            json={
                "enabled": True,
                "schedule": "daily",
                "run_hour": 6,
                "email_notifications": True,
                "notification_emails": []
            }
        )
        
        assert response.status_code == 401
        print("✅ POST schedule without auth returns 401")
    
    def test_update_schedule_non_admin(self):
        """Test POST schedule with non-admin user returns 403"""
        token = self.get_test_token()
        if not token:
            pytest.skip("Test user not available")
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "enabled": True,
                "schedule": "daily",
                "run_hour": 6,
                "email_notifications": True,
                "notification_emails": []
            }
        )
        
        assert response.status_code == 403
        print("✅ POST schedule with non-admin returns 403")
    
    # ============== Test Email Tests ==============
    
    def test_send_test_email_success(self):
        """Test POST /api/admin/domain-scoring/test-email sends test notification"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/test-email",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # May return 200 (success) or 500 (if RESEND_API_KEY not configured)
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            assert "message" in data
            print(f"✅ Test email sent: {data['message']}")
        elif response.status_code == 500:
            # Expected if email service not configured
            data = response.json()
            print(f"⚠️ Test email failed (expected if RESEND not configured): {data.get('detail', 'Unknown error')}")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_send_test_email_unauthorized(self):
        """Test POST test-email without auth returns 401"""
        response = self.session.post(f"{BASE_URL}/api/admin/domain-scoring/test-email")
        assert response.status_code == 401
        print("✅ POST test-email without auth returns 401")
    
    def test_send_test_email_non_admin(self):
        """Test POST test-email with non-admin user returns 403"""
        token = self.get_test_token()
        if not token:
            pytest.skip("Test user not available")
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/test-email",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        print("✅ POST test-email with non-admin returns 403")
    
    # ============== Verify Schedule Config Persistence ==============
    
    def test_schedule_config_persistence(self):
        """Test that schedule config changes persist"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        # Set specific config
        update_response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "enabled": True,
                "schedule": "daily",
                "run_hour": 14,
                "email_notifications": True,
                "notification_emails": ["jjspilot24@gmail.com", "test@example.com"]
            }
        )
        
        assert update_response.status_code == 200
        
        # Verify by fetching config
        get_response = self.session.get(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert get_response.status_code == 200
        data = get_response.json()
        
        assert data["enabled"] == True
        assert data["schedule"] == "daily"
        assert data["run_hour"] == 14
        assert data["email_notifications"] == True
        assert "jjspilot24@gmail.com" in data["notification_emails"]
        
        # Verify next_run is calculated when enabled
        assert data["next_run"] is not None
        
        print(f"✅ Schedule config persisted correctly, next_run: {data['next_run']}")
    
    # ============== Previous Features Still Work ==============
    
    def test_domain_scoring_run_still_works(self):
        """Test POST /api/admin/domain-scoring/run still works"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/run",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "alerts_created" in data
        assert "alerts_updated" in data
        assert "summary" in data
        
        print(f"✅ Domain scoring run: {data['alerts_created']} created, {data['alerts_updated']} updated")
    
    def test_domain_alerts_still_works(self):
        """Test GET /api/admin/domain-alerts still works"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/domain-alerts",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "alerts" in data
        assert "summary" in data
        assert isinstance(data["alerts"], list)
        
        print(f"✅ Domain alerts: {data['summary'].get('total', 0)} total alerts")
    
    def test_quality_analytics_still_works(self):
        """Test GET /api/analytics/quality-scores still works"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "average_score" in data
        assert "total_results" in data
        assert "distribution" in data
        
        print(f"✅ Quality analytics: avg={data['average_score']}, total={data['total_results']}")
    
    def test_blocked_domains_still_works(self):
        """Test GET /api/admin/blocked-domains still works"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/blocked-domains",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "blocked_domains" in data
        assert isinstance(data["blocked_domains"], list)
        
        print(f"✅ Blocked domains: {len(data['blocked_domains'])} domains")
    
    # ============== Cleanup ==============
    
    def test_cleanup_reset_schedule(self):
        """Reset schedule to disabled state after tests"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "enabled": False,
                "schedule": "daily",
                "run_hour": 6,
                "email_notifications": True,
                "notification_emails": ["jjspilot24@gmail.com"]
            }
        )
        
        assert response.status_code == 200
        print("✅ Schedule reset to disabled state")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
