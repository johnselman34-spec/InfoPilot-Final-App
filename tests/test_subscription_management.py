"""
InfoPilot Explorer - Subscription Management Tests
Tests for new subscription management endpoints:
- GET /api/stripe/subscription - returns user subscription status
- GET /api/stripe/billing-history - returns billing history
- POST /api/stripe/cancel-subscription - cancels active subscription
- POST /api/stripe/reactivate-subscription - reactivates cancelled subscription
- POST /api/stripe/upgrade-subscription - upgrades subscription plan
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infojethub.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "testuser_new@example.com"
TEST_USER_PASSWORD = "password123"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for test user"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestSubscriptionEndpoint:
    """GET /api/stripe/subscription - User subscription status tests"""
    
    def test_get_subscription_authenticated(self, authenticated_client):
        """GET /api/stripe/subscription should return subscription details"""
        response = authenticated_client.get(f"{BASE_URL}/api/stripe/subscription")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure - all expected fields should be present
        expected_fields = [
            "subscription_active",
            "subscription_type",
            "subscription_started_at",
            "subscription_end_date",
            "subscription_cancelled",
            "subscription_cancelled_at",
            "package_name",
            "package_amount",
            "wallet_balance"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify data types
        assert isinstance(data["subscription_active"], bool)
        assert isinstance(data["subscription_cancelled"], bool)
        assert isinstance(data["wallet_balance"], (int, float))
        
        print(f"✓ Subscription endpoint returned:")
        print(f"  - subscription_active: {data['subscription_active']}")
        print(f"  - subscription_type: {data['subscription_type']}")
        print(f"  - package_name: {data['package_name']}")
        print(f"  - wallet_balance: ${data['wallet_balance']}")
    
    def test_get_subscription_requires_auth(self):
        """GET /api/stripe/subscription without auth should fail"""
        unauthenticated = requests.Session()
        unauthenticated.headers.update({"Content-Type": "application/json"})
        
        response = unauthenticated.get(f"{BASE_URL}/api/stripe/subscription")
        
        assert response.status_code in [401, 403]
        print(f"✓ Unauthenticated subscription request correctly rejected with {response.status_code}")


class TestBillingHistoryEndpoint:
    """GET /api/stripe/billing-history - Billing history tests"""
    
    def test_get_billing_history_authenticated(self, authenticated_client):
        """GET /api/stripe/billing-history should return billing history"""
        response = authenticated_client.get(f"{BASE_URL}/api/stripe/billing-history")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "billing_history" in data
        assert "subscription_events" in data
        assert "total_spent" in data
        
        # Verify data types
        assert isinstance(data["billing_history"], list)
        assert isinstance(data["subscription_events"], list)
        assert isinstance(data["total_spent"], (int, float))
        
        print(f"✓ Billing history endpoint returned:")
        print(f"  - billing_history items: {len(data['billing_history'])}")
        print(f"  - subscription_events: {len(data['subscription_events'])}")
        print(f"  - total_spent: ${data['total_spent']}")
        
        # If there are billing items, verify structure
        if len(data["billing_history"]) > 0:
            item = data["billing_history"][0]
            expected_item_fields = ["id", "type", "description", "amount", "currency", "status", "date"]
            for field in expected_item_fields:
                assert field in item, f"Missing billing item field: {field}"
            print(f"  - First item: {item['description']} - ${item['amount']} ({item['status']})")
    
    def test_get_billing_history_requires_auth(self):
        """GET /api/stripe/billing-history without auth should fail"""
        unauthenticated = requests.Session()
        unauthenticated.headers.update({"Content-Type": "application/json"})
        
        response = unauthenticated.get(f"{BASE_URL}/api/stripe/billing-history")
        
        assert response.status_code in [401, 403]
        print(f"✓ Unauthenticated billing history request correctly rejected with {response.status_code}")


class TestCancelSubscriptionEndpoint:
    """POST /api/stripe/cancel-subscription - Cancel subscription tests"""
    
    def test_cancel_subscription_no_active_subscription(self, authenticated_client):
        """POST /api/stripe/cancel-subscription without active subscription should fail"""
        # First check if user has active subscription
        sub_response = authenticated_client.get(f"{BASE_URL}/api/stripe/subscription")
        sub_data = sub_response.json()
        
        if not sub_data.get("subscription_active"):
            # User has no active subscription - should get 400
            response = authenticated_client.post(f"{BASE_URL}/api/stripe/cancel-subscription")
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            print(f"✓ Cancel without active subscription correctly rejected: {data['detail']}")
        else:
            # User has active subscription - skip this test
            pytest.skip("User has active subscription - cannot test 'no subscription' error")
    
    def test_cancel_subscription_requires_auth(self):
        """POST /api/stripe/cancel-subscription without auth should fail"""
        unauthenticated = requests.Session()
        unauthenticated.headers.update({"Content-Type": "application/json"})
        
        response = unauthenticated.post(f"{BASE_URL}/api/stripe/cancel-subscription")
        
        assert response.status_code in [401, 403]
        print(f"✓ Unauthenticated cancel request correctly rejected with {response.status_code}")


class TestReactivateSubscriptionEndpoint:
    """POST /api/stripe/reactivate-subscription - Reactivate subscription tests"""
    
    def test_reactivate_subscription_no_active_subscription(self, authenticated_client):
        """POST /api/stripe/reactivate-subscription without active subscription should fail"""
        # First check if user has active subscription
        sub_response = authenticated_client.get(f"{BASE_URL}/api/stripe/subscription")
        sub_data = sub_response.json()
        
        if not sub_data.get("subscription_active"):
            # User has no active subscription - should get 400
            response = authenticated_client.post(f"{BASE_URL}/api/stripe/reactivate-subscription")
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            print(f"✓ Reactivate without active subscription correctly rejected: {data['detail']}")
        else:
            # User has active subscription - check if it's cancelled
            if not sub_data.get("subscription_cancelled"):
                # Subscription is active but not cancelled - should get 400
                response = authenticated_client.post(f"{BASE_URL}/api/stripe/reactivate-subscription")
                
                assert response.status_code == 400
                data = response.json()
                assert "detail" in data
                print(f"✓ Reactivate non-cancelled subscription correctly rejected: {data['detail']}")
            else:
                pytest.skip("User has cancelled subscription - cannot test 'not cancelled' error")
    
    def test_reactivate_subscription_requires_auth(self):
        """POST /api/stripe/reactivate-subscription without auth should fail"""
        unauthenticated = requests.Session()
        unauthenticated.headers.update({"Content-Type": "application/json"})
        
        response = unauthenticated.post(f"{BASE_URL}/api/stripe/reactivate-subscription")
        
        assert response.status_code in [401, 403]
        print(f"✓ Unauthenticated reactivate request correctly rejected with {response.status_code}")


class TestUpgradeSubscriptionEndpoint:
    """POST /api/stripe/upgrade-subscription - Upgrade subscription tests"""
    
    def test_upgrade_subscription_invalid_package(self, authenticated_client):
        """POST /api/stripe/upgrade-subscription with invalid package should fail"""
        response = authenticated_client.post(f"{BASE_URL}/api/stripe/upgrade-subscription", json={
            "new_package": "invalid_package"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        print(f"✓ Invalid package type correctly rejected: {data['detail']}")
    
    def test_upgrade_subscription_valid_package(self, authenticated_client):
        """POST /api/stripe/upgrade-subscription with valid package should return redirect info"""
        # First check current subscription
        sub_response = authenticated_client.get(f"{BASE_URL}/api/stripe/subscription")
        sub_data = sub_response.json()
        
        # Choose a different package than current
        current_type = sub_data.get("subscription_type")
        new_package = "yearly" if current_type == "monthly" else "monthly"
        
        response = authenticated_client.post(f"{BASE_URL}/api/stripe/upgrade-subscription", json={
            "new_package": new_package
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "action" in data
        assert "message" in data
        assert "package" in data
        assert "amount" in data
        
        assert data["action"] == "redirect_to_checkout"
        assert data["package"] == new_package
        
        print(f"✓ Upgrade subscription returned redirect info:")
        print(f"  - action: {data['action']}")
        print(f"  - package: {data['package']}")
        print(f"  - amount: ${data['amount']}")
    
    def test_upgrade_subscription_same_package(self, authenticated_client):
        """POST /api/stripe/upgrade-subscription with same package should fail"""
        # First check current subscription
        sub_response = authenticated_client.get(f"{BASE_URL}/api/stripe/subscription")
        sub_data = sub_response.json()
        
        current_type = sub_data.get("subscription_type")
        
        if current_type:
            # Try to upgrade to same package
            response = authenticated_client.post(f"{BASE_URL}/api/stripe/upgrade-subscription", json={
                "new_package": current_type
            })
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            print(f"✓ Upgrade to same package correctly rejected: {data['detail']}")
        else:
            # No current subscription - test with monthly
            response = authenticated_client.post(f"{BASE_URL}/api/stripe/upgrade-subscription", json={
                "new_package": "monthly"
            })
            
            # Should return redirect info since no current subscription
            assert response.status_code == 200
            print(f"✓ Upgrade without subscription returns redirect to checkout")
    
    def test_upgrade_subscription_requires_auth(self):
        """POST /api/stripe/upgrade-subscription without auth should fail"""
        unauthenticated = requests.Session()
        unauthenticated.headers.update({"Content-Type": "application/json"})
        
        response = unauthenticated.post(f"{BASE_URL}/api/stripe/upgrade-subscription", json={
            "new_package": "yearly"
        })
        
        assert response.status_code in [401, 403]
        print(f"✓ Unauthenticated upgrade request correctly rejected with {response.status_code}")


class TestTransactionsEndpoint:
    """GET /api/stripe/transactions - Transactions endpoint tests"""
    
    def test_get_transactions_authenticated(self, authenticated_client):
        """GET /api/stripe/transactions should return user's transactions"""
        response = authenticated_client.get(f"{BASE_URL}/api/stripe/transactions")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "transactions" in data
        assert isinstance(data["transactions"], list)
        
        print(f"✓ Transactions endpoint returned {len(data['transactions'])} transactions")
        
        # If there are transactions, verify structure
        if len(data["transactions"]) > 0:
            txn = data["transactions"][0]
            expected_fields = ["id", "session_id", "user_id", "amount", "status"]
            for field in expected_fields:
                assert field in txn, f"Missing transaction field: {field}"
            print(f"  - First transaction: ${txn.get('amount', 0)} ({txn.get('status', 'unknown')})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
