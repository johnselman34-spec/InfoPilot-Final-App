#!/usr/bin/env python3
"""
InfoPilot Backend API Testing Suite
Tests authentication, Stripe payment integration, and subscription APIs
"""

import requests
import json
import uuid
from datetime import datetime
import time

# Backend URL from frontend .env
BACKEND_URL = "https://infopilot-1.preview.emergentagent.com/api"

class InfoPilotTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_user_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "testpass123"
        self.test_username = f"testuser_{uuid.uuid4().hex[:6]}"
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def test_health_check(self):
        """Test basic API health"""
        self.log("Testing API health check...")
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Health check passed: {data}")
                return True
            else:
                self.log(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Health check error: {e}")
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        self.log(f"Testing user registration with email: {self.test_user_email}")
        try:
            payload = {
                "username": self.test_username,
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.log(f"✅ Registration successful: {data['user']['username']}")
                self.log(f"✅ Auth token received: {self.auth_token[:20]}...")
                return True
            else:
                self.log(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Registration error: {e}")
            return False
    
    def test_user_login(self):
        """Test user login"""
        self.log(f"Testing user login with email: {self.test_user_email}")
        try:
            payload = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.log(f"✅ Login successful: {data['user']['username']}")
                return True
            else:
                self.log(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Login error: {e}")
            return False
    
    def test_subscription_info(self):
        """Test GET /api/subscription/info"""
        self.log("Testing subscription info API...")
        try:
            response = self.session.get(f"{BACKEND_URL}/subscription/info")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Subscription info retrieved:")
                self.log(f"   Price: ${data.get('price')}")
                self.log(f"   Regular Price: ${data.get('regular_price')}")
                self.log(f"   Sale Active: {data.get('is_sale_active')}")
                self.log(f"   Sale End Date: {data.get('sale_end_date')}")
                
                # Verify expected sale pricing
                if data.get('price') == 0.75 and data.get('is_sale_active') == True:
                    self.log("✅ Sale pricing correct: $0.75 with active sale")
                    return True
                else:
                    self.log(f"❌ Sale pricing incorrect: Expected $0.75 with active sale")
                    return False
            else:
                self.log(f"❌ Subscription info failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Subscription info error: {e}")
            return False
    
    def test_create_payment_intent(self):
        """Test POST /api/payments/create-intent"""
        self.log("Testing Stripe payment intent creation...")
        
        if not self.auth_token:
            self.log("❌ No auth token available for payment test")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {"item_type": "subscription"}
            
            response = self.session.post(
                f"{BACKEND_URL}/payments/create-intent", 
                json=payload, 
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                client_secret = data.get("client_secret")
                payment_intent_id = data.get("payment_intent_id")
                amount = data.get("amount")
                
                self.log(f"✅ Payment intent created successfully:")
                self.log(f"   Client Secret: {client_secret[:20]}...")
                self.log(f"   Payment Intent ID: {payment_intent_id}")
                self.log(f"   Amount: ${amount}")
                
                # Verify amount is correct for sale price
                if amount == 0.75:
                    self.log("✅ Payment amount correct: $0.75")
                    return True
                else:
                    self.log(f"❌ Payment amount incorrect: Expected $0.75, got ${amount}")
                    return False
            else:
                self.log(f"❌ Payment intent creation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Payment intent creation error: {e}")
            return False
    
    def test_stripe_config(self):
        """Test GET /api/payments/config"""
        self.log("Testing Stripe configuration API...")
        try:
            response = self.session.get(f"{BACKEND_URL}/payments/config")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Stripe config retrieved:")
                self.log(f"   Publishable Key: {data.get('publishable_key')[:20]}...")
                self.log(f"   Sale Price: ${data.get('sale_price')}")
                self.log(f"   Regular Price: ${data.get('regular_price')}")
                self.log(f"   Sale Active: {data.get('is_sale_active')}")
                
                # Verify Stripe keys are present
                if data.get('publishable_key') and data.get('publishable_key').startswith('pk_'):
                    self.log("✅ Stripe publishable key present and valid format")
                    return True
                else:
                    self.log("❌ Stripe publishable key missing or invalid format")
                    return False
            else:
                self.log(f"❌ Stripe config failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Stripe config error: {e}")
            return False
    
    def test_auth_me(self):
        """Test GET /api/auth/me"""
        self.log("Testing auth/me endpoint...")
        
        if not self.auth_token:
            self.log("❌ No auth token available for auth/me test")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{BACKEND_URL}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Auth/me successful:")
                self.log(f"   Username: {data.get('username')}")
                self.log(f"   Email: {data.get('email')}")
                self.log(f"   Is Paid: {data.get('is_paid')}")
                self.log(f"   Is Admin: {data.get('is_admin')}")
                return True
            else:
                self.log(f"❌ Auth/me failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Auth/me error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        self.log("=" * 60)
        self.log("STARTING INFOPILOT BACKEND API TESTS")
        self.log("=" * 60)
        
        results = {}
        
        # Test 1: Health Check
        results['health_check'] = self.test_health_check()
        
        # Test 2: User Registration
        results['user_registration'] = self.test_user_registration()
        
        # Test 3: User Login
        results['user_login'] = self.test_user_login()
        
        # Test 4: Auth Me
        results['auth_me'] = self.test_auth_me()
        
        # Test 5: Subscription Info
        results['subscription_info'] = self.test_subscription_info()
        
        # Test 6: Stripe Config
        results['stripe_config'] = self.test_stripe_config()
        
        # Test 7: Create Payment Intent (Stripe Integration)
        results['create_payment_intent'] = self.test_create_payment_intent()
        
        # Summary
        self.log("=" * 60)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
            if result:
                passed += 1
        
        self.log("=" * 60)
        self.log(f"OVERALL: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED!")
        else:
            self.log(f"⚠️  {total - passed} tests failed")
        
        return results

if __name__ == "__main__":
    tester = InfoPilotTester()
    results = tester.run_all_tests()