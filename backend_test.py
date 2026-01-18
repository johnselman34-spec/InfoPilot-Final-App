#!/usr/bin/env python3
"""
InfoPilot Explorer Backend API Testing
Tests all endpoints for the book store and food truck functionality
"""

import requests
import sys
import json
from datetime import datetime

class InfoPilotAPITester:
    def __init__(self, base_url="https://toppilot-hub.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.passed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.passed_tests.append(name)
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:500]
                })
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if success and response.text else {}

        except Exception as e:
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_book_info(self):
        """Test book information endpoint"""
        return self.run_test("Book Info", "GET", "book", 200)

    def test_book_prices(self):
        """Test book prices endpoint"""
        success, response = self.run_test("Book Prices", "GET", "book/prices", 200)
        if success:
            # Verify expected prices (as per requirements)
            expected_prices = {"ebook": 4.99, "paperback": 17.90, "hardcover": 24.99}
            for format_type, expected_price in expected_prices.items():
                if format_type in response and response[format_type] == expected_price:
                    print(f"   ✅ {format_type}: ${response[format_type]} (correct)")
                else:
                    print(f"   ❌ {format_type}: Expected ${expected_price}, got ${response.get(format_type, 'missing')}")
        return success, response

    def test_company_info(self):
        """Test company information endpoint"""
        return self.run_test("Company Info", "GET", "company", 200)

    def test_infopilot_plans(self):
        """Test InfoPilot subscription plans endpoint"""
        success, response = self.run_test("InfoPilot Plans", "GET", "infopilot/plans", 200)
        if success:
            # Verify expected plans
            if 'monthly' in response and 'yearly' in response:
                monthly_price = response['monthly'].get('price', 0)
                yearly_price = response['yearly'].get('price', 0)
                print(f"   ✅ Monthly plan: ${monthly_price}")
                print(f"   ✅ Yearly plan: ${yearly_price}")
                if monthly_price == 1.00:
                    print(f"   ✅ Monthly price correct: $1.00")
                else:
                    print(f"   ❌ Monthly price incorrect: Expected $1.00, got ${monthly_price}")
                if yearly_price == 9.98:
                    print(f"   ✅ Yearly price correct: $9.98")
                else:
                    print(f"   ❌ Yearly price incorrect: Expected $9.98, got ${yearly_price}")
        return success, response

    def test_book_order(self):
        """Test book order creation"""
        order_data = {
            "customer_name": "Test Customer",
            "email": "test@example.com",
            "book_format": "ebook",
            "quantity": 1
        }
        return self.run_test("Book Order Creation", "POST", "book/order", 200, order_data)

    def test_book_orders_list(self):
        """Test getting book orders list"""
        return self.run_test("Book Orders List", "GET", "book/orders", 200)

    def test_food_menu(self):
        """Test food menu endpoint"""
        success, response = self.run_test("Food Menu", "GET", "food/menu", 200)
        if success and 'menu' in response:
            menu_items = response['menu']
            print(f"   Found {len(menu_items)} menu items:")
            for item in menu_items:
                print(f"   - {item.get('name', 'Unknown')} (${item.get('price', 'N/A')})")
            
            # Check if we have the expected 5 items
            if len(menu_items) == 5:
                print("   ✅ Correct number of menu items (5)")
            else:
                print(f"   ❌ Expected 5 menu items, found {len(menu_items)}")
        return success, response

    def test_food_order(self):
        """Test food order creation"""
        order_data = {
            "customer_name": "Test Customer",
            "phone": "555-123-4567",
            "email": "test@example.com",
            "items": [
                {
                    "item_name": "German Beef Rouladen",
                    "quantity": 1,
                    "price": 18.99
                }
            ],
            "pickup_time": "ASAP"
        }
        return self.run_test("Food Order Creation", "POST", "food/order", 200, order_data)

    def test_food_orders_list(self):
        """Test getting food orders list"""
        return self.run_test("Food Orders List", "GET", "food/orders", 200)

    def test_testimonials(self):
        """Test testimonials endpoint"""
        success, response = self.run_test("Testimonials", "GET", "testimonials", 200)
        if success and 'testimonials' in response:
            testimonials = response['testimonials']
            print(f"   Found {len(testimonials)} testimonials")
            book_reviews = [t for t in testimonials if t.get('review_type') == 'book']
            food_reviews = [t for t in testimonials if t.get('review_type') == 'food']
            print(f"   - Book reviews: {len(book_reviews)}")
            print(f"   - Food reviews: {len(food_reviews)}")
        return success, response

    def test_newsletter_signup(self):
        """Test newsletter signup"""
        signup_data = {
            "name": "Test User",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "signup_type": "general"
        }
        return self.run_test("Newsletter Signup", "POST", "newsletter/signup", 200, signup_data)

    def test_newsletter_subscribers(self):
        """Test getting newsletter subscribers"""
        return self.run_test("Newsletter Subscribers", "GET", "newsletter/subscribers", 200)

    def test_contact_message(self):
        """Test contact message submission"""
        contact_data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test Message",
            "message": "This is a test message from the API tester."
        }
        return self.run_test("Contact Message", "POST", "contact", 200, contact_data)

    def test_contact_messages_list(self):
        """Test getting contact messages list"""
        return self.run_test("Contact Messages List", "GET", "contact/messages", 200)

    def test_stats(self):
        """Test stats endpoint"""
        return self.run_test("Stats", "GET", "stats", 200)

    def test_status_check(self):
        """Test status check creation"""
        status_data = {
            "client_name": "API Tester"
        }
        return self.run_test("Status Check", "POST", "status", 200, status_data)

    def test_status_checks_list(self):
        """Test getting status checks list"""
        return self.run_test("Status Checks List", "GET", "status", 200)

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting InfoPilot Explorer API Tests")
        print("=" * 50)

        # Basic API tests
        self.test_root_endpoint()
        
        # Company and InfoPilot tests
        print("\n🏢 COMPANY & INFOPILOT TESTS")
        print("-" * 30)
        self.test_company_info()
        self.test_infopilot_plans()
        
        # Book-related tests
        print("\n📚 BOOK TESTS")
        print("-" * 30)
        self.test_book_info()
        self.test_book_prices()
        self.test_book_order()
        self.test_book_orders_list()

        # Food-related tests
        print("\n🍽️ FOOD TESTS")
        print("-" * 30)
        self.test_food_menu()
        self.test_food_order()
        self.test_food_orders_list()

        # Communication tests
        print("\n📬 COMMUNICATION TESTS")
        print("-" * 30)
        self.test_testimonials()
        self.test_newsletter_signup()
        self.test_newsletter_subscribers()
        self.test_contact_message()
        self.test_contact_messages_list()

        # System tests
        print("\n⚙️ SYSTEM TESTS")
        print("-" * 30)
        self.test_stats()
        self.test_status_check()
        self.test_status_checks_list()

        # Print final results
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS")
        print("=" * 50)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")

        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for failure in self.failed_tests:
                print(f"  - {failure.get('test', 'Unknown')}")
                if 'error' in failure:
                    print(f"    Error: {failure['error']}")
                elif 'expected' in failure:
                    print(f"    Expected: {failure['expected']}, Got: {failure['actual']}")

        if self.passed_tests:
            print(f"\n✅ PASSED TESTS ({len(self.passed_tests)}):")
            for test in self.passed_tests:
                print(f"  - {test}")

        return len(self.failed_tests) == 0

def main():
    """Main test runner"""
    tester = InfoPilotAPITester()
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())