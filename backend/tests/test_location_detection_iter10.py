"""
Test Location Detection Bug Fix - Iteration 10
Tests the fix for detecting 'Virgin Bay, Nicaragua' without country name explicitly mentioned
Also tests the new modular backend structure
"""
import pytest
import requests
import os
import sys

# Add backend to path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ============= LOCATION DETECTION TESTS =============

class TestLocationExtractor:
    """Test LocationExtractor class for bug fix verification"""
    
    def test_virgin_bay_with_country(self):
        """Test Virgin Bay detection when Nicaragua is mentioned"""
        from server import LocationExtractor
        
        text = "The beautiful town of Virgin Bay, Nicaragua is a popular tourist destination."
        locations = LocationExtractor.extract_locations(text)
        
        # Find Virgin Bay in results
        virgin_bay_found = any(
            loc.get('city') == 'Virgin Bay' and loc.get('country') == 'Nicaragua'
            for loc in locations
        )
        assert virgin_bay_found, f"Virgin Bay not found in locations: {locations}"
    
    def test_virgin_bay_without_country_bug_fix(self):
        """BUG FIX TEST: Virgin Bay should be detected even without country name"""
        from server import LocationExtractor
        
        text = "We visited Virgin Bay last summer. The beaches were amazing."
        locations = LocationExtractor.extract_locations(text)
        
        # Find Virgin Bay in results - this is the bug fix
        virgin_bay_found = any(
            loc.get('city') == 'Virgin Bay' and loc.get('country') == 'Nicaragua'
            for loc in locations
        )
        assert virgin_bay_found, f"BUG NOT FIXED: Virgin Bay not detected without country name. Locations: {locations}"
    
    def test_multiple_nicaragua_cities(self):
        """Test multiple Nicaragua cities detection"""
        from server import LocationExtractor
        
        text = "From Managua to Virgin Bay, the journey takes about 2 hours through Granada."
        locations = LocationExtractor.extract_locations(text)
        
        cities_found = [loc.get('city') for loc in locations if loc.get('city')]
        
        assert 'Managua' in cities_found, f"Managua not found. Cities: {cities_found}"
        assert 'Virgin Bay' in cities_found, f"Virgin Bay not found. Cities: {cities_found}"
        assert 'Granada' in cities_found, f"Granada not found. Cities: {cities_found}"
    
    def test_nicaragua_cities_in_international_cities_dict(self):
        """Verify Nicaragua cities are in INTERNATIONAL_CITIES"""
        from server import LocationExtractor
        
        nicaragua_cities = LocationExtractor.INTERNATIONAL_CITIES.get('Nicaragua', [])
        
        assert 'Virgin Bay' in nicaragua_cities, "Virgin Bay not in Nicaragua cities list"
        assert 'Managua' in nicaragua_cities, "Managua not in Nicaragua cities list"
        assert 'Granada' in nicaragua_cities, "Granada not in Nicaragua cities list"
        assert 'San Juan del Sur' in nicaragua_cities, "San Juan del Sur not in Nicaragua cities list"
        assert len(nicaragua_cities) >= 10, f"Expected at least 10 Nicaragua cities, got {len(nicaragua_cities)}"
    
    def test_us_city_state_detection(self):
        """Test US city+state detection still works"""
        from server import LocationExtractor
        
        text = "Portland, Maine is known for its beautiful coastline."
        locations = LocationExtractor.extract_locations(text)
        
        portland_found = any(
            loc.get('city') == 'Portland' and loc.get('state') == 'Maine'
            for loc in locations
        )
        assert portland_found, f"Portland, Maine not found. Locations: {locations}"
    
    def test_international_cities_dict_structure(self):
        """Verify INTERNATIONAL_CITIES dict has expected countries"""
        from server import LocationExtractor
        
        expected_countries = ['Nicaragua', 'Costa Rica', 'Panama', 'Mexico', 'Canada', 'UK', 'Germany']
        
        for country in expected_countries:
            assert country in LocationExtractor.INTERNATIONAL_CITIES, f"{country} not in INTERNATIONAL_CITIES"
            cities = LocationExtractor.INTERNATIONAL_CITIES[country]
            assert len(cities) > 0, f"{country} has no cities"


# ============= MODULAR STRUCTURE TESTS =============

class TestModularStructure:
    """Test the new modular backend structure"""
    
    def test_models_enums_module_exists(self):
        """Test models/enums.py exists and has correct content"""
        from models.enums import DocumentType, ReactionType, SearchAggregation
        
        # Verify enums exist
        assert hasattr(DocumentType, 'INFORMATIVE_PHD')
        assert hasattr(DocumentType, 'NEWS_ARTICLE')
        assert hasattr(ReactionType, 'LIKE')
        assert hasattr(SearchAggregation, 'AND_OR')
    
    def test_models_schemas_module_exists(self):
        """Test models/schemas.py exists and has correct content"""
        from models.schemas import User, Category, CategoryCreate, SearchResult
        
        # Verify models exist
        assert User is not None
        assert Category is not None
        assert CategoryCreate is not None
        assert SearchResult is not None
    
    def test_services_location_module_exists(self):
        """Test services/location.py exists and has LocationExtractor"""
        from services.location import LocationExtractor as ServiceLocationExtractor
        
        # Verify class exists and has key methods
        assert hasattr(ServiceLocationExtractor, 'extract_locations')
        assert hasattr(ServiceLocationExtractor, 'INTERNATIONAL_CITIES')
        assert hasattr(ServiceLocationExtractor, 'US_STATES')
    
    def test_services_protocol_module_exists(self):
        """Test services/protocol.py exists and has ProtocolParser"""
        from services.protocol import ProtocolParser, DocumentClassifier
        
        # Verify classes exist
        assert hasattr(ProtocolParser, 'parse_protocol')
        assert hasattr(ProtocolParser, 'matches_protocol')
        assert hasattr(DocumentClassifier, 'classify')
    
    def test_services_location_virgin_bay_fix(self):
        """Test the refactored location service also has the bug fix"""
        from services.location import LocationExtractor
        
        text = "We visited Virgin Bay last summer."
        locations = LocationExtractor.extract_locations(text)
        
        virgin_bay_found = any(
            loc.get('city') == 'Virgin Bay' and loc.get('country') == 'Nicaragua'
            for loc in locations
        )
        assert virgin_bay_found, "Bug fix not present in services/location.py"


# ============= API ENDPOINT TESTS =============

class TestAPIEndpoints:
    """Test backend API endpoints are still functional after refactoring"""
    
    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'healthy'
    
    def test_document_types_endpoint(self):
        """Test /api/document-types endpoint"""
        response = requests.get(f"{BASE_URL}/api/document-types")
        assert response.status_code == 200
        data = response.json()
        assert 'types' in data
        assert len(data['types']) > 0
    
    def test_branding_info_endpoint(self):
        """Test /api/branding/info endpoint (public)"""
        response = requests.get(f"{BASE_URL}/api/branding/info")
        assert response.status_code == 200
        data = response.json()
        assert 'app_name' in data or 'tagline' in data
    
    def test_marketplace_headlines_endpoint(self):
        """Test /api/marketplace/headlines endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/headlines")
        assert response.status_code == 200
        data = response.json()
        assert 'headlines' in data
    
    def test_auth_me_requires_auth(self):
        """Test /api/auth/me requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


# ============= PROTOCOL PARSER TESTS =============

class TestProtocolParser:
    """Test ProtocolParser functionality"""
    
    def test_parse_simple_protocol(self):
        """Test parsing a simple protocol"""
        from server import ProtocolParser
        
        protocol = "(civil war) & (battle or battles)"
        result = ProtocolParser.parse_protocol(protocol)
        
        assert 'include_groups' in result
        assert len(result['include_groups']) >= 2
    
    def test_matches_protocol(self):
        """Test protocol matching"""
        from server import ProtocolParser
        
        protocol = "(civil war) & (battle)"
        text = "The civil war had many battles."
        
        assert ProtocolParser.matches_protocol(text, protocol) == True
    
    def test_exclude_modifier(self):
        """Test exclude modifier (^)"""
        from server import ProtocolParser
        
        protocol = "(civil war) & (spam)^"
        text = "The civil war was significant."
        
        # Should match because 'spam' is excluded and not in text
        assert ProtocolParser.matches_protocol(text, protocol) == True
        
        text_with_spam = "The civil war spam content."
        # Should not match because 'spam' is in text
        assert ProtocolParser.matches_protocol(text_with_spam, protocol) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
