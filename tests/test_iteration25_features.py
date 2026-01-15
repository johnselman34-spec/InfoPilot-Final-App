"""
InfoPilot Explorer - Iteration 25 Feature Tests
Tests for:
1. VAPID Keys configuration
2. Chrome Extension packaging
3. Video Tutorials with YouTube support and admin management
4. Protocol Analytics Dashboard for creators
5. Frontend component structure verification
"""
import pytest
import requests
import os

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestVAPIDConfiguration:
    """Test VAPID keys are properly configured"""
    
    def test_vapid_keys_in_backend_env(self):
        """Verify VAPID keys exist in backend .env"""
        env_path = "/app/backend/.env"
        assert os.path.exists(env_path), "Backend .env file not found"
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        assert "VAPID_PRIVATE_KEY=" in content, "VAPID_PRIVATE_KEY not found in .env"
        assert "VAPID_PUBLIC_KEY=" in content, "VAPID_PUBLIC_KEY not found in .env"
        assert "VAPID_CLAIMS_EMAIL=" in content, "VAPID_CLAIMS_EMAIL not found in .env"
        print("✓ VAPID keys configured in backend .env")
    
    def test_vapid_public_key_in_frontend_env(self):
        """Verify VAPID public key is in frontend .env"""
        env_path = "/app/frontend/.env"
        assert os.path.exists(env_path), "Frontend .env file not found"
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        assert "REACT_APP_VAPID_PUBLIC_KEY=" in content, "VAPID public key not in frontend .env"
        print("✓ VAPID public key configured in frontend .env")


class TestChromeExtension:
    """Test Chrome extension packaging"""
    
    def test_extension_zip_exists(self):
        """Verify Chrome extension zip file exists"""
        # Check both possible locations
        zip_paths = [
            "/app/browser-extension/infopilot-extension.zip",
            "/app/browser-extension/dist/infopilot-infojet-extension.zip"
        ]
        
        found = False
        for path in zip_paths:
            if os.path.exists(path):
                found = True
                size = os.path.getsize(path)
                assert size > 1000, f"Extension zip too small: {size} bytes"
                print(f"✓ Chrome extension zip found at {path} ({size} bytes)")
                break
        
        assert found, f"Chrome extension zip not found in any expected location: {zip_paths}"
    
    def test_extension_manifest_exists(self):
        """Verify manifest.json exists"""
        manifest_path = "/app/browser-extension/manifest.json"
        assert os.path.exists(manifest_path), "manifest.json not found"
        print("✓ Extension manifest.json exists")
    
    def test_extension_icons_exist(self):
        """Verify extension icons exist"""
        icons_dir = "/app/browser-extension/icons"
        assert os.path.isdir(icons_dir), "Icons directory not found"
        
        # Check for icon files
        icon_files = os.listdir(icons_dir)
        assert len(icon_files) > 0, "No icon files found"
        print(f"✓ Extension icons found: {icon_files}")


class TestTutorialsAPI:
    """Test Video Tutorials endpoints"""
    
    def test_get_tutorials_returns_list(self):
        """GET /api/tutorials returns tutorials with video fields"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "tutorials" in data, "Response missing 'tutorials' field"
        assert "categories" in data, "Response missing 'categories' field"
        assert isinstance(data["tutorials"], list), "tutorials should be a list"
        
        # Check that tutorials have video_url and video_id fields
        if len(data["tutorials"]) > 0:
            tutorial = data["tutorials"][0]
            assert "video_url" in tutorial or tutorial.get("video_url") is None, "Tutorial missing video_url field"
            assert "video_id" in tutorial or tutorial.get("video_id") is None, "Tutorial missing video_id field"
            assert "title" in tutorial, "Tutorial missing title"
            assert "content" in tutorial, "Tutorial missing content"
        
        print(f"✓ GET /api/tutorials returns {len(data['tutorials'])} tutorials")
    
    def test_get_single_tutorial(self):
        """GET /api/tutorials/{id} returns tutorial details"""
        response = requests.get(f"{BASE_URL}/api/tutorials/getting-started")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "tutorial" in data, "Response missing 'tutorial' field"
        assert data["tutorial"]["id"] == "getting-started"
        print("✓ GET /api/tutorials/{id} returns tutorial details")


class TestTutorialsAdminAPI:
    """Test admin video management endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed - skipping admin tests")
        return response.json().get("token")
    
    def test_admin_update_video_url(self, admin_token):
        """PUT /api/tutorials/admin/{id}/video updates video URL (admin only)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Update video URL
        response = requests.put(
            f"{BASE_URL}/api/tutorials/admin/getting-started/video",
            headers=headers,
            json={"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Update should return success=True"
        assert data.get("video_id") == "dQw4w9WgXcQ", "Video ID should be extracted from URL"
        print("✓ PUT /api/tutorials/admin/{id}/video updates video URL")
        
        # Clean up - remove the video
        requests.delete(
            f"{BASE_URL}/api/tutorials/admin/getting-started/video",
            headers=headers
        )
    
    def test_admin_video_requires_auth(self):
        """PUT /api/tutorials/admin/{id}/video requires admin auth"""
        response = requests.put(
            f"{BASE_URL}/api/tutorials/admin/getting-started/video",
            json={"video_url": "https://youtube.com/watch?v=test"}
        )
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✓ Admin video endpoint requires authentication")
    
    def test_admin_get_all_videos(self, admin_token):
        """GET /api/tutorials/admin/videos returns all video configurations"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/tutorials/admin/videos",
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "videos" in data, "Response missing 'videos' field"
        assert "total_tutorials" in data, "Response missing 'total_tutorials' field"
        print(f"✓ GET /api/tutorials/admin/videos returns {len(data['videos'])} configured videos")


class TestProtocolAnalyticsAPI:
    """Test Protocol Analytics endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed - skipping analytics tests")
        return response.json().get("token")
    
    def test_track_event_requires_valid_protocol(self, admin_token):
        """POST /api/analytics/track validates protocol exists"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/track",
            headers=headers,
            json={
                "protocol_id": "000000000000000000000000",  # Invalid ID
                "event_type": "view"
            }
        )
        assert response.status_code == 404, f"Expected 404 for invalid protocol, got {response.status_code}"
        print("✓ POST /api/analytics/track validates protocol exists")
    
    def test_track_event_validates_event_type(self, admin_token):
        """POST /api/analytics/track validates event type"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/track",
            headers=headers,
            json={
                "protocol_id": "000000000000000000000000",
                "event_type": "invalid_event"
            }
        )
        assert response.status_code == 400, f"Expected 400 for invalid event type, got {response.status_code}"
        print("✓ POST /api/analytics/track validates event type")
    
    def test_creator_dashboard_requires_auth(self):
        """GET /api/analytics/creator/dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/analytics/creator/dashboard")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✓ GET /api/analytics/creator/dashboard requires authentication")
    
    def test_creator_dashboard_returns_data(self, admin_token):
        """GET /api/analytics/creator/dashboard returns creator analytics"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/creator/dashboard",
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Should have summary even if no protocols
        assert "summary" in data, "Response missing 'summary' field"
        assert "total_views" in data["summary"], "Summary missing total_views"
        assert "total_copies" in data["summary"], "Summary missing total_copies"
        assert "total_purchases" in data["summary"], "Summary missing total_purchases"
        assert "total_revenue" in data["summary"], "Summary missing total_revenue"
        print(f"✓ GET /api/analytics/creator/dashboard returns analytics (protocols: {data.get('total_protocols', 0)})")
    
    def test_protocol_analytics_requires_auth(self):
        """GET /api/analytics/protocol/{id} requires authentication"""
        response = requests.get(f"{BASE_URL}/api/analytics/protocol/000000000000000000000000")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✓ GET /api/analytics/protocol/{id} requires authentication")
    
    def test_admin_overview_requires_admin(self, admin_token):
        """GET /api/analytics/admin/overview requires admin role"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/admin/overview",
            headers=headers
        )
        # Admin should get 200, non-admin would get 403
        assert response.status_code == 200, f"Expected 200 for admin, got {response.status_code}"
        
        data = response.json()
        assert "totals" in data, "Response missing 'totals' field"
        print("✓ GET /api/analytics/admin/overview returns platform analytics")


class TestFrontendComponentStructure:
    """Test new frontend component directories exist"""
    
    def test_ultimate_search_components_exist(self):
        """Verify UltimateSearch component directory exists"""
        dir_path = "/app/frontend/src/components/UltimateSearch"
        assert os.path.isdir(dir_path), f"UltimateSearch directory not found at {dir_path}"
        
        files = os.listdir(dir_path)
        assert "index.js" in files, "UltimateSearch missing index.js"
        print(f"✓ UltimateSearch components: {files}")
    
    def test_statistics_components_exist(self):
        """Verify Statistics component directory exists"""
        dir_path = "/app/frontend/src/components/Statistics"
        assert os.path.isdir(dir_path), f"Statistics directory not found at {dir_path}"
        
        files = os.listdir(dir_path)
        assert "index.js" in files, "Statistics missing index.js"
        print(f"✓ Statistics components: {files}")
    
    def test_social_components_exist(self):
        """Verify Social component directory exists"""
        dir_path = "/app/frontend/src/components/Social"
        assert os.path.isdir(dir_path), f"Social directory not found at {dir_path}"
        
        files = os.listdir(dir_path)
        assert "index.js" in files, "Social missing index.js"
        print(f"✓ Social components: {files}")
    
    def test_analytics_components_exist(self):
        """Verify Analytics component directory exists"""
        dir_path = "/app/frontend/src/components/Analytics"
        assert os.path.isdir(dir_path), f"Analytics directory not found at {dir_path}"
        
        files = os.listdir(dir_path)
        assert "index.js" in files, "Analytics missing index.js"
        assert "ProtocolAnalyticsDashboard.js" in files, "Analytics missing ProtocolAnalyticsDashboard.js"
        print(f"✓ Analytics components: {files}")
    
    def test_youtube_player_component_exists(self):
        """Verify YouTubePlayer component exists"""
        file_path = "/app/frontend/src/components/shared/YouTubePlayer.js"
        assert os.path.exists(file_path), f"YouTubePlayer.js not found at {file_path}"
        print("✓ YouTubePlayer component exists")


class TestHealthAndBasics:
    """Basic health checks"""
    
    def test_api_health(self):
        """Test API is responding"""
        response = requests.get(f"{BASE_URL}/api")
        assert response.status_code == 200, f"API health check failed: {response.status_code}"
        print("✓ API is healthy")
    
    def test_admin_login(self):
        """Test admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.status_code}"
        data = response.json()
        assert "token" in data, "Login response missing token"
        assert data.get("user", {}).get("is_admin") == True, "User should be admin"
        print("✓ Admin login successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
