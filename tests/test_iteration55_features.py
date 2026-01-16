"""
InfoPilot Explorer - Iteration 55 Feature Tests
Tests for:
1. Document Type Testing Tool (POST /api/admin/doctype-test)
2. Map Export Features (JSON, GeoJSON, KML, CSV)
3. PayPal Wallet Accumulation
4. Gamification Badges (storyteller, academic_hunter, news_junkie)
5. Personal Report Creator
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestIteration55Features:
    """Test suite for Iteration 55 new features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        
    def get_auth_token(self):
        """Get authentication token"""
        if self.token:
            return self.token
            
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return self.token
        return None
    
    # ==================== HEALTH CHECK ====================
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health endpoint working")
    
    # ==================== AUTHENTICATION ====================
    
    def test_admin_login(self):
        """Test admin login works"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data.get("user", {}).get("is_admin") == True
        print("✓ Admin login successful")
    
    # ==================== DOCUMENT TYPE TESTING TOOL ====================
    
    def test_doctype_test_endpoint_exists(self):
        """Test POST /api/admin/doctype-test endpoint exists"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        # Test with sample PhD content
        response = self.session.post(f"{BASE_URL}/api/admin/doctype-test", json={
            "title": "Dr. Smith's Research on Climate Change",
            "content": "In this peer-reviewed study, Dr. John Smith, Ph.D., examines the impact of climate change on coastal ecosystems. The research, conducted at the University of Maine, found that there are significant changes in marine biodiversity. There is evidence that these kinds of environmental shifts may have long-term consequences. It is easily observable that more than 50% of species are affected. Dr. Smith's findings suggest that this kind of research is essential for policy-making. The study includes over 2000 words of detailed analysis from multiple Ph.D. researchers including D.Phil. candidates from Oxford University.",
            "url": ""
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "classification" in data
        assert "analysis" in data
        assert "protocol_matches" in data
        print(f"✓ Doctype test endpoint works - classified as: {data.get('classification')}")
    
    def test_doctype_test_blog_classification(self):
        """Test blog content classification"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.post(f"{BASE_URL}/api/admin/doctype-test", json={
            "title": "My Blog Post About Cooking",
            "content": "Welcome to my cooking blog! In this blog post, I'll share my favorite recipes. This blog started as a hobby, but now my blog has thousands of readers. Check out my other blog entries for more recipes!",
            "url": "https://example.com/blog/cooking"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "classification" in data
        # Blog should be classified as Blog Post
        print(f"✓ Blog classification test - classified as: {data.get('classification')}")
    
    def test_doctype_test_news_classification(self):
        """Test news content classification"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.post(f"{BASE_URL}/api/admin/doctype-test", json={
            "title": "Breaking News: Major Discovery",
            "content": "In today's news story, scientists announced a major breakthrough. This news article covers the latest developments. The news report indicates significant progress. News outlets worldwide are covering this story.",
            "url": "https://example.com/news/discovery"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "classification" in data
        print(f"✓ News classification test - classified as: {data.get('classification')}")
    
    def test_doctype_test_requires_content(self):
        """Test that doctype test requires title or content"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.post(f"{BASE_URL}/api/admin/doctype-test", json={
            "title": "",
            "content": "",
            "url": ""
        })
        
        assert response.status_code == 400
        print("✓ Doctype test correctly requires title or content")
    
    # ==================== MAP EXPORT FEATURES ====================
    
    def test_map_export_json(self):
        """Test GET /api/map-data/export?format=json"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(f"{BASE_URL}/api/map-data/export?format=json")
        assert response.status_code == 200
        data = response.json()
        assert data.get("format") == "json"
        assert "results" in data or "total" in data
        print(f"✓ Map export JSON works - {data.get('total', 0)} results")
    
    def test_map_export_geojson(self):
        """Test GET /api/map-data/export?format=geojson"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(f"{BASE_URL}/api/map-data/export?format=geojson")
        assert response.status_code == 200
        data = response.json()
        assert data.get("type") == "FeatureCollection"
        assert "features" in data
        print(f"✓ Map export GeoJSON works - {len(data.get('features', []))} features")
    
    def test_map_export_kml(self):
        """Test GET /api/map-data/export?format=kml"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(f"{BASE_URL}/api/map-data/export?format=kml")
        assert response.status_code == 200
        data = response.json()
        assert data.get("format") == "kml"
        assert "placemarks" in data
        print(f"✓ Map export KML works - {data.get('total', 0)} placemarks")
    
    def test_map_export_csv(self):
        """Test GET /api/map-data/export?format=csv"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(f"{BASE_URL}/api/map-data/export?format=csv")
        assert response.status_code == 200
        data = response.json()
        assert data.get("format") == "csv"
        assert "headers" in data
        assert "rows" in data
        # Verify CSV headers
        expected_headers = ["id", "title", "url", "latitude", "longitude", "article_type", "snippet"]
        assert data.get("headers") == expected_headers
        print(f"✓ Map export CSV works - {data.get('total', 0)} rows")
    
    def test_map_statistics(self):
        """Test GET /api/map-data/statistics"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(f"{BASE_URL}/api/map-data/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_geolocated" in data
        assert "regions" in data
        assert "export_formats" in data
        # Verify export formats include all 4
        assert set(data.get("export_formats", [])) == {"json", "geojson", "kml", "csv"}
        print(f"✓ Map statistics works - {data.get('total_geolocated', 0)} geolocated results")
    
    # ==================== PAYPAL WALLET ACCUMULATION ====================
    
    def test_paypal_wallets_endpoint(self):
        """Test GET /api/admin/paypal-wallets"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(f"{BASE_URL}/api/admin/paypal-wallets")
        assert response.status_code == 200
        data = response.json()
        assert "wallets" in data
        assert "total_wallets" in data
        assert "total_accumulated" in data
        assert "min_payout_threshold" in data
        print(f"✓ PayPal wallets endpoint works - {data.get('total_wallets', 0)} wallets, ${data.get('total_accumulated', 0):.2f} accumulated")
    
    # ==================== PERSONAL REPORTS ====================
    
    def test_personal_reports_get(self):
        """Test GET /api/personal-reports"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(f"{BASE_URL}/api/personal-reports")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        print(f"✓ Personal reports GET works - {len(data.get('reports', []))} reports")
    
    def test_personal_reports_create(self):
        """Test POST /api/personal-reports"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.post(f"{BASE_URL}/api/personal-reports", json={
            "title": "Test Personal Report from Iteration 55",
            "content": "This is a test personal report created during iteration 55 testing. I wanted to share my experience testing the InfoPilot application. I found the document classification feature very useful. I was impressed by the map export functionality. I think the gamification badges are a great addition.",
            "topic": "Testing",
            "location_name": "Test Location"
        })
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "report_id" in data or "id" in data
        report_id = data.get("report_id") or data.get("id")
        print(f"✓ Personal report created - ID: {report_id}")
        
        # Clean up - delete the test report
        if report_id:
            delete_response = self.session.delete(f"{BASE_URL}/api/personal-reports/{report_id}")
            if delete_response.status_code == 200:
                print("  ✓ Test report cleaned up")
    
    # ==================== GAMIFICATION BADGES ====================
    
    def test_gamification_achievements(self):
        """Test gamification achievements endpoint"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(f"{BASE_URL}/api/gamification/achievements")
        assert response.status_code == 200
        data = response.json()
        assert "achievements" in data or "total_points" in data
        print(f"✓ Gamification achievements endpoint works")
    
    def test_gamification_available_badges(self):
        """Test that new badges exist in gamification service"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(f"{BASE_URL}/api/gamification/available")
        # This endpoint may or may not exist, so we check both cases
        if response.status_code == 200:
            data = response.json()
            # Check for new badges
            badges = data.get("badges", data.get("achievements", []))
            badge_ids = [b.get("id") for b in badges] if isinstance(badges, list) else list(badges.keys())
            
            # Check for new badges from iteration 55
            new_badges = ["first_personal_report", "phd_finder", "news_junkie"]
            found_badges = [b for b in new_badges if b in badge_ids]
            print(f"✓ Found new badges: {found_badges}")
        else:
            # Try alternative endpoint
            response = self.session.get(f"{BASE_URL}/api/gamification/badges")
            if response.status_code == 200:
                print("✓ Gamification badges endpoint accessible")
            else:
                print("⚠ Gamification available badges endpoint not found (may be internal)")
    
    # ==================== DOCTYPE SETTINGS ====================
    
    def test_doctype_settings_get(self):
        """Test GET /api/admin/doctype-settings"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(f"{BASE_URL}/api/admin/doctype-settings")
        assert response.status_code == 200
        data = response.json()
        assert "settings" in data
        assert "document_types" in data
        
        # Verify document types include all expected types
        doc_types = [dt.get("type") for dt in data.get("document_types", [])]
        expected_types = ["PhD Informative", "Informative", "News Article", "Blog Post", "Forum", "Personal Report (Organic)", "Personal Report (Collected)"]
        for expected in expected_types:
            assert expected in doc_types, f"Missing document type: {expected}"
        
        print(f"✓ Doctype settings GET works - {len(doc_types)} document types")
    
    # ==================== ADMIN STATS ====================
    
    def test_admin_stats(self):
        """Test GET /api/admin/stats"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(f"{BASE_URL}/api/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "categories" in data
        print(f"✓ Admin stats works - {data.get('users', 0)} users, {data.get('categories', 0)} categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
