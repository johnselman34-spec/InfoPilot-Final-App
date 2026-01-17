"""
InfoPilot Explorer - Iteration 16 Statistics & Leaderboard Tests
Tests for:
- Statistics Overview API
- Statistics Dashboard API
- Countries breakdown
- US States breakdown
- Document types
- Top words
- Top Sellers Leaderboard (Sales & Revenue)
- Marketplace protocols (11 total including George Bush, William C. Gamble, Richard J. Selman)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://info-explorer-hub.preview.emergentagent.com').rstrip('/')


class TestStatisticsOverview:
    """Test /api/statistics/overview endpoint"""
    
    def test_statistics_overview_returns_200(self):
        """Test that statistics overview endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/overview")
        assert response.status_code == 200
        
    def test_statistics_overview_has_required_fields(self):
        """Test that overview contains all required fields"""
        response = requests.get(f"{BASE_URL}/api/statistics/overview")
        data = response.json()
        
        required_fields = [
            'total_users', 'active_users_7d', 'total_categories',
            'total_protocols', 'total_searches', 'total_purchases',
            'total_revenue', 'generated_at'
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            
    def test_statistics_overview_values_are_valid(self):
        """Test that overview values are valid numbers"""
        response = requests.get(f"{BASE_URL}/api/statistics/overview")
        data = response.json()
        
        assert isinstance(data['total_users'], int)
        assert isinstance(data['total_protocols'], int)
        assert data['total_protocols'] == 11, f"Expected 11 protocols, got {data['total_protocols']}"
        assert isinstance(data['total_revenue'], (int, float))


class TestStatisticsDashboard:
    """Test /api/statistics/dashboard endpoint"""
    
    def test_dashboard_returns_200(self):
        """Test that dashboard endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/dashboard")
        assert response.status_code == 200
        
    def test_dashboard_has_all_sections(self):
        """Test that dashboard contains all required sections"""
        response = requests.get(f"{BASE_URL}/api/statistics/dashboard")
        data = response.json()
        
        required_sections = [
            'overview', 'countries', 'us_states', 'document_types',
            'top_words', 'top_phrases', 'categories', 'funny_fact'
        ]
        
        for section in required_sections:
            assert section in data, f"Missing section: {section}"
            
    def test_dashboard_funny_fact_exists(self):
        """Test that dashboard includes a funny fact"""
        response = requests.get(f"{BASE_URL}/api/statistics/dashboard")
        data = response.json()
        
        assert 'funny_fact' in data
        assert isinstance(data['funny_fact'], str)
        assert len(data['funny_fact']) > 10


class TestCountriesStatistics:
    """Test /api/statistics/countries endpoint"""
    
    def test_countries_returns_200(self):
        """Test that countries endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/countries")
        assert response.status_code == 200
        
    def test_countries_has_correct_structure(self):
        """Test that countries data has correct structure"""
        response = requests.get(f"{BASE_URL}/api/statistics/countries")
        data = response.json()
        
        assert 'countries' in data
        assert 'total_results' in data
        assert 'chart_type' in data
        assert data['chart_type'] == 'pie'
        
    def test_countries_includes_usa(self):
        """Test that USA is in the countries list"""
        response = requests.get(f"{BASE_URL}/api/statistics/countries")
        data = response.json()
        
        country_names = [c['name'] for c in data['countries']]
        assert 'United States' in country_names
        
    def test_countries_have_required_fields(self):
        """Test that each country has required fields"""
        response = requests.get(f"{BASE_URL}/api/statistics/countries")
        data = response.json()
        
        for country in data['countries']:
            assert 'name' in country
            assert 'code' in country
            assert 'count' in country
            assert 'percentage' in country


class TestUSStatesStatistics:
    """Test /api/statistics/us-states endpoint"""
    
    def test_us_states_returns_200(self):
        """Test that US states endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/us-states")
        assert response.status_code == 200
        
    def test_us_states_has_correct_structure(self):
        """Test that US states data has correct structure"""
        response = requests.get(f"{BASE_URL}/api/statistics/us-states")
        data = response.json()
        
        assert 'states' in data
        assert 'total_results' in data
        assert 'chart_type' in data
        assert data['chart_type'] == 'bar'
        
    def test_us_states_includes_maine(self):
        """Test that Maine (Brunswick connection) is in the states list"""
        response = requests.get(f"{BASE_URL}/api/statistics/us-states")
        data = response.json()
        
        state_names = [s['name'] for s in data['states']]
        assert 'Maine' in state_names, "Maine should be included (Brunswick connection)"


class TestDocumentTypesStatistics:
    """Test /api/statistics/document-types endpoint"""
    
    def test_document_types_returns_200(self):
        """Test that document types endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/document-types")
        assert response.status_code == 200
        
    def test_document_types_has_correct_structure(self):
        """Test that document types data has correct structure"""
        response = requests.get(f"{BASE_URL}/api/statistics/document-types")
        data = response.json()
        
        assert 'document_types' in data
        assert 'total_results' in data
        assert 'chart_type' in data
        
    def test_document_types_have_colors(self):
        """Test that document types have color codes for charts"""
        response = requests.get(f"{BASE_URL}/api/statistics/document-types")
        data = response.json()
        
        for doc_type in data['document_types']:
            assert 'color' in doc_type
            assert doc_type['color'].startswith('#')


class TestTopWordsStatistics:
    """Test /api/statistics/top-words endpoint"""
    
    def test_top_words_returns_200(self):
        """Test that top words endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/top-words")
        assert response.status_code == 200
        
    def test_top_words_has_correct_structure(self):
        """Test that top words data has correct structure"""
        response = requests.get(f"{BASE_URL}/api/statistics/top-words")
        data = response.json()
        
        assert 'top_words' in data
        assert 'chart_type' in data
        
    def test_top_words_have_ranks(self):
        """Test that top words have rank numbers"""
        response = requests.get(f"{BASE_URL}/api/statistics/top-words")
        data = response.json()
        
        for word in data['top_words']:
            assert 'word' in word
            assert 'count' in word
            assert 'rank' in word


class TestLeaderboardBySales:
    """Test /api/marketplace/leaderboard/sales endpoint"""
    
    def test_leaderboard_sales_returns_200(self):
        """Test that leaderboard by sales endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/sales")
        assert response.status_code == 200
        
    def test_leaderboard_sales_has_correct_structure(self):
        """Test that leaderboard has correct structure"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/sales")
        data = response.json()
        
        assert 'leaderboard' in data
        assert 'last_updated' in data
        assert 'type' in data
        assert data['type'] == 'sales'
        
    def test_leaderboard_sales_has_funny_titles(self):
        """Test that leaderboard entries have funny titles"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/sales")
        data = response.json()
        
        if data['leaderboard']:
            first_seller = data['leaderboard'][0]
            assert 'title' in first_seller
            assert 'badge' in first_seller
            # First place should be "The Protocol Overlord"
            assert 'Protocol Overlord' in first_seller['title'] or 'Overlord' in first_seller['title']
            
    def test_leaderboard_sales_entries_have_required_fields(self):
        """Test that each leaderboard entry has required fields"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/sales")
        data = response.json()
        
        required_fields = ['rank', 'creator_id', 'creator_name', 'total_sales', 
                          'protocol_count', 'avg_rating', 'badge', 'title']
        
        for seller in data['leaderboard']:
            for field in required_fields:
                assert field in seller, f"Missing field: {field}"


class TestLeaderboardByRevenue:
    """Test /api/marketplace/leaderboard/revenue endpoint"""
    
    def test_leaderboard_revenue_returns_200(self):
        """Test that leaderboard by revenue endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/revenue")
        assert response.status_code == 200
        
    def test_leaderboard_revenue_has_correct_structure(self):
        """Test that leaderboard has correct structure"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/revenue")
        data = response.json()
        
        assert 'leaderboard' in data
        assert 'last_updated' in data
        assert 'type' in data
        assert data['type'] == 'revenue'
        
    def test_leaderboard_revenue_has_funny_titles(self):
        """Test that revenue leaderboard has funny titles"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/revenue")
        data = response.json()
        
        if data['leaderboard']:
            first_seller = data['leaderboard'][0]
            assert 'title' in first_seller
            # First place should be "The Protocol Billionaire"
            assert 'Billionaire' in first_seller['title'] or 'Protocol' in first_seller['title']
            
    def test_leaderboard_revenue_entries_have_required_fields(self):
        """Test that each revenue leaderboard entry has required fields"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/revenue")
        data = response.json()
        
        required_fields = ['rank', 'creator_id', 'creator_name', 'total_revenue', 
                          'creator_earnings', 'total_sales', 'protocol_count', 'badge', 'title']
        
        for seller in data['leaderboard']:
            for field in required_fields:
                assert field in seller, f"Missing field: {field}"


class TestMarketplaceProtocols:
    """Test marketplace protocols - verify all 11 protocols including new ones"""
    
    def test_marketplace_has_11_protocols(self):
        """Test that marketplace has exactly 11 protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols?limit=20")
        assert response.status_code == 200
        
        data = response.json()
        assert data['total'] == 11, f"Expected 11 protocols, got {data['total']}"
        
    def test_george_bush_protocol_exists(self):
        """Test that George Bush protocol exists in marketplace"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols?limit=20")
        data = response.json()
        
        protocol_names = [p['name'] for p in data['protocols']]
        assert any('George Bush' in name for name in protocol_names), \
            f"George Bush protocol not found. Available: {protocol_names}"
            
    def test_william_c_gamble_protocol_exists(self):
        """Test that William C. Gamble protocol exists in marketplace"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols?limit=20")
        data = response.json()
        
        protocol_names = [p['name'] for p in data['protocols']]
        assert any('William C. Gamble' in name or 'Gamble' in name for name in protocol_names), \
            f"William C. Gamble protocol not found. Available: {protocol_names}"
            
    def test_richard_j_selman_protocol_exists(self):
        """Test that Richard J. Selman protocol exists in marketplace"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols?limit=20")
        data = response.json()
        
        protocol_names = [p['name'] for p in data['protocols']]
        assert any('Richard J. Selman' in name or 'Selman' in name for name in protocol_names), \
            f"Richard J. Selman protocol not found. Available: {protocol_names}"


class TestAdditionalStatisticsEndpoints:
    """Test additional statistics endpoints"""
    
    def test_top_protocol_phrases_returns_200(self):
        """Test that top protocol phrases endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/top-protocol-phrases")
        assert response.status_code == 200
        
    def test_category_breakdown_returns_200(self):
        """Test that category breakdown endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/category-breakdown")
        assert response.status_code == 200
        
    def test_user_growth_time_series_returns_200(self):
        """Test that user growth time series endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/time-series/users")
        assert response.status_code == 200
        
    def test_revenue_time_series_returns_200(self):
        """Test that revenue time series endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/time-series/revenue")
        assert response.status_code == 200
        
    def test_clipboard_copy_stats_returns_200(self):
        """Test that clipboard copy stats endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/statistics/protocol-clipboard-copies")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
