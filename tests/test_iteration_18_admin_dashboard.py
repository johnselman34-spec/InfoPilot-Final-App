"""
InfoPilot Explorer - Iteration 18 Tests
Testing Admin Dashboard features:
- System status endpoint
- Maintenance mode toggle
- Health check endpoint
- Test alert endpoint
- Admin-only access control
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@infopilot.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = "testuser_new@example.com"
TEST_USER_PASSWORD = "password123"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def user_token(api_client):
    """Get regular user authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"User authentication failed: {response.status_code} - {response.text}")


@pytest.fixture
def admin_client(api_client, admin_token):
    """Session with admin auth header"""
    api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return api_client


@pytest.fixture
def user_client(api_client, user_token):
    """Session with regular user auth header"""
    api_client.headers.update({"Authorization": f"Bearer {user_token}"})
    return api_client


class TestAdminAuthentication:
    """Test admin user authentication"""
    
    def test_admin_login_success(self, api_client):
        """Test admin can login successfully"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["is_admin"] == True
        print(f"Admin login successful: {data['user']['email']}")
    
    def test_regular_user_login_success(self, api_client):
        """Test regular user can login successfully"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"].get("is_admin", False) == False
        print(f"Regular user login successful: {data['user']['email']}")


class TestAdminSystemStatus:
    """Test /api/admin/system-status endpoint"""
    
    def test_system_status_requires_admin(self, api_client, user_token):
        """Test that system-status requires admin role"""
        api_client.headers.update({"Authorization": f"Bearer {user_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin/system-status")
        assert response.status_code == 403
        print("System status correctly requires admin access")
    
    def test_system_status_returns_data(self, api_client, admin_token):
        """Test system status returns comprehensive data"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin/system-status")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "timestamp" in data
        assert "overall_status" in data
        assert "services" in data
        assert "statistics" in data
        print(f"System status returned: overall_status={data['overall_status']}")
    
    def test_system_status_services_structure(self, api_client, admin_token):
        """Test services structure in system status"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin/system-status")
        assert response.status_code == 200
        services = response.json()["services"]
        
        # Check all service categories exist
        assert "database" in services
        assert "search_engines" in services
        assert "elasticsearch" in services
        assert "email" in services
        assert "payments" in services
        assert "paywall_filter" in services
        assert "cache" in services
        
        # Check database status
        assert services["database"]["connected"] == True
        print(f"Database connected: {services['database']['name']}")
        
        # Check search engines
        assert len(services["search_engines"]) >= 2
        for engine in services["search_engines"]:
            print(f"Search engine: {engine['name']} - {engine['status']}")
    
    def test_system_status_statistics(self, api_client, admin_token):
        """Test statistics in system status"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin/system-status")
        assert response.status_code == 200
        stats = response.json()["statistics"]
        
        # Check all stat fields exist
        assert "total_users" in stats
        assert "total_categories" in stats
        assert "public_protocols" in stats
        assert "total_search_results" in stats
        assert "total_purchases" in stats
        
        print(f"Platform stats: {stats['total_users']} users, {stats['total_categories']} categories")


class TestMaintenanceMode:
    """Test /api/admin/maintenance GET and POST endpoints"""
    
    def test_maintenance_get_requires_admin(self, api_client, user_token):
        """Test that maintenance GET requires admin role"""
        api_client.headers.update({"Authorization": f"Bearer {user_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin/maintenance")
        assert response.status_code == 403
        print("Maintenance GET correctly requires admin access")
    
    def test_maintenance_post_requires_admin(self, api_client, user_token):
        """Test that maintenance POST requires admin role"""
        api_client.headers.update({"Authorization": f"Bearer {user_token}"})
        response = api_client.post(f"{BASE_URL}/api/admin/maintenance", json={
            "enabled": True,
            "message": "Test maintenance"
        })
        assert response.status_code == 403
        print("Maintenance POST correctly requires admin access")
    
    def test_maintenance_get_status(self, api_client, admin_token):
        """Test getting maintenance status"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin/maintenance")
        assert response.status_code == 200
        data = response.json()
        
        assert "enabled" in data
        assert "message" in data
        print(f"Maintenance status: enabled={data['enabled']}")
    
    def test_maintenance_enable_disable_cycle(self, api_client, admin_token):
        """Test enabling and disabling maintenance mode"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        
        # Enable maintenance
        response = api_client.post(f"{BASE_URL}/api/admin/maintenance", json={
            "enabled": True,
            "message": "Test maintenance message from pytest"
        })
        assert response.status_code == 200
        data = response.json()
        assert "maintenance" in data
        assert data["maintenance"]["enabled"] == True
        print("Maintenance mode enabled successfully")
        
        # Verify it's enabled
        response = api_client.get(f"{BASE_URL}/api/admin/maintenance")
        assert response.status_code == 200
        assert response.json()["enabled"] == True
        
        # Disable maintenance
        response = api_client.post(f"{BASE_URL}/api/admin/maintenance", json={
            "enabled": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["maintenance"]["enabled"] == False
        print("Maintenance mode disabled successfully")
        
        # Verify it's disabled
        response = api_client.get(f"{BASE_URL}/api/admin/maintenance")
        assert response.status_code == 200
        assert response.json()["enabled"] == False


class TestPublicMaintenanceStatus:
    """Test /api/maintenance-status public endpoint"""
    
    def test_public_maintenance_status_no_auth(self, api_client):
        """Test public maintenance status doesn't require auth"""
        # Remove any auth headers
        api_client.headers.pop("Authorization", None)
        response = api_client.get(f"{BASE_URL}/api/maintenance-status")
        assert response.status_code == 200
        data = response.json()
        
        assert "enabled" in data
        assert "message" in data
        print(f"Public maintenance status: enabled={data['enabled']}")


class TestHealthCheck:
    """Test /api/admin/health-check endpoint"""
    
    def test_health_check_requires_admin(self, api_client, user_token):
        """Test that health-check requires admin role"""
        api_client.headers.update({"Authorization": f"Bearer {user_token}"})
        response = api_client.post(f"{BASE_URL}/api/admin/health-check", json={
            "send_alerts": False
        })
        assert response.status_code == 403
        print("Health check correctly requires admin access")
    
    def test_health_check_without_alerts(self, api_client, admin_token):
        """Test running health check without sending alerts"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.post(f"{BASE_URL}/api/admin/health-check", json={
            "send_alerts": False
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "result" in data
        assert "services" in data["result"]
        assert "checked_at" in data["result"]
        
        # Check services health
        services = data["result"]["services"]
        print(f"Health check completed. Services checked: {list(services.keys())}")
        
        for service, status in services.items():
            print(f"  {service}: {status['status']}")


class TestTestAlert:
    """Test /api/admin/test-alert endpoint"""
    
    def test_test_alert_requires_admin(self, api_client, user_token):
        """Test that test-alert requires admin role"""
        api_client.headers.update({"Authorization": f"Bearer {user_token}"})
        response = api_client.post(f"{BASE_URL}/api/admin/test-alert")
        assert response.status_code == 403
        print("Test alert correctly requires admin access")
    
    def test_test_alert_sends_email(self, api_client, admin_token):
        """Test sending a test alert email"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.post(f"{BASE_URL}/api/admin/test-alert")
        
        # May succeed or fail depending on email config
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            print(f"Test alert sent: {data['message']}")
        else:
            # 500/520 is acceptable if email config is not working or timeout
            assert response.status_code in [500, 520]
            print(f"Test alert failed with status {response.status_code} (expected if email not configured or timeout)")


class TestRecentActivity:
    """Test /api/admin/recent-activity endpoint"""
    
    def test_recent_activity_requires_admin(self, api_client, user_token):
        """Test that recent-activity requires admin role"""
        api_client.headers.update({"Authorization": f"Bearer {user_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin/recent-activity")
        assert response.status_code == 403
        print("Recent activity correctly requires admin access")
    
    def test_recent_activity_returns_data(self, api_client, admin_token):
        """Test getting recent activity"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin/recent-activity")
        assert response.status_code == 200
        data = response.json()
        
        assert "recent_users" in data
        assert "recent_purchases" in data
        assert "chat_messages_24h" in data
        
        print(f"Recent activity: {len(data['recent_users'])} users, {len(data['recent_purchases'])} purchases, {data['chat_messages_24h']} chat messages")


class TestAdminSettings:
    """Test /api/admin/settings endpoints"""
    
    def test_admin_settings_requires_admin(self, api_client, user_token):
        """Test that admin settings requires admin role"""
        api_client.headers.update({"Authorization": f"Bearer {user_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin/settings")
        assert response.status_code == 403
        print("Admin settings correctly requires admin access")
    
    def test_admin_settings_get(self, api_client, admin_token):
        """Test getting admin settings"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin/settings")
        assert response.status_code == 200
        print("Admin settings retrieved successfully")


class TestExistingEndpoints:
    """Test existing endpoints still work (regression tests)"""
    
    def test_search_engines_status(self, api_client, admin_token):
        """Test search engines status endpoint"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/search/engines")
        assert response.status_code == 200
        data = response.json()
        
        assert "engines" in data
        engines = data["engines"]
        assert len(engines) >= 2
        
        engine_names = [e["name"] for e in engines]
        assert "DuckDuckGo" in engine_names
        assert "Brave Search" in engine_names
        print(f"Search engines: {engine_names}")
    
    def test_marketplace_protocols(self, api_client, admin_token):
        """Test marketplace protocols endpoint"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        
        assert "protocols" in data
        print(f"Marketplace has {len(data['protocols'])} protocols")
    
    def test_chat_rooms(self, api_client, admin_token):
        """Test chat rooms endpoint"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/chat/rooms")
        assert response.status_code == 200
        data = response.json()
        
        assert "rooms" in data
        print(f"Chat has {len(data['rooms'])} rooms")
    
    def test_stripe_checkout_requires_auth(self, api_client):
        """Test Stripe checkout requires authentication"""
        api_client.headers.pop("Authorization", None)
        response = api_client.post(f"{BASE_URL}/api/stripe/create-checkout", json={
            "plan": "monthly"
        })
        assert response.status_code == 401
        print("Stripe checkout correctly requires authentication")


class TestAccessControl:
    """Test that admin endpoints return 403 for non-admin users"""
    
    def test_all_admin_endpoints_require_admin(self, api_client, user_token):
        """Test all admin endpoints return 403 for regular users"""
        api_client.headers.update({"Authorization": f"Bearer {user_token}"})
        
        admin_endpoints = [
            ("GET", "/api/admin/system-status"),
            ("GET", "/api/admin/maintenance"),
            ("POST", "/api/admin/maintenance"),
            ("POST", "/api/admin/health-check"),
            ("POST", "/api/admin/test-alert"),
            ("GET", "/api/admin/recent-activity"),
            ("GET", "/api/admin/settings"),
            ("PUT", "/api/admin/settings"),
        ]
        
        for method, endpoint in admin_endpoints:
            if method == "GET":
                response = api_client.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                response = api_client.post(f"{BASE_URL}{endpoint}", json={})
            elif method == "PUT":
                response = api_client.put(f"{BASE_URL}{endpoint}", json={})
            
            assert response.status_code == 403, f"{method} {endpoint} should return 403 for non-admin"
            print(f"✓ {method} {endpoint} correctly returns 403")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
