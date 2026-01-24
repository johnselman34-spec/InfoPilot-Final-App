"""
Test suite for InfoPilot Explorer - Iteration 8 Features
Tests: Heatmaps, Collaborative Sessions, Protocol Versioning, App Branding
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from setup
SESSION_TOKEN = "test_session_1769226222270"
USER_ID = "test-user-1769226222270"


@pytest.fixture
def api_client():
    """Shared requests session with auth"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    session.cookies.set("session_token", SESSION_TOKEN)
    return session


@pytest.fixture
def public_client():
    """Requests session without auth for public endpoints"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestBrandingEndpoints:
    """App Branding endpoint tests - PUBLIC endpoints"""
    
    def test_branding_info_returns_app_info(self, public_client):
        """Test /api/branding/info returns app info with tagline"""
        response = public_client.get(f"{BASE_URL}/api/branding/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "app_name" in data
        assert data["app_name"] == "InfoPilot Explorer"
        assert "tagline" in data
        assert "First in Flight" in data["tagline"]
        assert "company" in data
        assert data["company"] == "Top Pilot Enterprises, Inc."
        assert "ceo" in data
        assert data["ceo"] == "John Selman"
        assert "contact" in data
        assert "icon_description" in data
        assert "app_stores" in data
        assert "slogan_variants" in data
        assert "legal_notices" in data
    
    def test_branding_icons_returns_fa18c_and_s3_viking(self, public_client):
        """Test /api/branding/icons returns FA-18C Hornet and S-3 Viking"""
        response = public_client.get(f"{BASE_URL}/api/branding/icons")
        assert response.status_code == 200
        
        data = response.json()
        assert "primary_icon" in data
        assert data["primary_icon"]["name"] == "FA-18C Hornet"
        assert "F/A-18C Hornet" in data["primary_icon"]["description"]
        
        assert "secondary_icon" in data
        assert data["secondary_icon"]["name"] == "S-3 Viking"
        assert "S-3 Viking" in data["secondary_icon"]["description"]
        
        assert "favicon" in data
        assert "app_store_icons" in data
        assert "ios" in data["app_store_icons"]
        assert "android" in data["app_store_icons"]


class TestHeatmapEndpoints:
    """Heatmap endpoint tests - AUTHENTICATED endpoints"""
    
    def test_activity_heatmap_returns_7x24_grid(self, api_client):
        """Test /api/heatmaps/activity returns activity heatmap data"""
        response = api_client.get(f"{BASE_URL}/api/heatmaps/activity?period=month")
        assert response.status_code == 200
        
        data = response.json()
        assert "period" in data
        assert data["period"] == "month"
        assert "heatmap" in data
        assert len(data["heatmap"]) == 7  # 7 days
        assert all(len(row) == 24 for row in data["heatmap"])  # 24 hours each
        assert "days" in data
        assert len(data["days"]) == 7
        assert "hours" in data
        assert len(data["hours"]) == 24
        assert "max_value" in data
    
    def test_activity_heatmap_week_period(self, api_client):
        """Test activity heatmap with week period"""
        response = api_client.get(f"{BASE_URL}/api/heatmaps/activity?period=week")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "week"
    
    def test_activity_heatmap_year_period(self, api_client):
        """Test activity heatmap with year period"""
        response = api_client.get(f"{BASE_URL}/api/heatmaps/activity?period=year")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "year"
    
    def test_location_heatmap_returns_locations(self, api_client):
        """Test /api/heatmaps/location returns location heatmap"""
        response = api_client.get(f"{BASE_URL}/api/heatmaps/location")
        assert response.status_code == 200
        
        data = response.json()
        assert "locations" in data
        assert isinstance(data["locations"], list)
    
    def test_domain_heatmap_returns_domains(self, api_client):
        """Test /api/heatmaps/domain returns domain heatmap"""
        response = api_client.get(f"{BASE_URL}/api/heatmaps/domain")
        assert response.status_code == 200
        
        data = response.json()
        assert "domains" in data
        assert isinstance(data["domains"], list)
    
    def test_heatmap_requires_auth(self, public_client):
        """Test heatmap endpoints require authentication"""
        response = public_client.get(f"{BASE_URL}/api/heatmaps/activity")
        assert response.status_code == 401


class TestCollaborativeSessionsEndpoints:
    """Collaborative Sessions endpoint tests"""
    
    def test_create_collab_session(self, api_client):
        """Test /api/collab/sessions POST creates session"""
        response = api_client.post(
            f"{BASE_URL}/api/collab/sessions",
            json={"name": "TEST_Collab Session", "description": "Test description"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "session_id" in data
        assert data["name"] == "TEST_Collab Session"
        assert "invite_code" in data
        assert len(data["invite_code"]) == 8  # 8-char uppercase
        assert data["invite_code"].isupper()
        assert "host_id" in data
        assert "participants" in data
        assert len(data["participants"]) >= 1
        assert data["participants"][0]["role"] == "host"
        assert data["is_active"] == True
    
    def test_get_collab_sessions(self, api_client):
        """Test /api/collab/sessions GET returns user sessions"""
        response = api_client.get(f"{BASE_URL}/api/collab/sessions")
        assert response.status_code == 200
        
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
        # Should have at least one session from previous test
        assert len(data["sessions"]) >= 1
    
    def test_join_session_with_invite_code(self, api_client):
        """Test joining session with invite code"""
        # First create a session
        create_response = api_client.post(
            f"{BASE_URL}/api/collab/sessions",
            json={"name": "TEST_Join Session", "description": "For join test"}
        )
        assert create_response.status_code == 200
        invite_code = create_response.json()["invite_code"]
        
        # Join with invite code
        join_response = api_client.post(
            f"{BASE_URL}/api/collab/sessions/join",
            json={"invite_code": invite_code}
        )
        assert join_response.status_code == 200
        data = join_response.json()
        assert data["invite_code"] == invite_code
    
    def test_join_session_invalid_code(self, api_client):
        """Test joining with invalid invite code returns 404"""
        response = api_client.post(
            f"{BASE_URL}/api/collab/sessions/join",
            json={"invite_code": "INVALID1"}
        )
        assert response.status_code == 404
    
    def test_get_specific_session(self, api_client):
        """Test getting a specific session by ID"""
        # First create a session
        create_response = api_client.post(
            f"{BASE_URL}/api/collab/sessions",
            json={"name": "TEST_Specific Session", "description": "For get test"}
        )
        session_id = create_response.json()["session_id"]
        
        # Get specific session
        response = api_client.get(f"{BASE_URL}/api/collab/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
    
    def test_send_message_in_session(self, api_client):
        """Test sending a message in collaborative session"""
        # First create a session
        create_response = api_client.post(
            f"{BASE_URL}/api/collab/sessions",
            json={"name": "TEST_Message Session", "description": "For message test"}
        )
        session_id = create_response.json()["session_id"]
        
        # Send message
        response = api_client.post(
            f"{BASE_URL}/api/collab/sessions/{session_id}/message",
            json={"content": "Hello from test!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message_id" in data
        assert data["content"] == "Hello from test!"
    
    def test_collab_sessions_require_auth(self, public_client):
        """Test collab endpoints require authentication"""
        response = public_client.get(f"{BASE_URL}/api/collab/sessions")
        assert response.status_code == 401


class TestProtocolVersioningEndpoints:
    """Protocol Versioning endpoint tests"""
    
    @pytest.fixture
    def test_category(self, api_client):
        """Create a test category for versioning tests"""
        response = api_client.post(
            f"{BASE_URL}/api/categories",
            json={"name": "TEST_Versioning Protocol", "protocol": "test protocol v1"}
        )
        assert response.status_code == 200
        return response.json()
    
    def test_get_protocol_versions(self, api_client, test_category):
        """Test /api/versioning/protocols/{id}/versions returns versions"""
        category_id = test_category["category_id"]
        response = api_client.get(f"{BASE_URL}/api/versioning/protocols/{category_id}/versions")
        assert response.status_code == 200
        
        data = response.json()
        assert "versions" in data
        assert isinstance(data["versions"], list)
    
    def test_create_protocol_version(self, api_client, test_category):
        """Test POST creates new version"""
        category_id = test_category["category_id"]
        response = api_client.post(
            f"{BASE_URL}/api/versioning/protocols/{category_id}/versions",
            json={"protocol": "test protocol v2", "changelog": "Updated to v2"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "version_id" in data
        assert data["version"] == 1
        assert data["changelog"] == "Updated to v2"
        assert data["category_id"] == category_id
    
    def test_export_protocol(self, api_client, test_category):
        """Test /api/versioning/protocols/export/{id} returns export data"""
        category_id = test_category["category_id"]
        
        # First create a version
        api_client.post(
            f"{BASE_URL}/api/versioning/protocols/{category_id}/versions",
            json={"protocol": "export test v1", "changelog": "For export"}
        )
        
        # Export
        response = api_client.get(f"{BASE_URL}/api/versioning/protocols/export/{category_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "export_version" in data
        assert data["export_version"] == "1.0"
        assert "exported_at" in data
        assert "protocol" in data
        assert "versions" in data
    
    def test_import_protocol(self, api_client):
        """Test /api/versioning/protocols/import accepts export data"""
        import_data = {
            "protocol": {
                "name": "TEST_Imported Protocol",
                "protocol": "imported protocol content"
            },
            "versions": []
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/versioning/protocols/import",
            json=import_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Protocol imported"
        assert "category" in data
        assert data["category"]["name"] == "TEST_Imported Protocol"
    
    def test_revert_protocol_version(self, api_client, test_category):
        """Test reverting to a specific version"""
        category_id = test_category["category_id"]
        
        # Create version 1
        api_client.post(
            f"{BASE_URL}/api/versioning/protocols/{category_id}/versions",
            json={"protocol": "version 1 content", "changelog": "v1"}
        )
        
        # Create version 2
        api_client.post(
            f"{BASE_URL}/api/versioning/protocols/{category_id}/versions",
            json={"protocol": "version 2 content", "changelog": "v2"}
        )
        
        # Revert to version 1
        response = api_client.post(f"{BASE_URL}/api/versioning/protocols/{category_id}/revert/1")
        assert response.status_code == 200
        data = response.json()
        assert "Reverted to version 1" in data["message"]


class TestStatisticsPageStillHas16Aspects:
    """Verify Statistics page still has 16 analysis aspects"""
    
    def test_stats_overview_has_16_aspects(self, api_client):
        """Test /api/stats/overview returns 16+ data fields"""
        response = api_client.get(f"{BASE_URL}/api/stats/overview")
        assert response.status_code == 200
        
        data = response.json()
        # Check for all 16 analysis aspects
        expected_fields = [
            "by_document_type",
            "by_source_type", 
            "by_category",
            "by_country",
            "by_state",
            "by_city",
            "by_region",
            "by_domain",
            "by_tld",
            "by_year",
            "by_age_bracket",
            "by_day_of_week",
            "by_month",
            "by_content_length",
            "by_match_quality",
            "by_reaction"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


class TestNavigationLinks:
    """Test navigation links exist in sidebar"""
    
    def test_heatmaps_route_accessible(self, api_client):
        """Test heatmaps route is accessible"""
        response = api_client.get(f"{BASE_URL}/api/heatmaps/activity")
        assert response.status_code == 200
    
    def test_collab_route_accessible(self, api_client):
        """Test collaborative sessions route is accessible"""
        response = api_client.get(f"{BASE_URL}/api/collab/sessions")
        assert response.status_code == 200
