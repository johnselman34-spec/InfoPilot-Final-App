#!/usr/bin/env python3
"""
InfoPilot Backend API Testing Suite
Tests all backend endpoints to identify issues causing blank screen
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, Optional
import sys

# Backend URL from frontend environment
BACKEND_URL = "https://infopilot-search.preview.emergentagent.com/api"

class InfoPilotTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_user_id = None
        self.test_category_id = None
        self.results = {
            "health_check": {"status": "pending", "details": ""},
            "user_registration": {"status": "pending", "details": ""},
            "user_login": {"status": "pending", "details": ""},
            "auth_verification": {"status": "pending", "details": ""},
            "subscription_endpoint": {"status": "pending", "details": ""},
            "subscription_verification": {"status": "pending", "details": ""},
            "category_creation": {"status": "pending", "details": ""},
            "category_retrieval": {"status": "pending", "details": ""},
            "google_search": {"status": "pending", "details": ""},
            "admin_settings": {"status": "pending", "details": ""},
            "collate_search": {"status": "pending", "details": ""}
        }
    
    async def setup_session(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
    
    async def cleanup_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                          headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{BACKEND_URL}{endpoint}"
        request_headers = {"Content-Type": "application/json"}
        
        if headers:
            request_headers.update(headers)
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    response_text = await response.text()
                    return {
                        "status_code": response.status,
                        "data": await self._parse_response(response_text),
                        "success": response.status < 400
                    }
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    response_text = await response.text()
                    return {
                        "status_code": response.status,
                        "data": await self._parse_response(response_text),
                        "success": response.status < 400
                    }
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data, headers=request_headers) as response:
                    response_text = await response.text()
                    return {
                        "status_code": response.status,
                        "data": await self._parse_response(response_text),
                        "success": response.status < 400
                    }
            elif method.upper() == "DELETE":
                async with self.session.delete(url, headers=request_headers) as response:
                    response_text = await response.text()
                    return {
                        "status_code": response.status,
                        "data": await self._parse_response(response_text),
                        "success": response.status < 400
                    }
        except Exception as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False
            }
    
    async def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse response text to JSON"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {"raw_response": response_text}
    
    async def test_health_check(self):
        """Test API health endpoint"""
        print("🔍 Testing health check...")
        
        response = await self.make_request("GET", "/health")
        
        if response["success"] and response["data"].get("status") == "healthy":
            self.results["health_check"]["status"] = "✅ PASS"
            self.results["health_check"]["details"] = "Health check successful"
            print("✅ Health check: PASS")
        else:
            self.results["health_check"]["status"] = "❌ FAIL"
            self.results["health_check"]["details"] = f"Status: {response['status_code']}, Data: {response['data']}"
            print(f"❌ Health check: FAIL - {response['data']}")
    
    async def test_user_registration(self):
        """Test user registration endpoint"""
        print("🔍 Testing user registration...")
        
        test_user_data = {
            "username": "testuser123",
            "email": "test@infopilot.com",
            "password": "TestPass123"
        }
        
        response = await self.make_request("POST", "/auth/register", test_user_data)
        
        if response["success"] and response["data"].get("success"):
            self.results["user_registration"]["status"] = "✅ PASS"
            self.results["user_registration"]["details"] = "User registration successful"
            self.auth_token = response["data"].get("token")
            self.test_user_id = response["data"].get("user", {}).get("id")
            print("✅ User registration: PASS")
        else:
            self.results["user_registration"]["status"] = "❌ FAIL"
            self.results["user_registration"]["details"] = f"Status: {response['status_code']}, Data: {response['data']}"
            print(f"❌ User registration: FAIL - {response['data']}")
    
    async def test_user_login(self):
        """Test user login endpoint"""
        print("🔍 Testing user login...")
        
        login_data = {
            "username": "testuser_infopilot_2024",
            "password": "SecurePassword123!"
        }
        
        response = await self.make_request("POST", "/auth/login", login_data)
        
        if response["success"] and response["data"].get("success"):
            self.results["user_login"]["status"] = "✅ PASS"
            self.results["user_login"]["details"] = "User login successful"
            # Update token in case registration failed but login worked
            if not self.auth_token:
                self.auth_token = response["data"].get("token")
                self.test_user_id = response["data"].get("user", {}).get("id")
            print("✅ User login: PASS")
        else:
            self.results["user_login"]["status"] = "❌ FAIL"
            self.results["user_login"]["details"] = f"Status: {response['status_code']}, Data: {response['data']}"
            print(f"❌ User login: FAIL - {response['data']}")
    
    async def test_auth_verification(self):
        """Test authentication verification"""
        print("🔍 Testing authentication verification...")
        
        if not self.auth_token:
            self.results["auth_verification"]["status"] = "❌ FAIL"
            self.results["auth_verification"]["details"] = "No auth token available"
            print("❌ Auth verification: FAIL - No token")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.make_request("GET", "/auth/me", headers=headers)
        
        if response["success"] and response["data"].get("username"):
            self.results["auth_verification"]["status"] = "✅ PASS"
            self.results["auth_verification"]["details"] = "Authentication verification successful"
            print("✅ Auth verification: PASS")
        else:
            self.results["auth_verification"]["status"] = "❌ FAIL"
            self.results["auth_verification"]["details"] = f"Status: {response['status_code']}, Data: {response['data']}"
            print(f"❌ Auth verification: FAIL - {response['data']}")
    
    async def test_subscription_endpoint(self):
        """Test the NEW subscription endpoint"""
        print("🔍 Testing subscription endpoint...")
        
        if not self.auth_token:
            self.results["subscription_endpoint"]["status"] = "❌ FAIL"
            self.results["subscription_endpoint"]["details"] = "No auth token available"
            print("❌ Subscription endpoint: FAIL - No token")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.make_request("POST", "/users/subscribe", headers=headers)
        
        if response["success"] and response["data"].get("success"):
            self.results["subscription_endpoint"]["status"] = "✅ PASS"
            self.results["subscription_endpoint"]["details"] = f"Subscription activated: {response['data'].get('message', 'Success')}"
            print("✅ Subscription endpoint: PASS")
        else:
            self.results["subscription_endpoint"]["status"] = "❌ FAIL"
            self.results["subscription_endpoint"]["details"] = f"Status: {response['status_code']}, Data: {response['data']}"
            print(f"❌ Subscription endpoint: FAIL - {response['data']}")
    
    async def test_subscription_verification(self):
        """Test that subscription status was updated correctly"""
        print("🔍 Testing subscription verification...")
        
        if not self.auth_token:
            self.results["subscription_verification"]["status"] = "❌ FAIL"
            self.results["subscription_verification"]["details"] = "No auth token available"
            print("❌ Subscription verification: FAIL - No token")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.make_request("GET", "/auth/me", headers=headers)
        
        if response["success"] and response["data"].get("subscription_status") == "paid":
            self.results["subscription_verification"]["status"] = "✅ PASS"
            self.results["subscription_verification"]["details"] = "Subscription status correctly updated to 'paid'"
            print("✅ Subscription verification: PASS")
        else:
            subscription_status = response["data"].get("subscription_status", "unknown") if response["success"] else "error"
            self.results["subscription_verification"]["status"] = "❌ FAIL"
            self.results["subscription_verification"]["details"] = f"Subscription status: {subscription_status}, Expected: paid"
            print(f"❌ Subscription verification: FAIL - Status: {subscription_status}")

    async def test_category_creation(self):
        """Test category creation endpoint with InfoPilot 2.0 protocol"""
        print("🔍 Testing category creation...")
        
        if not self.auth_token:
            self.results["category_creation"]["status"] = "❌ FAIL"
            self.results["category_creation"]["details"] = "No auth token available"
            print("❌ Category creation: FAIL - No token")
            return
        
        category_data = {
            "name": "Tech News Analysis",
            "protocol": "InfoPilot 2.0: technology AND (artificial intelligence OR machine learning) AND news",
            "is_public": False
        }
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.make_request("POST", "/categories", category_data, headers)
        
        if response["success"] and response["data"].get("success"):
            self.results["category_creation"]["status"] = "✅ PASS"
            self.results["category_creation"]["details"] = "Category creation successful with InfoPilot 2.0 protocol"
            self.test_category_id = response["data"].get("category", {}).get("id")
            print("✅ Category creation: PASS")
        else:
            self.results["category_creation"]["status"] = "❌ FAIL"
            self.results["category_creation"]["details"] = f"Status: {response['status_code']}, Data: {response['data']}"
            print(f"❌ Category creation: FAIL - {response['data']}")
    
    async def test_category_retrieval(self):
        """Test category retrieval endpoint"""
        print("🔍 Testing category retrieval...")
        
        if not self.auth_token:
            self.results["category_retrieval"]["status"] = "❌ FAIL"
            self.results["category_retrieval"]["details"] = "No auth token available"
            print("❌ Category retrieval: FAIL - No token")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.make_request("GET", "/categories", headers=headers)
        
        if response["success"] and response["data"].get("success"):
            categories = response["data"].get("categories", [])
            self.results["category_retrieval"]["status"] = "✅ PASS"
            self.results["category_retrieval"]["details"] = f"Retrieved {len(categories)} categories"
            print(f"✅ Category retrieval: PASS - Found {len(categories)} categories")
        else:
            self.results["category_retrieval"]["status"] = "❌ FAIL"
            self.results["category_retrieval"]["details"] = f"Status: {response['status_code']}, Data: {response['data']}"
            print(f"❌ Category retrieval: FAIL - {response['data']}")
    
    async def test_google_search(self):
        """Test Google search endpoint"""
        print("🔍 Testing Google search...")
        
        response = await self.make_request("GET", "/search/google?q=artificial intelligence")
        
        if response["success"] and response["data"].get("success"):
            results = response["data"].get("results", [])
            self.results["google_search"]["status"] = "✅ PASS"
            self.results["google_search"]["details"] = f"Search returned {len(results)} results"
            print(f"✅ Google search: PASS - Found {len(results)} results")
        else:
            self.results["google_search"]["status"] = "❌ FAIL"
            self.results["google_search"]["details"] = f"Status: {response['status_code']}, Data: {response['data']}"
            print(f"❌ Google search: FAIL - {response['data']}")
    
    async def test_admin_settings(self):
        """Test admin settings endpoint"""
        print("🔍 Testing admin settings...")
        
        response = await self.make_request("GET", "/admin/settings")
        
        if response["success"] and response["data"].get("success"):
            self.results["admin_settings"]["status"] = "✅ PASS"
            self.results["admin_settings"]["details"] = "Admin settings retrieved successfully"
            print("✅ Admin settings: PASS")
        else:
            self.results["admin_settings"]["status"] = "❌ FAIL"
            self.results["admin_settings"]["details"] = f"Status: {response['status_code']}, Data: {response['data']}"
            print(f"❌ Admin settings: FAIL - {response['data']}")
    
    async def test_collate_search(self):
        """Test collate search functionality"""
        print("🔍 Testing collate search...")
        
        if not self.auth_token or not self.test_category_id:
            self.results["collate_search"]["status"] = "❌ FAIL"
            self.results["collate_search"]["details"] = "No auth token or category ID available"
            print("❌ Collate search: FAIL - Missing prerequisites")
            return
        
        collate_data = {
            "category_id": self.test_category_id,
            "search_query": "artificial intelligence research"
        }
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.make_request("POST", "/search/collate", collate_data, headers)
        
        if response["success"] and response["data"].get("success"):
            processed_count = response["data"].get("processed_count", 0)
            self.results["collate_search"]["status"] = "✅ PASS"
            self.results["collate_search"]["details"] = f"Collated {processed_count} results"
            print(f"✅ Collate search: PASS - Processed {processed_count} results")
        else:
            self.results["collate_search"]["status"] = "❌ FAIL"
            self.results["collate_search"]["details"] = f"Status: {response['status_code']}, Data: {response['data']}"
            print(f"❌ Collate search: FAIL - {response['data']}")
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting InfoPilot Backend API Tests")
        print(f"🌐 Testing against: {BACKEND_URL}")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Test in logical order
            await self.test_health_check()
            await self.test_user_registration()
            await self.test_user_login()
            await self.test_auth_verification()
            await self.test_category_creation()
            await self.test_category_retrieval()
            await self.test_google_search()
            await self.test_admin_settings()
            await self.test_collate_search()
            
        finally:
            await self.cleanup_session()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.results.items():
            status = result["status"]
            details = result["details"]
            print(f"{status} {test_name.replace('_', ' ').title()}: {details}")
            
            if "✅" in status:
                passed += 1
            elif "❌" in status:
                failed += 1
        
        print(f"\n📈 OVERALL: {passed} passed, {failed} failed")
        
        if failed > 0:
            print("\n🚨 CRITICAL ISSUES FOUND:")
            for test_name, result in self.results.items():
                if "❌" in result["status"]:
                    print(f"   • {test_name.replace('_', ' ').title()}: {result['details']}")
        
        return self.results

async def main():
    """Main test runner"""
    tester = InfoPilotTester()
    results = await tester.run_all_tests()
    
    # Return exit code based on results
    failed_tests = sum(1 for result in results.values() if "❌" in result["status"])
    return failed_tests

if __name__ == "__main__":
    try:
        failed_count = asyncio.run(main())
        sys.exit(failed_count)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner error: {str(e)}")
        sys.exit(1)