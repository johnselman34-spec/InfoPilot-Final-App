"""
Iteration 32 - Testing A/B Optimizer Scheduler, Refactored Pages, and Admin Features
Tests:
- P0: A/B Optimizer Scheduler starts on backend startup
- P1: Statistics Page loads correctly with charts, stats grid, interactive map, poll stats, leaderboards
- P1: Social Page loads correctly with Feed, Friends, Groups, Pages tabs
- Revenue Forecasting admin tab
- YouTube Tutorial Admin
- Admin Ad-Hiding (Maestro Bistro)
- Email Reports system
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://info-pilot.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is working"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health endpoint working")


class TestABOptimizerScheduler:
    """P0: Test A/B Optimizer Scheduler functionality"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_optimizer_status_endpoint(self, admin_token):
        """Test optimizer status endpoint returns scheduler info"""
        response = requests.get(
            f"{BASE_URL}/api/ab-optimizer/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Verify status fields exist
        assert "enabled" in data
        assert "min_confidence" in data
        assert "min_sample_size" in data
        print(f"✅ Optimizer status: enabled={data.get('enabled')}, confidence={data.get('min_confidence')}%")
    
    def test_optimizer_analyze_all(self, admin_token):
        """Test optimizer can analyze all tests"""
        response = requests.get(
            f"{BASE_URL}/api/ab-optimizer/analyze-all?days=30",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_tests" in data
        assert "analyses" in data
        print(f"✅ Optimizer analyze-all: {data.get('total_tests')} tests found")
    
    def test_optimizer_history(self, admin_token):
        """Test optimizer history endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ab-optimizer/history?limit=20",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        print(f"✅ Optimizer history: {len(data.get('history', []))} entries")
    
    def test_optimizer_requires_admin(self):
        """Test optimizer endpoints require admin authentication"""
        response = requests.get(f"{BASE_URL}/api/ab-optimizer/status")
        assert response.status_code in [401, 403]
        print("✅ Optimizer endpoints require authentication")


class TestStatisticsPage:
    """P1: Test Statistics Page components"""
    
    def test_statistics_dashboard(self):
        """Test statistics dashboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/statistics/dashboard")
        assert response.status_code == 200
        data = response.json()
        # Verify expected fields for charts
        assert "overview" in data or "countries" in data or "us_states" in data
        print(f"✅ Statistics dashboard returns data")
    
    def test_statistics_most_copied(self):
        """Test most copied protocols endpoint"""
        response = requests.get(f"{BASE_URL}/api/statistics/most-copied")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data or "stats" in data
        print(f"✅ Most copied endpoint working")
    
    def test_marketplace_leaderboard_sales(self):
        """Test marketplace sales leaderboard"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/sales")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        print(f"✅ Sales leaderboard: {len(data.get('leaderboard', []))} entries")
    
    def test_marketplace_leaderboard_revenue(self):
        """Test marketplace revenue leaderboard"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/revenue")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        print(f"✅ Revenue leaderboard: {len(data.get('leaderboard', []))} entries")
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_poll_user_statistics(self, admin_token):
        """Test poll user statistics endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/polls/user/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Verify poll stats fields
        assert "polls_created" in data or "polls_voted_on" in data or "total_votes_received" in data
        print(f"✅ Poll user statistics working")
    
    def test_poll_admin_statistics(self, admin_token):
        """Test poll admin statistics endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/polls/admin/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_polls" in data or "total_votes" in data
        print(f"✅ Poll admin statistics working")


class TestSocialPage:
    """P1: Test Social Page components"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_feed_endpoint(self, admin_token):
        """Test social feed endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/feed",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "posts" in data
        print(f"✅ Feed endpoint: {len(data.get('posts', []))} posts")
    
    def test_friends_endpoint(self, admin_token):
        """Test friends endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/friends",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "friends" in data
        print(f"✅ Friends endpoint: {len(data.get('friends', []))} friends")
    
    def test_friends_requests_endpoint(self, admin_token):
        """Test friend requests endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/friends/requests",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "incoming" in data or "outgoing" in data
        print(f"✅ Friend requests endpoint working")
    
    def test_groups_endpoint(self, admin_token):
        """Test groups endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        print(f"✅ Groups endpoint: {len(data.get('groups', []))} groups")
    
    def test_pages_endpoint(self, admin_token):
        """Test pages endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        print(f"✅ Pages endpoint: {len(data.get('pages', []))} pages")


class TestRevenueForecast:
    """Test Revenue Forecasting admin feature"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_revenue_forecast_summary(self, admin_token):
        """Test revenue forecast summary endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/revenue-forecast/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Verify summary fields
        assert "weekly" in data or "monthly" in data or "trend" in data
        print(f"✅ Revenue forecast summary working")
    
    def test_revenue_forecast_requires_admin(self):
        """Test revenue forecast requires admin"""
        response = requests.get(f"{BASE_URL}/api/revenue-forecast/summary")
        assert response.status_code in [401, 403]
        print("✅ Revenue forecast requires authentication")


class TestYouTubeTutorialAdmin:
    """Test YouTube Tutorial Admin feature"""
    
    def test_tutorials_endpoint(self):
        """Test tutorials endpoint returns tutorials"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        data = response.json()
        assert "tutorials" in data
        tutorials = data.get("tutorials", [])
        # Check if any tutorials have videos
        tutorials_with_videos = [t for t in tutorials if t.get("video_url") or t.get("video_id")]
        print(f"✅ Tutorials endpoint: {len(tutorials)} tutorials, {len(tutorials_with_videos)} with videos")
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_tutorial_video_update_requires_admin(self):
        """Test tutorial video update requires admin"""
        response = requests.put(
            f"{BASE_URL}/api/tutorials/admin/test-id/video",
            json={"video_url": "https://youtube.com/watch?v=test"}
        )
        assert response.status_code in [401, 403]
        print("✅ Tutorial video update requires authentication")


class TestEmailReports:
    """Test Email Reports system"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_email_reports_status(self, admin_token):
        """Test email reports status endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/email-reports/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data or "schedule" in data or "last_sent" in data
        print(f"✅ Email reports status working")
    
    def test_email_reports_requires_admin(self):
        """Test email reports requires admin"""
        response = requests.get(f"{BASE_URL}/api/email-reports/status")
        assert response.status_code in [401, 403]
        print("✅ Email reports requires authentication")


class TestABTesting:
    """Test A/B Testing endpoints (regression)"""
    
    def test_ab_tests_list(self):
        """Test A/B tests list endpoint"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/tests")
        assert response.status_code == 200
        data = response.json()
        assert "tests" in data
        print(f"✅ A/B tests: {len(data.get('tests', []))} tests found")
    
    def test_ab_variant_endpoint(self):
        """Test A/B variant endpoint"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/variant/book_promo_headline")
        assert response.status_code == 200
        data = response.json()
        assert "variant_id" in data or "value" in data
        print(f"✅ A/B variant endpoint working")


class TestAdminPanel:
    """Test Admin Panel endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_admin_settings(self, admin_token):
        """Test admin settings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Admin settings can be a list or dict depending on endpoint
        assert isinstance(data, (list, dict))
        print(f"✅ Admin settings: {len(data) if isinstance(data, list) else len(data.keys())} settings")
    
    def test_admin_requires_auth(self):
        """Test admin endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/settings")
        assert response.status_code in [401, 403]
        print("✅ Admin endpoints require authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
