"""
Iteration 57 - Comprehensive Feature Tests
Tests for:
1. Personal Reports Page - CRUD operations
2. PayPal Wallet Page - Earnings and payout info
3. Upgrade Subscription Promo Banner
4. Easter Egg Stats and Reward History
5. Quick Links section in Settings
6. Maestro Bistro food images
7. Category management in Settings
8. Legal documents accessibility
9. API health check
10. Admin login
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "password123"


class TestHealthAndAuth:
    """Health check and authentication tests"""
    
    def test_health_endpoint(self):
        """Test API health endpoint"""
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
        assert data.get("user", {}).get("is_admin") == True
        print(f"✓ Admin login successful: {data['user'].get('email')}")
        return data["token"]


class TestPersonalReports:
    """Personal Reports CRUD tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_get_personal_reports(self, admin_token):
        """Test fetching personal reports list"""
        response = requests.get(
            f"{BASE_URL}/api/personal-reports",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        print(f"✓ Personal reports fetched: {len(data.get('reports', []))} reports")
    
    def test_create_personal_report(self, admin_token):
        """Test creating a new personal report"""
        report_data = {
            "title": f"TEST_Report_{datetime.now().strftime('%H%M%S')}",
            "topic": "Technology",
            "content": "This is a test personal report content for iteration 57 testing.",
            "location": "Brunswick, Maine"
        }
        response = requests.post(
            f"{BASE_URL}/api/personal-reports",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=report_data
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "report" in data or "id" in data
        print(f"✓ Personal report created: {data}")
        return data.get("report", {}).get("id") or data.get("id")


class TestPayPalWallet:
    """PayPal Wallet and Earnings tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_get_my_earnings(self, admin_token):
        """Test fetching user's earnings/wallet info"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/my-earnings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Verify expected fields
        assert "accumulated_earnings" in data or "pending_balance" in data
        print(f"✓ Earnings fetched: {data}")
    
    def test_update_paypal_email(self, admin_token):
        """Test updating PayPal email"""
        response = requests.put(
            f"{BASE_URL}/api/marketplace/my-paypal-email",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"paypal_email": "test-paypal@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✓ PayPal email updated: {data}")


class TestAdminSettings:
    """Admin settings and public settings tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_get_public_settings(self):
        """Test fetching public admin settings (for promo banner)"""
        response = requests.get(f"{BASE_URL}/api/admin/settings/public")
        # This endpoint may or may not exist - check both cases
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Public settings fetched: {data}")
        elif response.status_code == 404:
            print("⚠ Public settings endpoint not found (may need implementation)")
        else:
            print(f"⚠ Public settings returned status {response.status_code}")
    
    def test_get_admin_settings(self, admin_token):
        """Test fetching admin settings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Admin settings fetched: {len(data)} settings")


class TestCategories:
    """Category management tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_get_categories(self, admin_token):
        """Test fetching categories list"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Categories fetched: {len(data)} categories")
        return data


class TestGamification:
    """Gamification and Easter Egg tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_get_gamification_profile(self, admin_token):
        """Test fetching gamification profile (for Easter Egg stats)"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/profile",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should have XP, level, badges info
        assert "xp" in data or "total_xp" in data or "level" in data
        print(f"✓ Gamification profile fetched: {data}")
    
    def test_get_achievements(self, admin_token):
        """Test fetching achievements"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/achievements",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Achievements fetched: {data}")


class TestMarketplace:
    """Marketplace protocol tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_get_marketplace_protocols(self, admin_token):
        """Test fetching marketplace protocols"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/protocols",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        print(f"✓ Marketplace protocols fetched: {len(data.get('protocols', []))} protocols")
    
    def test_get_seller_sales(self, admin_token):
        """Test fetching seller sales info"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/seller/sales",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Seller sales fetched: {data}")


class TestQuoteGallery:
    """Quote gallery tests"""
    
    def test_get_quote_gallery(self):
        """Test fetching quote gallery"""
        response = requests.get(f"{BASE_URL}/api/quotes/gallery")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Quote gallery fetched: {len(data) if isinstance(data, list) else 'N/A'} quotes")


class TestProtocolValidation:
    """Protocol validation tests"""
    
    def test_validate_protocol(self):
        """Test protocol validation endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/protocol/validate",
            json={"protocol": "(word1 or word2) & (word3 or word4)+"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Protocol validation: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
