"""
Test P0 Features for InfoPilot Explorer
Tests: Document Types, Stripe Integration, App Downloads, Legal Pages, Protocol Templates, Enhanced Map
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
SESSION_TOKEN = "test_session_1769221186289"

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SESSION_TOKEN}"
    })
    return session

@pytest.fixture
def public_client():
    """Public requests session (no auth)"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestDocumentTypes:
    """Test Document Types API - Feature 1"""
    
    def test_get_document_types(self, api_client):
        """GET /api/document-types - Returns all document types for filtering"""
        response = api_client.get(f"{BASE_URL}/api/document-types")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "types" in data, "Response should contain 'types' key"
        assert len(data["types"]) == 8, f"Expected 8 document types, got {len(data['types'])}"
        
        # Verify expected document types exist
        type_ids = [t["id"] for t in data["types"]]
        expected_types = ["informative_phd", "informative", "news_article", "blog", "forum", 
                         "personal_report_organic", "personal_report_collected", "infopilot_exclusive"]
        for expected in expected_types:
            assert expected in type_ids, f"Missing document type: {expected}"
        
        # Verify structure
        for doc_type in data["types"]:
            assert "id" in doc_type
            assert "name" in doc_type
            assert "description" in doc_type
        
        print(f"✓ Document types API returns {len(data['types'])} types correctly")


class TestStripeIntegration:
    """Test Stripe Payment Integration - Feature 2"""
    
    def test_get_packages_with_stripe_enabled(self, api_client):
        """GET /api/payments/packages - Returns packages with stripe_enabled flag"""
        response = api_client.get(f"{BASE_URL}/api/payments/packages")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "packages" in data, "Response should contain 'packages' key"
        assert "stripe_enabled" in data, "Response should contain 'stripe_enabled' flag"
        
        # Verify stripe_enabled is boolean
        assert isinstance(data["stripe_enabled"], bool), "stripe_enabled should be boolean"
        print(f"✓ Stripe enabled: {data['stripe_enabled']}")
        
        # Verify packages structure
        assert len(data["packages"]) >= 3, f"Expected at least 3 packages, got {len(data['packages'])}"
        
        for pkg in data["packages"]:
            assert "id" in pkg
            assert "name" in pkg
            assert "price" in pkg
            assert "period" in pkg
        
        print(f"✓ Packages API returns {len(data['packages'])} packages with stripe_enabled={data['stripe_enabled']}")
    
    def test_checkout_session_endpoint_exists(self, api_client):
        """POST /api/payments/checkout/session - Endpoint exists and requires proper data"""
        # Test that endpoint exists (may fail with 400/422 due to missing data, but not 404)
        response = api_client.post(f"{BASE_URL}/api/payments/checkout/session", json={
            "origin_url": "https://infopilot-hub-1.preview.emergentagent.com",
            "package_type": "monthly"
        })
        
        # Should not be 404 - endpoint exists
        assert response.status_code != 404, "Checkout session endpoint should exist"
        
        # If Stripe is configured, should return URL or error
        if response.status_code == 200:
            data = response.json()
            assert "url" in data or "session_id" in data, "Success response should contain url or session_id"
            print(f"✓ Checkout session created successfully")
        elif response.status_code == 503:
            print(f"✓ Checkout endpoint exists but Stripe not available (503)")
        else:
            print(f"✓ Checkout endpoint exists, returned {response.status_code}")


class TestAppDownloads:
    """Test App Download Links API - Feature 3"""
    
    def test_get_app_downloads(self, public_client):
        """GET /api/app-downloads - Returns download links for all platforms"""
        response = public_client.get(f"{BASE_URL}/api/app-downloads")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify all platforms exist
        assert "android" in data, "Response should contain 'android' key"
        assert "ios" in data, "Response should contain 'ios' key"
        assert "desktop" in data, "Response should contain 'desktop' key"
        assert "browser_extension" in data, "Response should contain 'browser_extension' key"
        
        # Verify Android structure
        assert "url" in data["android"], "Android should have URL"
        assert "play.google.com" in data["android"]["url"], "Android URL should be Play Store"
        
        # Verify iOS structure
        assert "url" in data["ios"], "iOS should have URL"
        assert "apps.apple.com" in data["ios"]["url"], "iOS URL should be App Store"
        
        # Verify Desktop structure
        assert "url" in data["desktop"], "Desktop should have URL"
        
        # Verify Browser Extension structure
        assert "url" in data["browser_extension"], "Browser extension should have URL"
        
        print(f"✓ App downloads API returns all 4 platforms correctly")


class TestLegalPages:
    """Test Legal Pages API - Features 4, 5, 6, 7"""
    
    def test_privacy_policy_endpoint(self, public_client):
        """GET /api/legal/privacy-policy - Returns privacy policy with 'First in Flight' content"""
        response = public_client.get(f"{BASE_URL}/api/legal/privacy-policy")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "title" in data, "Response should contain 'title'"
        assert "content" in data, "Response should contain 'content'"
        assert "last_updated" in data, "Response should contain 'last_updated'"
        
        # Verify 'First in Flight' branding
        assert "First in Flight" in data["content"], "Privacy policy should contain 'First in Flight' messaging"
        assert "Privacy Policy" in data["title"], "Title should be Privacy Policy"
        
        print(f"✓ Privacy Policy API returns document with 'First in Flight' content")
    
    def test_terms_of_service_endpoint(self, public_client):
        """GET /api/legal/terms-of-service - Returns terms with copyright info"""
        response = public_client.get(f"{BASE_URL}/api/legal/terms-of-service")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "title" in data, "Response should contain 'title'"
        assert "content" in data, "Response should contain 'content'"
        assert "last_updated" in data, "Response should contain 'last_updated'"
        
        # Verify copyright info
        assert "Copyright" in data["content"] or "copyright" in data["content"].lower(), \
            "Terms should contain copyright information"
        assert "Top Pilot Enterprises" in data["content"], "Terms should mention Top Pilot Enterprises"
        
        print(f"✓ Terms of Service API returns document with copyright info")
    
    def test_invalid_legal_document(self, public_client):
        """GET /api/legal/invalid - Returns 404 for invalid document type"""
        response = public_client.get(f"{BASE_URL}/api/legal/invalid-document")
        assert response.status_code == 404, f"Expected 404 for invalid document, got {response.status_code}"
        print(f"✓ Invalid legal document returns 404 correctly")


class TestProtocolTemplates:
    """Test Protocol Templates CRUD - Feature 6"""
    
    def test_get_templates(self, api_client):
        """GET /api/templates - Returns protocol templates list"""
        response = api_client.get(f"{BASE_URL}/api/templates")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "templates" in data, "Response should contain 'templates' key"
        assert isinstance(data["templates"], list), "Templates should be a list"
        
        print(f"✓ Templates API returns {len(data['templates'])} templates")
    
    def test_create_template(self, api_client):
        """POST /api/templates - Creates a new protocol template"""
        template_data = {
            "name": "TEST_Template_" + str(os.urandom(4).hex()),
            "description": "Test template for automated testing",
            "protocol_string": "(test or testing) & (automation)+",
            "category": "Testing",
            "is_public": False
        }
        
        response = api_client.post(f"{BASE_URL}/api/templates", json=template_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "template_id" in data, "Response should contain 'template_id'"
        assert data["name"] == template_data["name"], "Name should match"
        assert data["protocol_string"] == template_data["protocol_string"], "Protocol string should match"
        
        # Verify by GET
        template_id = data["template_id"]
        get_response = api_client.get(f"{BASE_URL}/api/templates/{template_id}")
        assert get_response.status_code == 200, f"GET template failed: {get_response.status_code}"
        
        print(f"✓ Template created and verified: {template_id}")
        
        # Cleanup - delete the template
        delete_response = api_client.delete(f"{BASE_URL}/api/templates/{template_id}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.status_code}"
        print(f"✓ Template deleted successfully")


class TestEnhancedMap:
    """Test Enhanced Map Data API - Feature 5"""
    
    def test_map_data_detailed_endpoint(self, api_client):
        """GET /api/stats/map-data-detailed - Returns locations with results"""
        response = api_client.get(f"{BASE_URL}/api/stats/map-data-detailed")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "locations" in data, "Response should contain 'locations' key"
        assert "total_locations" in data, "Response should contain 'total_locations'"
        assert "total_results" in data, "Response should contain 'total_results'"
        
        assert isinstance(data["locations"], list), "Locations should be a list"
        
        # If there are locations, verify structure
        if len(data["locations"]) > 0:
            loc = data["locations"][0]
            assert "location" in loc, "Each location should have 'location' object"
            assert "count" in loc, "Each location should have 'count'"
        
        print(f"✓ Map data detailed API returns {data['total_locations']} locations with {data['total_results']} results")


class TestHealthAndBasics:
    """Basic health checks"""
    
    def test_api_health(self, public_client):
        """GET /api/health - API is healthy"""
        response = public_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "healthy", "Status should be healthy"
        print(f"✓ API health check passed")
    
    def test_api_root(self, public_client):
        """GET /api/ - Returns API info"""
        response = public_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "name" in data, "Response should contain 'name'"
        assert "InfoPilot" in data["name"], "API name should contain InfoPilot"
        print(f"✓ API root returns: {data['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
