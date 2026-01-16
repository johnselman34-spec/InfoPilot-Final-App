#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class InfoPilotAPITester:
    def __init__(self, base_url="https://deep-search-app.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.category_id = None

    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}", "PASS")
                try:
                    return True, response.json() if response.text else {}
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}", "FAIL")
                try:
                    error_detail = response.json().get('detail', 'No detail')
                    self.log(f"   Error: {error_detail}", "ERROR")
                except:
                    self.log(f"   Response: {response.text[:200]}", "ERROR")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Exception: {str(e)}", "FAIL")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoints"""
        self.log("=== HEALTH CHECK TESTS ===", "SECTION")
        
        # Test root endpoint
        self.run_test("Root Endpoint", "GET", "", 200)
        
        # Test health endpoint
        self.run_test("Health Check", "GET", "health", 200)

    def test_authentication(self):
        """Test authentication endpoints"""
        self.log("=== AUTHENTICATION TESTS ===", "SECTION")
        
        # Test login with admin credentials
        login_data = {
            "email": "john@infojet.com",
            "password": "password123"
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            self.log(f"✅ Token obtained: {self.token[:20]}...", "SUCCESS")
            self.log(f"✅ User ID: {self.user_id}", "SUCCESS")
            self.log(f"✅ Is Admin: {response['user'].get('is_admin', False)}", "SUCCESS")
            
            # Test /auth/me endpoint
            self.run_test("Get Current User", "GET", "auth/me", 200)
            
            return True
        else:
            self.log("❌ Failed to get authentication token", "FAIL")
            return False

    def test_admin_endpoints(self):
        """Test admin-specific endpoints"""
        if not self.token:
            self.log("❌ Skipping admin tests - no auth token", "SKIP")
            return
            
        self.log("=== ADMIN ENDPOINTS TESTS ===", "SECTION")
        
        # Test get admin settings
        self.run_test("Get Admin Settings", "GET", "admin/settings", 200)
        
        # Test update admin setting
        self.run_test(
            "Update Admin Setting",
            "PUT",
            "admin/settings/daily_collate_limit",
            200,
            data=15
        )
        
        # Test init admin settings
        self.run_test("Init Admin Settings", "POST", "admin/init", 200)

    def test_categories(self):
        """Test category management"""
        if not self.token:
            self.log("❌ Skipping category tests - no auth token", "SKIP")
            return
            
        self.log("=== CATEGORY TESTS ===", "SECTION")
        
        # Test get categories (should be empty initially)
        self.run_test("Get Categories", "GET", "categories", 200)
        
        # Test create category
        category_data = {
            "name": "Test Category",
            "protocol": "(test or example) & (info)",
            "is_public": True
        }
        
        success, response = self.run_test(
            "Create Category",
            "POST",
            "categories",
            200,
            data=category_data
        )
        
        if success and 'id' in response:
            self.category_id = response['id']
            self.log(f"✅ Category created with ID: {self.category_id}", "SUCCESS")
            
            # Test update category
            update_data = {
                "name": "Updated Test Category",
                "is_public": False
            }
            
            self.run_test(
                "Update Category",
                "PUT",
                f"categories/{self.category_id}",
                200,
                data=update_data
            )

    def test_search_and_collate(self):
        """Test search and collate functionality"""
        if not self.token:
            self.log("❌ Skipping search tests - no auth token", "SKIP")
            return
            
        self.log("=== SEARCH & COLLATE TESTS ===", "SECTION")
        
        # Test search
        search_data = {
            "query": "artificial intelligence test"
        }
        
        success, search_response = self.run_test(
            "Web Search",
            "POST",
            "search",
            200,
            data=search_data
        )
        
        if success and 'results' in search_response:
            self.log(f"✅ Search returned {len(search_response['results'])} results", "SUCCESS")
            
            # Test collate with search results
            collate_data = {
                "search_results": search_response['results'][:5]  # Use first 5 results
            }
            
            self.run_test(
                "Collate Results",
                "POST",
                "collate",
                200,
                data=collate_data
            )

    def test_ultimate_search(self):
        """Test ultimate search page endpoints"""
        if not self.token:
            self.log("❌ Skipping ultimate search tests - no auth token", "SKIP")
            return
            
        self.log("=== ULTIMATE SEARCH TESTS ===", "SECTION")
        
        # Test get ultimate search results
        self.run_test("Get Ultimate Search Results", "GET", "ultimate-search", 200)
        
        # Test get ultimate search stats
        self.run_test("Get Ultimate Search Stats", "GET", "ultimate-search/stats", 200)

    def test_social_features(self):
        """Test social features"""
        if not self.token:
            self.log("❌ Skipping social tests - no auth token", "SKIP")
            return
            
        self.log("=== SOCIAL FEATURES TESTS ===", "SECTION")
        
        # Test get friends
        self.run_test("Get Friends List", "GET", "friends", 200)

    def test_map_data(self):
        """Test map data endpoint"""
        if not self.token:
            self.log("❌ Skipping map tests - no auth token", "SKIP")
            return
            
        self.log("=== MAP DATA TESTS ===", "SECTION")
        
        # Test get map data (admin should have access)
        self.run_test("Get Map Data", "GET", "map-data", 200)

    def test_user_settings(self):
        """Test user settings"""
        if not self.token:
            self.log("❌ Skipping settings tests - no auth token", "SKIP")
            return
            
        self.log("=== USER SETTINGS TESTS ===", "SECTION")
        
        # Test update user settings
        self.run_test(
            "Update User Settings",
            "PUT",
            "users/settings?ultimate_search_public=true&friends_visible=true",
            200
        )

    def cleanup(self):
        """Clean up test data"""
        if not self.token or not self.category_id:
            return
            
        self.log("=== CLEANUP ===", "SECTION")
        
        # Delete test category
        self.run_test(
            "Delete Test Category",
            "DELETE",
            f"categories/{self.category_id}",
            200
        )

    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting InfoPilot API Tests", "START")
        self.log(f"🔗 Base URL: {self.base_url}", "INFO")
        
        # Run tests in order
        self.test_health_check()
        
        if self.test_authentication():
            self.test_admin_endpoints()
            self.test_categories()
            self.test_search_and_collate()
            self.test_ultimate_search()
            self.test_social_features()
            self.test_map_data()
            self.test_user_settings()
            self.cleanup()
        
        # Print final results
        self.log("=" * 50, "SECTION")
        self.log(f"📊 FINAL RESULTS", "RESULT")
        self.log(f"✅ Tests Passed: {self.tests_passed}", "RESULT")
        self.log(f"❌ Tests Failed: {self.tests_run - self.tests_passed}", "RESULT")
        self.log(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%", "RESULT")
        
        if self.tests_passed == self.tests_run:
            self.log("🎉 ALL TESTS PASSED!", "SUCCESS")
            return 0
        else:
            self.log("⚠️  SOME TESTS FAILED", "WARNING")
            return 1

def main():
    tester = InfoPilotAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())