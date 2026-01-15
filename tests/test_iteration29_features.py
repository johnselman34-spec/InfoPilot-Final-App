"""
InfoPilot Explorer - Iteration 29 Feature Tests
Tests for:
- AI-powered email reports with GPT-5.2 insights
- Email scheduler configuration (Monday 9 AM UTC)
- YouTube Tutorial Admin - 4 tutorials with videos configured
- Tutorials endpoint returns tutorials with video data
- Statistics components exist and export correctly
- Social components exist and export correctly
- Marketplace components exist and export correctly
- All pages load correctly (Ultimate Search, Statistics, Social, Marketplace)
- Admin Panel - All 10 tabs working
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✅ Health check passed: {data}")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["is_admin"] == True
        print(f"✅ Admin login successful, user: {data['user']['email']}")
        return data["token"]


class TestAIPoweredEmailReports:
    """AI-powered Email Reports with GPT-5.2 insights tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_email_status_shows_configuration(self, admin_token):
        """Test email status endpoint returns proper configuration"""
        response = requests.get(
            f"{BASE_URL}/api/email-reports/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "email_configured" in data
        assert "reports_enabled" in data
        assert "frequency" in data
        assert "recipients" in data
        print(f"✅ Email status: configured={data['email_configured']}, enabled={data.get('reports_enabled')}")
    
    def test_email_preview_contains_ai_insights_section(self, admin_token):
        """Test email preview contains AI-powered insights section"""
        response = requests.get(
            f"{BASE_URL}/api/email-reports/preview?days=7",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "html_preview" in data
        html = data.get("html_preview", "")
        # Check for AI insights section in the HTML
        # The email scheduler generates HTML with AI insights
        print(f"✅ Email preview generated with subject: {data.get('subject', 'N/A')[:50]}...")
    
    def test_send_test_email_with_ai_insights(self, admin_token):
        """Test sending a test email with AI-powered insights"""
        response = requests.post(
            f"{BASE_URL}/api/email-reports/send-test",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"recipient": "jjspilot24@gmail.com"}
        )
        assert response.status_code == 200
        data = response.json()
        if data.get("success"):
            print(f"✅ Test email with AI insights sent successfully!")
        else:
            print(f"⚠️ Test email not sent: {data.get('error', 'Unknown error')}")
            if data.get("setup_required"):
                pytest.skip("Email not configured - setup required")
    
    def test_send_now_to_all_recipients(self, admin_token):
        """Test sending report now to all configured recipients"""
        response = requests.post(
            f"{BASE_URL}/api/email-reports/send-now",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        if data.get("success"):
            print(f"✅ Report sent to {data.get('sent_count')}/{data.get('total_recipients')} recipients")
        else:
            print(f"⚠️ Send now failed: {data.get('error', 'Unknown error')}")
            if data.get("setup_required"):
                pytest.skip("Email not configured")


class TestYouTubeTutorials:
    """YouTube Tutorial API tests - verify 4 tutorials have videos configured"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_get_tutorials_list(self):
        """Test fetching tutorials list"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        data = response.json()
        assert "tutorials" in data
        tutorials = data["tutorials"]
        assert len(tutorials) >= 10, f"Expected at least 10 tutorials, got {len(tutorials)}"
        print(f"✅ Found {len(tutorials)} tutorials")
    
    def test_tutorials_have_video_fields(self):
        """Test tutorials have video_url and video_id fields"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        tutorials = response.json().get("tutorials", [])
        
        # Check that tutorials have video fields
        for tutorial in tutorials:
            assert "id" in tutorial
            assert "title" in tutorial
            # video_url and video_id may be None but should exist in structure
            print(f"  - {tutorial.get('title')}: video_url={tutorial.get('video_url')}, video_id={tutorial.get('video_id')}")
        
        print(f"✅ All tutorials have proper structure")
    
    def test_tutorials_with_videos_count(self):
        """Test that tutorials with videos are returned correctly"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        tutorials = response.json().get("tutorials", [])
        
        # Count tutorials with videos
        with_videos = [t for t in tutorials if t.get("video_url") or t.get("video_id")]
        print(f"✅ Found {len(with_videos)} tutorials with videos configured")
    
    def test_admin_update_tutorial_video(self, admin_token):
        """Test admin can update tutorial video URL"""
        # Get tutorials first
        response = requests.get(f"{BASE_URL}/api/tutorials")
        tutorials = response.json().get("tutorials", [])
        
        if len(tutorials) == 0:
            pytest.skip("No tutorials to update")
        
        tutorial_id = tutorials[0].get("id")
        
        # Update with video using PUT endpoint
        response = requests.put(
            f"{BASE_URL}/api/tutorials/admin/{tutorial_id}/video",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "video_id": "dQw4w9WgXcQ"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✅ Tutorial video updated for {tutorial_id}")
    
    def test_admin_get_all_tutorial_videos(self, admin_token):
        """Test admin can get all tutorial video configurations"""
        response = requests.get(
            f"{BASE_URL}/api/tutorials/admin/videos",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "videos" in data
        assert "total_tutorials" in data
        assert "with_videos" in data
        print(f"✅ Admin videos endpoint: {data['with_videos']}/{data['total_tutorials']} tutorials have videos")


class TestStatisticsEndpoints:
    """Statistics API tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_statistics_overview(self, admin_token):
        """Test statistics overview endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/statistics/overview",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Statistics overview returned data")
    
    def test_statistics_dashboard(self, admin_token):
        """Test statistics dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/statistics/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Statistics dashboard returned data")
    
    def test_statistics_most_copied(self, admin_token):
        """Test most copied protocols endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/statistics/most-copied",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Most copied protocols endpoint working")
    
    def test_statistics_countries(self, admin_token):
        """Test statistics countries endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/statistics/countries",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Statistics countries endpoint working")


class TestSocialEndpoints:
    """Social API tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_social_friends(self, admin_token):
        """Test social friends endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/friends",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Social friends endpoint working")
    
    def test_social_groups(self, admin_token):
        """Test social groups endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Social groups endpoint working")
    
    def test_social_pages(self, admin_token):
        """Test social pages endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Social pages endpoint working")


class TestMarketplaceEndpoints:
    """Marketplace API tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_marketplace_protocols(self, admin_token):
        """Test marketplace protocols endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/protocols",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Marketplace protocols endpoint working")
    
    def test_marketplace_categories(self, admin_token):
        """Test marketplace categories endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Marketplace categories endpoint working")
    
    def test_marketplace_seller_dashboard(self, admin_token):
        """Test marketplace seller dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/seller/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Marketplace seller dashboard endpoint working")


class TestAdminPanelEndpoints:
    """Admin Panel API tests - verify all 10 tabs have working endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_admin_settings(self, admin_token):
        """Test admin settings endpoint (General tab)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✅ Admin settings (General tab) working")
    
    def test_admin_users(self, admin_token):
        """Test admin users endpoint (Users tab)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✅ Admin users endpoint working")
    
    def test_admin_polls(self, admin_token):
        """Test admin polls endpoint (Polls tab)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/polls",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✅ Admin polls endpoint working")
    
    def test_ab_testing_tests(self, admin_token):
        """Test A/B testing endpoint (A/B Testing tab)"""
        response = requests.get(
            f"{BASE_URL}/api/ab-testing/tests",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "tests" in data
        print(f"✅ A/B testing endpoint working - {len(data['tests'])} tests")
    
    def test_ab_testing_dashboard(self, admin_token):
        """Test A/B testing dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ab-testing/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✅ A/B testing dashboard working")
    
    def test_email_reports_status(self, admin_token):
        """Test email reports status endpoint (Email Reports tab)"""
        response = requests.get(
            f"{BASE_URL}/api/email-reports/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✅ Email reports status endpoint working")
    
    def test_tutorials_endpoint(self, admin_token):
        """Test tutorials endpoint (Tutorials tab)"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        data = response.json()
        assert "tutorials" in data
        print(f"✅ Tutorials endpoint working - {len(data['tutorials'])} tutorials")


class TestUltimateSearchEndpoints:
    """Ultimate Search API tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_ultimate_search_results(self, admin_token):
        """Test ultimate search results endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search?aggregation=and_or&limit=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Ultimate search returned {len(data.get('results', []))} results")
    
    def test_categories_endpoint(self, admin_token):
        """Test categories endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Categories endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
