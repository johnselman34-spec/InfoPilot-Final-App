#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class InfoPilotAPITester:
    def __init__(self, base_url="https://data-scout-11.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.category_id = None
        
        # Test credentials
        self.test_email = "test@example.com"
        self.test_password = "password123"
        
        # New user for registration test
        timestamp = int(time.time())
        self.new_email = f"testuser{timestamp}@example.com"
        self.new_username = f"testuser{timestamp}"
        self.new_password = "testpass123"

    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json() if response.text else {}
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'No detail')
                    self.log(f"   Error: {error_detail}")
                except:
                    self.log(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoints"""
        self.log("\n=== HEALTH CHECK TESTS ===")
        
        # Test root endpoint
        success, response = self.run_test(
            "API Root",
            "GET",
            "/",
            200
        )
        
        # Test health endpoint
        success, response = self.run_test(
            "Health Check",
            "GET",
            "/health",
            200
        )
        
        return success

    def test_authentication(self):
        """Test authentication flow"""
        self.log("\n=== AUTHENTICATION TESTS ===")
        
        # Test registration with new user
        success, response = self.run_test(
            "User Registration",
            "POST",
            "/auth/register",
            200,
            data={
                "email": self.new_email,
                "username": self.new_username,
                "password": self.new_password
            }
        )
        
        if success and 'token' in response:
            self.log(f"✅ Registration successful, got token")
        else:
            self.log(f"❌ Registration failed or no token received")
            return False
        
        # Test login with test credentials
        success, response = self.run_test(
            "User Login",
            "POST",
            "/auth/login",
            200,
            data={
                "email": self.test_email,
                "password": self.test_password
            }
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            self.log(f"✅ Login successful, got token: {self.token[:20]}...")
        else:
            self.log(f"❌ Login failed or no token received")
            return False
        
        # Test get current user
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "/auth/me",
            200
        )
        
        if success:
            self.log(f"✅ User info: {response.get('username', 'N/A')} ({response.get('email', 'N/A')})")
        
        return success

    def test_categories(self):
        """Test category management"""
        self.log("\n=== CATEGORY TESTS ===")
        
        # Test get categories (should be empty initially)
        success, response = self.run_test(
            "Get Categories (Empty)",
            "GET",
            "/categories",
            200
        )
        
        # Test create category
        success, response = self.run_test(
            "Create Category",
            "POST",
            "/categories",
            200,
            data={
                "name": "American History",
                "protocol": "(civil war or american revolution)",
                "is_public": False
            }
        )
        
        if success and 'id' in response:
            self.category_id = response['id']
            self.log(f"✅ Category created with ID: {self.category_id}")
        else:
            self.log(f"❌ Category creation failed")
            return False
        
        # Test get categories (should have one now)
        success, response = self.run_test(
            "Get Categories (With Data)",
            "GET",
            "/categories",
            200
        )
        
        if success and len(response) > 0:
            self.log(f"✅ Found {len(response)} categories")
        
        # Test update category
        success, response = self.run_test(
            "Update Category",
            "PUT",
            f"/categories/{self.category_id}",
            200,
            data={
                "name": "American History Updated",
                "protocol": "(civil war or american revolution or independence)",
                "is_public": True
            }
        )
        
        return success

    def test_search_and_collate(self):
        """Test search and collate functionality"""
        self.log("\n=== SEARCH & COLLATE TESTS ===")
        
        # Test search
        success, response = self.run_test(
            "Web Search",
            "POST",
            "/search",
            200,
            data={
                "query": "artificial intelligence"
            }
        )
        
        search_results = []
        if success and 'results' in response:
            search_results = response['results']
            self.log(f"✅ Search returned {len(search_results)} results")
        else:
            self.log(f"❌ Search failed or no results")
            return False
        
        # Test collate (only if we have categories and search results)
        if self.category_id and search_results:
            success, response = self.run_test(
                "Collate Results",
                "POST",
                "/collate",
                200,
                data={
                    "search_results": search_results[:5]  # Use first 5 results
                }
            )
            
            if success:
                collated_count = response.get('collated_count', 0)
                self.log(f"✅ Collated {collated_count} results")
        
        return success

    def test_ultimate_search(self):
        """Test ultimate search functionality"""
        self.log("\n=== ULTIMATE SEARCH TESTS ===")
        
        # Test get ultimate search results
        success, response = self.run_test(
            "Ultimate Search Results",
            "GET",
            "/ultimate-search",
            200,
            params={
                "page": 1,
                "aggregation": "and_or"
            }
        )
        
        if success:
            total_results = response.get('total', 0)
            self.log(f"✅ Ultimate search returned {total_results} total results")
        
        # Test ultimate search stats
        success, response = self.run_test(
            "Ultimate Search Stats",
            "GET",
            "/ultimate-search/stats",
            200
        )
        
        return success

    def test_user_settings(self):
        """Test user settings"""
        self.log("\n=== USER SETTINGS TESTS ===")
        
        # Test update user settings
        success, response = self.run_test(
            "Update User Settings",
            "PUT",
            "/users/settings",
            200,
            data={
                "ultimate_search_public": True,
                "friends_visible": False
            }
        )
        
        return success

    def test_payment_endpoints(self):
        """Test payment related endpoints"""
        self.log("\n=== PAYMENT TESTS ===")
        
        # Test get payment link
        success, response = self.run_test(
            "Get Payment Link",
            "GET",
            "/payment/link",
            200
        )
        
        if success and 'payment_url' in response:
            self.log(f"✅ Payment URL: {response['payment_url']}")
        
        return success

    def test_social_features(self):
        """Test social features - groups, pages, posts, comments"""
        self.log("\n=== SOCIAL FEATURES TESTS ===")
        
        # Test create group
        success, response = self.run_test(
            "Create Group",
            "POST",
            "/groups",
            200,
            data={
                "name": "Test Group",
                "description": "A test group for API testing",
                "is_public": True
            }
        )
        
        group_id = None
        if success and 'id' in response:
            group_id = response['id']
            self.log(f"✅ Group created with ID: {group_id}")
        
        # Test get groups
        success, response = self.run_test(
            "Get Groups",
            "GET",
            "/groups",
            200
        )
        
        if success:
            self.log(f"✅ Found {len(response)} groups")
        
        # Test create page
        success, response = self.run_test(
            "Create Page",
            "POST",
            "/pages",
            200,
            data={
                "name": "Test Page",
                "description": "A test page for API testing",
                "category": "Technology"
            }
        )
        
        page_id = None
        if success and 'id' in response:
            page_id = response['id']
            self.log(f"✅ Page created with ID: {page_id}")
        
        # Test get pages
        success, response = self.run_test(
            "Get Pages",
            "GET",
            "/pages",
            200
        )
        
        if success:
            self.log(f"✅ Found {len(response)} pages")
        
        # Test create post
        success, response = self.run_test(
            "Create Post",
            "POST",
            "/posts",
            200,
            data={
                "content": "This is a test post for API testing",
                "images": []
            }
        )
        
        post_id = None
        if success and 'id' in response:
            post_id = response['id']
            self.log(f"✅ Post created with ID: {post_id}")
        
        # Test get feed
        success, response = self.run_test(
            "Get Feed",
            "GET",
            "/feed",
            200
        )
        
        if success:
            self.log(f"✅ Feed returned {len(response)} posts")
        
        # Test react to post
        if post_id:
            success, response = self.run_test(
                "React to Post",
                "POST",
                f"/posts/{post_id}/react",
                200,
                data={"reaction_type": "Like"}
            )
        
        # Test create comment
        if post_id:
            success, response = self.run_test(
                "Create Comment",
                "POST",
                "/comments",
                200,
                data={
                    "content": "This is a test comment",
                    "post_id": post_id
                }
            )
            
            if success and 'id' in response:
                comment_id = response['id']
                self.log(f"✅ Comment created with ID: {comment_id}")
        
        # Test get comments
        if post_id:
            success, response = self.run_test(
                "Get Comments",
                "GET",
                "/comments",
                200,
                params={"post_id": post_id}
            )
            
            if success:
                self.log(f"✅ Found {len(response)} comments for post")
        
        return success

    def test_cleanup(self):
        """Clean up test data"""
        self.log("\n=== CLEANUP ===")
        
        # Delete the test category
        if self.category_id:
            success, response = self.run_test(
                "Delete Test Category",
                "DELETE",
                f"/categories/{self.category_id}",
                200
            )
        
        # Test logout
        success, response = self.run_test(
            "Logout",
            "POST",
            "/auth/logout",
            200
        )
        
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting InfoPilot API Tests")
        self.log(f"📍 Testing against: {self.base_url}")
        
        try:
            # Run test suites
            if not self.test_health_check():
                self.log("❌ Health check failed, stopping tests")
                return False
            
            if not self.test_authentication():
                self.log("❌ Authentication failed, stopping tests")
                return False
            
            self.test_categories()
            self.test_search_and_collate()
            self.test_ultimate_search()
            self.test_user_settings()
            self.test_payment_endpoints()
            self.test_social_features()
            self.test_cleanup()
            
        except Exception as e:
            self.log(f"❌ Unexpected error: {str(e)}")
            return False
        
        # Print final results
        self.log(f"\n📊 FINAL RESULTS:")
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            self.log("🎉 All tests passed!")
            return True
        else:
            failed = self.tests_run - self.tests_passed
            self.log(f"⚠️  {failed} tests failed")
            return False

def main():
    tester = InfoPilotAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())