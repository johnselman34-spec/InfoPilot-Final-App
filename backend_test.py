#!/usr/bin/env python3
"""
InfoPilot Explorer Backend API Test Suite
Tests all major API endpoints and functionality
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class InfoPilotAPITester:
    def __init__(self, base_url: str = "https://word-integrator.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        # Test credentials from review request
        self.session_token = "test_session_1769213571175"
        self.user_id = "test-user-1769213571175"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.critical_failures = []

    def log_result(self, test_name: str, success: bool, details: str = "", is_critical: bool = False):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")
        
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append({"test": test_name, "details": details})
            if is_critical:
                self.critical_failures.append(test_name)
        print()

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200, headers: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Make HTTP request and return success status and response data"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        # Default headers
        req_headers = {'Content-Type': 'application/json'}
        if self.session_token:
            req_headers['Authorization'] = f'Bearer {self.session_token}'
        if headers:
            req_headers.update(headers)

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=req_headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=req_headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=req_headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"status_code": response.status_code, "text": response.text[:200]}
            
            return success, response_data

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_health_check(self):
        """Test basic API health"""
        success, data = self.make_request('GET', '/')
        if success:
            expected_fields = ['name', 'version', 'description']
            has_fields = all(field in data for field in expected_fields)
            self.log_result(
                "API Health Check", 
                has_fields,
                f"Response: {data.get('name', 'N/A')} v{data.get('version', 'N/A')}",
                is_critical=True
            )
        else:
            self.log_result("API Health Check", False, f"Failed to connect: {data}", is_critical=True)

    def test_health_endpoint(self):
        """Test health endpoint"""
        success, data = self.make_request('GET', '/health')
        if success and 'status' in data:
            self.log_result("Health Endpoint", True, f"Status: {data.get('status')}")
        else:
            self.log_result("Health Endpoint", False, f"Response: {data}")

    def create_test_user_session(self):
        """Create a test user session for authenticated endpoints"""
        # For testing purposes, we'll simulate the OAuth flow
        # In a real scenario, this would go through the actual OAuth process
        test_user_data = {
            "session_id": f"test_session_{datetime.now().timestamp()}"
        }
        
        # Try to create session (this will likely fail without proper OAuth)
        success, data = self.make_request('POST', '/auth/session', test_user_data, expected_status=400)
        
        # Since OAuth integration requires external service, we'll note this limitation
        self.log_result(
            "Auth Session Creation", 
            False, 
            "OAuth integration requires external service - cannot test authenticated endpoints fully",
            is_critical=False
        )
        return False

    def test_categories_endpoints(self):
        """Test categories API endpoints"""
        # Test GET categories (public)
        success, data = self.make_request('GET', '/categories?public_only=true')
        self.log_result(
            "GET Categories (Public)", 
            success and 'categories' in data,
            f"Found {len(data.get('categories', []))} public categories" if success else f"Error: {data}"
        )

        # Test POST categories (requires auth)
        category_data = {
            "name": "Test Category",
            "protocol": "(test or testing) & (api)+",
            "is_public": True,
            "price": 0.0
        }
        success, data = self.make_request('POST', '/categories', category_data, expected_status=401)
        self.log_result(
            "POST Categories (Auth Required)", 
            success,  # 401 is expected without auth
            "Correctly requires authentication"
        )

    def test_search_endpoints(self):
        """Test search and collate endpoints"""
        # Test search collate (requires auth)
        search_data = {
            "query": "artificial intelligence",
            "category_ids": [],
            "max_results": 10
        }
        success, data = self.make_request('POST', '/search/collate', search_data, expected_status=401)
        self.log_result(
            "POST Search/Collate (Auth Required)", 
            success,  # 401 is expected without auth
            "Correctly requires authentication"
        )

        # Test get results (requires auth)
        success, data = self.make_request('GET', '/search/results', expected_status=401)
        self.log_result(
            "GET Search Results (Auth Required)", 
            success,  # 401 is expected without auth
            "Correctly requires authentication"
        )

    def test_social_endpoints(self):
        """Test social API endpoints"""
        # Test friend request (requires auth)
        friend_data = {"user_id": "test_user_123"}
        success, data = self.make_request('POST', '/social/friends/request', friend_data, expected_status=401)
        self.log_result(
            "POST Friend Request (Auth Required)", 
            success,
            "Correctly requires authentication"
        )

        # Test get friends (requires auth)
        success, data = self.make_request('GET', '/social/friends', expected_status=401)
        self.log_result(
            "GET Friends (Auth Required)", 
            success,
            "Correctly requires authentication"
        )

        # Test reactions (requires auth)
        reaction_data = {"result_id": "test_result", "reaction_type": "Like"}
        success, data = self.make_request('POST', '/social/reactions', reaction_data, expected_status=401)
        self.log_result(
            "POST Reactions (Auth Required)", 
            success,
            "Correctly requires authentication"
        )

    def test_marketplace_endpoints(self):
        """Test marketplace API endpoints"""
        # Test get protocols (public)
        success, data = self.make_request('GET', '/marketplace/protocols')
        self.log_result(
            "GET Marketplace Protocols", 
            success and 'protocols' in data,
            f"Found {len(data.get('protocols', []))} protocols" if success else f"Error: {data}"
        )

        # Test leaderboard (public)
        success, data = self.make_request('GET', '/marketplace/leaderboard')
        self.log_result(
            "GET Marketplace Leaderboard", 
            success and ('top_sellers' in data or 'most_copied' in data),
            "Leaderboard data available" if success else f"Error: {data}"
        )

        # Test purchase (requires auth)
        purchase_data = {"category_id": "test_category"}
        success, data = self.make_request('POST', '/marketplace/purchase', purchase_data, expected_status=401)
        self.log_result(
            "POST Purchase Protocol (Auth Required)", 
            success,
            "Correctly requires authentication"
        )

    def test_groups_endpoints(self):
        """Test groups API endpoints"""
        # Test get groups (requires auth)
        success, data = self.make_request('GET', '/groups', expected_status=401)
        self.log_result(
            "GET Groups (Auth Required)", 
            success,
            "Correctly requires authentication"
        )

        # Test create group (requires auth)
        group_data = {"name": "Test Group", "description": "Test group description"}
        success, data = self.make_request('POST', '/groups', group_data, expected_status=401)
        self.log_result(
            "POST Create Group (Auth Required)", 
            success,
            "Correctly requires authentication"
        )

    def test_chat_endpoints(self):
        """Test chat API endpoints"""
        # Test get conversations (requires auth)
        success, data = self.make_request('GET', '/chat/conversations', expected_status=401)
        self.log_result(
            "GET Chat Conversations (Auth Required)", 
            success,
            "Correctly requires authentication"
        )

        # Test send message (requires auth)
        message_data = {"recipient_id": "test_user", "content": "Test message"}
        success, data = self.make_request('POST', '/chat/messages', message_data, expected_status=401)
        self.log_result(
            "POST Send Message (Auth Required)", 
            success,
            "Correctly requires authentication"
        )

    def test_stats_endpoints(self):
        """Test statistics API endpoints"""
        # Test stats overview (requires auth)
        success, data = self.make_request('GET', '/stats/overview', expected_status=401)
        self.log_result(
            "GET Stats Overview (Auth Required)", 
            success,
            "Correctly requires authentication"
        )

        # Test map data (requires auth)
        success, data = self.make_request('GET', '/stats/map-data', expected_status=401)
        self.log_result(
            "GET Map Data (Auth Required)", 
            success,
            "Correctly requires authentication"
        )

    def test_admin_endpoints(self):
        """Test admin API endpoints"""
        # Test admin analytics (requires admin auth)
        success, data = self.make_request('GET', '/admin/analytics', expected_status=401)
        self.log_result(
            "GET Admin Analytics (Auth Required)", 
            success,
            "Correctly requires authentication"
        )

    def test_protocol_parser(self):
        """Test protocol debugging endpoint"""
        protocol_data = {
            "protocol": "(artificial intelligence or AI) & (machine learning)+",
            "test_text": "This article discusses artificial intelligence and machine learning applications."
        }
        success, data = self.make_request('POST', '/debug-protocol', protocol_data)
        
        if success and 'parsed' in data and 'matches' in data:
            matches = data.get('matches', False)
            self.log_result(
                "Protocol Parser Debug", 
                True,
                f"Protocol parsing works, matches: {matches}"
            )
        else:
            self.log_result(
                "Protocol Parser Debug", 
                False,
                f"Parser failed: {data}"
            )

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting InfoPilot Explorer Backend API Tests")
        print(f"📍 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Core API tests
        self.test_health_check()
        self.test_health_endpoint()
        
        # Authentication test
        self.create_test_user_session()
        
        # Feature endpoint tests
        self.test_categories_endpoints()
        self.test_search_endpoints()
        self.test_social_endpoints()
        self.test_marketplace_endpoints()
        self.test_groups_endpoints()
        self.test_chat_endpoints()
        self.test_stats_endpoints()
        self.test_admin_endpoints()
        
        # Protocol parser test
        self.test_protocol_parser()
        
        # Print summary
        print("=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.critical_failures:
            print(f"\n🚨 CRITICAL FAILURES: {len(self.critical_failures)}")
            for failure in self.critical_failures:
                print(f"  - {failure}")
        
        if self.failed_tests:
            print(f"\n📋 FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        print("\n" + "=" * 60)
        
        # Return exit code
        return 0 if len(self.critical_failures) == 0 else 1

def main():
    """Main test runner"""
    tester = InfoPilotAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())