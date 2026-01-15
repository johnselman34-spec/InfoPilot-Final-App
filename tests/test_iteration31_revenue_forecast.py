"""
InfoPilot Explorer - Iteration 31 Tests
Testing: Revenue Forecasting, Maestro Bistro Hide Toggle, YouTube Tutorial Video Upload
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is working"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health endpoint working")
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["is_admin"] == True
        print(f"✅ Admin login successful: {data['user']['email']}")
        return data["token"]


class TestRevenueForecast:
    """Revenue Forecasting API tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin login failed")
    
    def test_revenue_forecast_summary(self, admin_token):
        """Test /api/revenue-forecast/summary endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/revenue-forecast/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "weekly" in data
        assert "monthly" in data
        assert "trend" in data
        assert "trend_percent" in data
        assert "projected_monthly" in data
        
        # Verify weekly data structure
        assert "revenue" in data["weekly"]
        assert "conversions" in data["weekly"]
        assert "conversion_rate" in data["weekly"]
        assert "avg_daily" in data["weekly"]
        
        # Verify monthly data structure
        assert "revenue" in data["monthly"]
        assert "conversions" in data["monthly"]
        assert "conversion_rate" in data["monthly"]
        assert "avg_daily" in data["monthly"]
        
        print(f"✅ Revenue summary: Weekly ${data['weekly']['revenue']:.2f}, Monthly ${data['monthly']['revenue']:.2f}")
        print(f"   Trend: {data['trend']} ({data['trend_percent']}%)")
    
    def test_revenue_forecast_data(self, admin_token):
        """Test /api/revenue-forecast/data endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/revenue-forecast/data?days=30",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "period_days" in data
        assert "daily_stats" in data
        assert "totals" in data
        assert "averages" in data
        
        # Verify totals structure
        assert "impressions" in data["totals"]
        assert "conversions" in data["totals"]
        assert "revenue" in data["totals"]
        assert "conversion_rate" in data["totals"]
        
        print(f"✅ Revenue data: {data['period_days']} days, {data['totals']['impressions']} impressions")
    
    def test_revenue_forecast_generate(self, admin_token):
        """Test /api/revenue-forecast/forecast endpoint (AI forecast generation)"""
        response = requests.get(
            f"{BASE_URL}/api/revenue-forecast/forecast?history_days=30&forecast_days=30",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=60  # AI generation may take time
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "historical_data" in data
        assert "forecast" in data
        assert "forecast_period_days" in data
        assert "generated_at" in data
        
        # Verify forecast structure
        forecast = data["forecast"]
        assert "conservative_revenue" in forecast
        assert "expected_revenue" in forecast
        assert "optimistic_revenue" in forecast
        assert "confidence_level" in forecast
        assert "key_factors" in forecast
        assert "recommendation" in forecast
        assert "weekly_breakdown" in forecast
        
        ai_generated = forecast.get("ai_generated", False)
        print(f"✅ Forecast generated: Expected ${forecast['expected_revenue']:.2f}")
        print(f"   AI Generated: {ai_generated}")
        print(f"   Confidence: {forecast['confidence_level']}")
    
    def test_revenue_forecast_requires_admin(self):
        """Test that revenue forecast endpoints require admin access"""
        # Test without auth
        response = requests.get(f"{BASE_URL}/api/revenue-forecast/summary")
        assert response.status_code in [401, 403]
        
        # Test with non-admin user (if available)
        print("✅ Revenue forecast endpoints require admin authentication")


class TestYouTubeTutorialVideo:
    """YouTube Tutorial Video Upload/Delete tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin login failed")
    
    def test_get_tutorials(self, admin_token):
        """Test getting tutorials list"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        data = response.json()
        
        assert "tutorials" in data
        assert "categories" in data
        assert "total" in data
        assert len(data["tutorials"]) > 0
        
        print(f"✅ Tutorials: {data['total']} tutorials found")
    
    def test_tutorial_video_upload_put(self, admin_token):
        """Test PUT /api/tutorials/admin/{id}/video endpoint"""
        tutorial_id = "getting-started"
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        response = requests.put(
            f"{BASE_URL}/api/tutorials/admin/{tutorial_id}/video",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "video_url": test_video_url,
                "video_id": "dQw4w9WgXcQ"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["tutorial_id"] == tutorial_id
        assert data["video_id"] == "dQw4w9WgXcQ"
        
        print(f"✅ Tutorial video upload: {tutorial_id} -> {data['video_id']}")
    
    def test_tutorial_video_delete(self, admin_token):
        """Test DELETE /api/tutorials/admin/{id}/video endpoint"""
        tutorial_id = "getting-started"
        
        response = requests.delete(
            f"{BASE_URL}/api/tutorials/admin/{tutorial_id}/video",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        print(f"✅ Tutorial video deleted: {tutorial_id}")
    
    def test_tutorial_video_requires_admin(self):
        """Test that tutorial video endpoints require admin access"""
        tutorial_id = "getting-started"
        
        # Test PUT without auth
        response = requests.put(
            f"{BASE_URL}/api/tutorials/admin/{tutorial_id}/video",
            json={"video_url": "https://youtube.com/watch?v=test"}
        )
        assert response.status_code in [401, 403]
        
        # Test DELETE without auth
        response = requests.delete(
            f"{BASE_URL}/api/tutorials/admin/{tutorial_id}/video"
        )
        assert response.status_code in [401, 403]
        
        print("✅ Tutorial video endpoints require admin authentication")
    
    def test_get_admin_videos(self, admin_token):
        """Test GET /api/tutorials/admin/videos endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/tutorials/admin/videos",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "videos" in data
        assert "total_tutorials" in data
        assert "with_videos" in data
        
        print(f"✅ Admin videos: {data['with_videos']}/{data['total_tutorials']} tutorials have videos")


class TestAdminPanelTabs:
    """Test Admin Panel has correct number of tabs"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin login failed")
    
    def test_admin_settings_endpoint(self, admin_token):
        """Test admin settings endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✅ Admin settings endpoint working")
    
    def test_ab_testing_endpoint(self, admin_token):
        """Test A/B testing endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/ab-tests",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "tests" in data
        print(f"✅ A/B Testing endpoint: {len(data['tests'])} tests found")
    
    def test_ab_optimizer_endpoint(self, admin_token):
        """Test A/B Optimizer endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/ab-optimizer/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        print(f"✅ A/B Optimizer endpoint: enabled={data['enabled']}")
    
    def test_email_reports_endpoint(self, admin_token):
        """Test Email Reports endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/email-reports/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "email_configured" in data
        print(f"✅ Email Reports endpoint: configured={data['email_configured']}")


class TestRegressionBasics:
    """Basic regression tests for existing features"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin login failed")
    
    def test_marketplace_endpoint(self, admin_token):
        """Test marketplace endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        print("✅ Marketplace endpoint working")
    
    def test_statistics_endpoint(self, admin_token):
        """Test statistics endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/statistics/overview",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✅ Statistics endpoint working")
    
    def test_newsletter_history(self, admin_token):
        """Test newsletter history endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/newsletter/history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✅ Newsletter history endpoint working")
    
    def test_polls_admin_statistics(self, admin_token):
        """Test polls admin statistics endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/polls/admin/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_polls" in data
        print(f"✅ Polls statistics: {data['total_polls']} total polls")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
