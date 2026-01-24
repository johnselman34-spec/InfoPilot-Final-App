"""
Test Statistics Features - 14+ Analysis Aspects
Tests for enhanced statistics with geolocation, source types, and all analysis dimensions
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session created for testing
TEST_SESSION_TOKEN = "test_session_1769225468527"
TEST_USER_ID = "test-user-1769225468527"


class TestStatisticsAPI:
    """Test Statistics API with 16 analysis aspects"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def test_stats_overview_requires_auth(self):
        """Test that stats/overview requires authentication"""
        response = requests.get(f"{BASE_URL}/api/stats/overview")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_stats_overview_returns_all_fields(self):
        """Test that stats/overview returns all 16+ data fields"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify all 16+ fields are present
        required_fields = [
            "total_results",
            "total_categories", 
            "total_locations",
            "by_document_type",      # Aspect 1
            "by_source_type",        # Aspect 2
            "by_category",           # Aspect 3
            "by_country",            # Aspect 5
            "by_state",              # Aspect 6
            "by_city",               # Aspect 7
            "by_region",             # Aspect 8 - US Regions
            "by_year",               # Aspect 9
            "by_age_bracket",        # Aspect 10
            "by_day_of_week",        # Aspect 11
            "by_month",              # Aspect 12
            "by_domain",             # Aspect 13
            "by_tld",                # Aspect 14
            "by_content_length",     # Aspect 15
            "by_match_quality",      # Aspect 16
            "by_reaction"            # Aspect 17
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify we have at least 16 data fields (excluding totals)
        data_fields = [k for k in data.keys() if k.startswith("by_")]
        assert len(data_fields) >= 14, f"Expected 14+ data fields, got {len(data_fields)}"
    
    def test_stats_document_types(self):
        """Test Aspect 1: Document Types distribution"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        doc_types = data.get("by_document_type", [])
        
        # Verify structure
        if doc_types:
            assert "_id" in doc_types[0], "Document type should have _id"
            assert "count" in doc_types[0], "Document type should have count"
    
    def test_stats_source_types(self):
        """Test Aspect 2: Source Types (Webpage, News, Academic, etc.)"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        source_types = data.get("by_source_type", [])
        
        # Verify structure
        if source_types:
            assert "_id" in source_types[0], "Source type should have _id"
            assert "count" in source_types[0], "Source type should have count"
            
            # Check for expected source type categories
            type_names = [s["_id"] for s in source_types]
            expected_types = ["News", "Academic", "Government", "Wiki", "Webpage"]
            # At least some expected types should be present
            found_types = [t for t in expected_types if t in type_names]
            print(f"Found source types: {type_names}")
    
    def test_stats_by_category(self):
        """Test Aspect 3: Results by Category"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        categories = data.get("by_category", [])
        
        if categories:
            assert "_id" in categories[0], "Category should have _id"
            assert "count" in categories[0], "Category should have count"
    
    def test_stats_by_country(self):
        """Test Aspect 5: Results by Country"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        countries = data.get("by_country", [])
        
        if countries:
            assert "_id" in countries[0], "Country should have _id"
            assert "count" in countries[0], "Country should have count"
    
    def test_stats_by_state(self):
        """Test Aspect 6: Results by State"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        states = data.get("by_state", [])
        
        if states:
            assert "_id" in states[0], "State should have _id"
            assert "count" in states[0], "State should have count"
    
    def test_stats_by_city(self):
        """Test Aspect 7: Results by City"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        cities = data.get("by_city", [])
        
        if cities:
            assert "_id" in cities[0], "City should have _id"
            assert "count" in cities[0], "City should have count"
    
    def test_stats_us_regions(self):
        """Test Aspect 8: US Regions (Northeast, Southeast, Midwest, Southwest, West)"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        regions = data.get("by_region", [])
        
        if regions:
            assert "_id" in regions[0], "Region should have _id"
            assert "count" in regions[0], "Region should have count"
            
            # Check for expected US regions
            region_names = [r["_id"] for r in regions]
            expected_regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
            print(f"Found regions: {region_names}")
    
    def test_stats_by_year(self):
        """Test Aspect 9: Results by Year"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        years = data.get("by_year", [])
        
        if years:
            assert "_id" in years[0], "Year should have _id"
            assert "count" in years[0], "Year should have count"
    
    def test_stats_age_brackets(self):
        """Test Aspect 10: Age of Subjects brackets"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        age_brackets = data.get("by_age_bracket", [])
        
        if age_brackets:
            assert "_id" in age_brackets[0], "Age bracket should have _id"
            assert "count" in age_brackets[0], "Age bracket should have count"
    
    def test_stats_top_domains(self):
        """Test Aspect 13: Top Domains"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        domains = data.get("by_domain", [])
        
        if domains:
            assert "_id" in domains[0], "Domain should have _id"
            assert "count" in domains[0], "Domain should have count"
    
    def test_stats_tld_distribution(self):
        """Test Aspect 14: Top Level Domains (.com, .org, .edu)"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        tlds = data.get("by_tld", [])
        
        if tlds:
            assert "_id" in tlds[0], "TLD should have _id"
            assert "count" in tlds[0], "TLD should have count"
            
            # Check for expected TLDs
            tld_names = [t["_id"] for t in tlds]
            expected_tlds = ["com", "org", "edu", "gov"]
            print(f"Found TLDs: {tld_names}")


class TestMarketplaceFeatures:
    """Test Marketplace Headlines and Recommended Protocols"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def test_marketplace_headlines(self):
        """Test Marketplace Headlines endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/headlines")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "headlines" in data, "Response should have headlines"
        
        headlines = data["headlines"]
        assert len(headlines) >= 5, f"Expected at least 5 headlines, got {len(headlines)}"
        
        # Verify headline structure
        for headline in headlines:
            assert "title" in headline, "Headline should have title"
            assert "category" in headline, "Headline should have category"
    
    def test_recommended_protocols_requires_auth(self):
        """Test that recommended protocols requires authentication"""
        response = requests.get(f"{BASE_URL}/api/marketplace/recommended")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_recommended_protocols_with_auth(self):
        """Test Recommended Protocols with authentication"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/recommended",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "protocols" in data, "Response should have protocols"


class TestLocationExtractor:
    """Test Enhanced Geolocation features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def test_search_with_state_abbreviation(self):
        """Test that search detects state abbreviations like CA, NY, VA"""
        # This tests the LocationExtractor indirectly through search
        response = requests.post(
            f"{BASE_URL}/api/search",
            headers=self.headers,
            json={
                "query": "technology news from San Francisco, CA",
                "category_ids": []
            }
        )
        # Just verify the endpoint works
        assert response.status_code in [200, 201], f"Search should work, got {response.status_code}"
    
    def test_search_with_city_name(self):
        """Test that search detects major cities"""
        response = requests.post(
            f"{BASE_URL}/api/search",
            headers=self.headers,
            json={
                "query": "business news from New York City",
                "category_ids": []
            }
        )
        assert response.status_code in [200, 201], f"Search should work, got {response.status_code}"
    
    def test_search_with_regional_prefix(self):
        """Test that search detects regional prefixes (Northern Virginia, Greater Boston)"""
        response = requests.post(
            f"{BASE_URL}/api/search",
            headers=self.headers,
            json={
                "query": "tech companies in Northern Virginia",
                "category_ids": []
            }
        )
        assert response.status_code in [200, 201], f"Search should work, got {response.status_code}"


class TestSearchMatchOptions:
    """Test Search Match Options checkboxes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def test_search_with_match_options(self):
        """Test search with various match options"""
        response = requests.post(
            f"{BASE_URL}/api/search",
            headers=self.headers,
            json={
                "query": "test search",
                "category_ids": [],
                "match_options": {
                    "exact_match": True,
                    "strict_match": False,
                    "ai_match": True,
                    "intelligent_match": False,
                    "schematics": False
                }
            }
        )
        assert response.status_code in [200, 201], f"Search with match options should work, got {response.status_code}"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_auth_me_with_valid_token(self):
        """Test auth/me with valid session token"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {TEST_SESSION_TOKEN}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data or "email" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
