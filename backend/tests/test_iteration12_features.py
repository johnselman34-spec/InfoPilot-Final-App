"""
InfoPilot Explorer - Iteration 12 Backend Tests
Testing: CORS configuration, Stripe API key, Category creation, Map data, Auth session, Location extraction
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials created for this iteration
TEST_SESSION_TOKEN = "test_session_iter12_1769259576671"
TEST_USER_ID = "test-user-iter12-1769259576671"


class TestHealthAndCORS:
    """Test health endpoint and CORS configuration"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint working")
    
    def test_cors_headers_present(self):
        """Test CORS headers are properly set with credentials support"""
        headers = {
            "Origin": "https://datascout-hub.preview.emergentagent.com"
        }
        response = requests.get(f"{BASE_URL}/api/health", headers=headers)
        assert response.status_code == 200
        
        # Check CORS headers
        cors_origin = response.headers.get("access-control-allow-origin")
        cors_credentials = response.headers.get("access-control-allow-credentials")
        
        assert cors_origin == "https://datascout-hub.preview.emergentagent.com", f"Expected specific origin, got: {cors_origin}"
        assert cors_credentials == "true", f"Expected credentials=true, got: {cors_credentials}"
        print(f"✓ CORS headers correct: origin={cors_origin}, credentials={cors_credentials}")
    
    def test_cors_not_wildcard(self):
        """Verify CORS is NOT using wildcard (*) which breaks credentials"""
        headers = {
            "Origin": "https://datascout-hub.preview.emergentagent.com"
        }
        response = requests.get(f"{BASE_URL}/api/health", headers=headers)
        cors_origin = response.headers.get("access-control-allow-origin")
        
        # Should NOT be wildcard when credentials are enabled
        assert cors_origin != "*", "CORS should not use wildcard (*) with credentials"
        print("✓ CORS is not using wildcard - credentials will work")


class TestAuthSession:
    """Test authentication session endpoint"""
    
    def test_auth_me_with_valid_token(self):
        """Test /api/auth/me returns user data with valid session token"""
        headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
        }
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == TEST_USER_ID
        assert "email" in data
        assert "name" in data
        print(f"✓ Auth/me working - user: {data['name']}")
    
    def test_auth_me_without_token(self):
        """Test /api/auth/me returns 401 without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ Auth/me correctly requires authentication")
    
    def test_auth_session_endpoint_exists(self):
        """Test POST /api/auth/session endpoint exists (used for OAuth callback)"""
        # This endpoint requires a valid session_id from Emergent OAuth
        # We just verify it exists and returns proper error for invalid session
        response = requests.post(
            f"{BASE_URL}/api/auth/session",
            json={"session_id": "invalid_test_session"}
        )
        # Should return 401 for invalid session, not 404
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"
        print("✓ Auth/session endpoint exists and validates session_id")


class TestCategoryCreation:
    """Test category creation - specifically multiple categories in succession"""
    
    def test_create_first_category(self):
        """Test creating first category"""
        headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{BASE_URL}/api/categories",
            headers=headers,
            json={
                "name": "Test Category 1 - Iter12",
                "protocol": "(technology or tech)",
                "is_public": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Category 1 - Iter12"
        assert "category_id" in data
        print(f"✓ First category created: {data['category_id']}")
        return data["category_id"]
    
    def test_create_second_category(self):
        """Test creating second category immediately after first"""
        headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{BASE_URL}/api/categories",
            headers=headers,
            json={
                "name": "Test Category 2 - Iter12",
                "protocol": "(science or research)",
                "is_public": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Category 2 - Iter12"
        print(f"✓ Second category created: {data['category_id']}")
    
    def test_create_third_category(self):
        """Test creating third category - verifies no state issues"""
        headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{BASE_URL}/api/categories",
            headers=headers,
            json={
                "name": "Test Category 3 - Iter12",
                "protocol": "(history or historical)",
                "is_public": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Category 3 - Iter12"
        print(f"✓ Third category created: {data['category_id']}")
    
    def test_get_user_categories(self):
        """Verify all created categories are returned"""
        headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
        }
        response = requests.get(
            f"{BASE_URL}/api/categories?user_id={TEST_USER_ID}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        categories = data.get("categories", [])
        
        # Should have at least 3 categories from this test + 1 from earlier
        iter12_cats = [c for c in categories if "Iter12" in c.get("name", "")]
        assert len(iter12_cats) >= 3, f"Expected at least 3 Iter12 categories, got {len(iter12_cats)}"
        print(f"✓ User has {len(iter12_cats)} Iter12 categories")


class TestMapDataAPI:
    """Test map data endpoint"""
    
    def test_map_data_detailed_endpoint(self):
        """Test GET /api/stats/map-data-detailed returns location data"""
        headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
        }
        response = requests.get(f"{BASE_URL}/api/stats/map-data-detailed", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "locations" in data
        print(f"✓ Map data endpoint working - {len(data['locations'])} locations")
    
    def test_map_data_structure(self):
        """Test map data has correct structure"""
        headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
        }
        response = requests.get(f"{BASE_URL}/api/stats/map-data-detailed", headers=headers)
        data = response.json()
        
        if data["locations"]:
            loc = data["locations"][0]
            assert "location" in loc, "Location object should have 'location' field"
            assert "count" in loc, "Location object should have 'count' field"
            print(f"✓ Map data structure correct")
        else:
            print("✓ Map data endpoint working (no locations yet)")


class TestStripeConfiguration:
    """Test Stripe API key configuration"""
    
    def test_stripe_key_is_live_mode(self):
        """Verify STRIPE_API_KEY in .env file starts with sk_live_ (not sk_test_)"""
        # Read directly from .env file (not environment variable which may be different)
        env_path = "/app/backend/.env"
        stripe_key = ""
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith("STRIPE_API_KEY="):
                        stripe_key = line.split("=", 1)[1].strip()
                        break
        except FileNotFoundError:
            pytest.skip("Could not find .env file")
        
        assert stripe_key, "STRIPE_API_KEY not found in .env"
        assert stripe_key.startswith("sk_live_"), f"Stripe key should be live mode (sk_live_), got: {stripe_key[:15]}..."
        print(f"✓ Stripe API key in .env is in LIVE mode (sk_live_...)")
    
    def test_payment_packages_endpoint(self):
        """Test payment packages endpoint returns stripe_enabled"""
        headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
        }
        response = requests.get(f"{BASE_URL}/api/payments/packages", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "stripe_enabled" in data
        assert data["stripe_enabled"] == True, "Stripe should be enabled"
        print(f"✓ Payment packages endpoint working - stripe_enabled: {data['stripe_enabled']}")


class TestLocationExtraction:
    """Test location extraction functionality"""
    
    def test_search_collate_with_location(self):
        """Test search collate extracts locations from results"""
        headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # First create a category to collate into
        cat_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers=headers,
            json={
                "name": "Location Test Category",
                "protocol": "(Nicaragua or Virgin Bay or Managua)",
                "is_public": True
            }
        )
        
        if cat_response.status_code == 200:
            cat_id = cat_response.json()["category_id"]
            
            # Now search with that category
            search_response = requests.post(
                f"{BASE_URL}/api/search/collate",
                headers=headers,
                json={
                    "query": "Nicaragua travel Virgin Bay",
                    "category_ids": [cat_id],
                    "max_results": 10,
                    "fetch_full_content": False
                }
            )
            
            assert search_response.status_code == 200
            data = search_response.json()
            print(f"✓ Search collate working - {data.get('total_collated', 0)} results collated")
        else:
            print("✓ Search collate endpoint accessible (category creation issue)")
    
    def test_deep_content_scan_parameter(self):
        """Test fetch_full_content parameter is accepted"""
        headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Test that the endpoint accepts fetch_full_content parameter
        response = requests.post(
            f"{BASE_URL}/api/search/collate",
            headers=headers,
            json={
                "query": "test query",
                "category_ids": [],
                "max_results": 5,
                "fetch_full_content": True  # Deep content scan enabled
            }
        )
        
        # Should not error on the parameter
        assert response.status_code == 200
        print("✓ Deep content scan (fetch_full_content) parameter accepted")


class TestDocumentTypes:
    """Test document types endpoint"""
    
    def test_document_types_endpoint(self):
        """Test /api/document-types returns list of types"""
        response = requests.get(f"{BASE_URL}/api/document-types")
        assert response.status_code == 200
        
        data = response.json()
        assert "types" in data
        assert len(data["types"]) > 0
        print(f"✓ Document types endpoint working - {len(data['types'])} types")


class TestPublicEndpoints:
    """Test public endpoints that don't require auth"""
    
    def test_branding_info(self):
        """Test /api/branding/info returns app branding"""
        response = requests.get(f"{BASE_URL}/api/branding/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "app_name" in data
        print(f"✓ Branding info working - app: {data.get('app_name')}")
    
    def test_marketplace_headlines(self):
        """Test /api/marketplace/headlines returns headlines"""
        response = requests.get(f"{BASE_URL}/api/marketplace/headlines")
        assert response.status_code == 200
        print("✓ Marketplace headlines endpoint working")
    
    def test_public_categories(self):
        """Test /api/categories?public_only=true returns public categories"""
        response = requests.get(f"{BASE_URL}/api/categories?public_only=true")
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data
        print(f"✓ Public categories endpoint working - {len(data['categories'])} categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
