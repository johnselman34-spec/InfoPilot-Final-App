# InfoPilot Explorer - Product Requirements Document

**App Name:** InfoPilot Explorer  
**Company:** Top Pilot Enterprises, Inc.  
**Tagline:** "First in Flight with Monetization of Searches! It's a Bear! 🐻"  
**Author/Owner:** John Selman (JJSpilot24@gmail.com, 207-522-0894)  
**Location:** Brunswick, Maine

---

## 1. Integration Status ✅

| Integration | Status | Details |
|-------------|--------|---------|
| **Stripe Payments** | ✅ **LIVE** | Primary payment provider (test mode) |
| **Resend Email** | ✅ **LIVE** | API key configured, welcome emails sent |
| **DuckDuckGo Search** | ✅ **LIVE** | Real web search results |
| **PayPal Simple Payments** | ⚠️ **BLOCKED** | User account issues - needs resolution |
| **PayPal Orders API** | ⚠️ **BLOCKED** | Needs CLIENT_ID + SECRET after account fixed |

---

## 2. All Implemented Features

### ✅ Core Platform
- User authentication (register/login/logout)
- JWT-based session management with MongoDB
- InfoJet 2.0 Protocol Parser
- Category/Subcategory hierarchy
- Real DuckDuckGo Search Integration

### ✅ Stripe Integration (Primary Payment) - LIVE
- Stripe Checkout for subscriptions and marketplace purchases
- **Subscription Management Dashboard** (`/subscription`)
  - View current subscription status
  - Cancel/reactivate subscription
  - Billing history with past transactions
  - Wallet balance from marketplace sales
  - Change plan (monthly/yearly)
- **Subscription Checkout** (`/subscribe`)
  - Monthly plan: $1.00/mo
  - Yearly plan: $9.98/yr (Save 17%)
- Marketplace protocol purchases via Stripe
- 85% seller / 15% platform fee structure
- Payment success/cancel pages

### ✅ Email Integration (Resend) - LIVE
- Newsletter subscription with welcome email
- Unsubscribe functionality
- Admin newsletter sending
- Branded HTML email templates

### ✅ Search & UI
- Real web search via DuckDuckGo
- **Select All / Deselect All** buttons everywhere
- Document type classification
- Search aggregation modes

### ✅ All Pages Working
- HomePage, LoginPage
- UltimateSearchPage (with Select All/Deselect All)
- MapPage (Leaflet integration)
- ChatPage
- GroupsPage, PagesPage
- ReportsPage (with image upload + Select All/Deselect All)
- RevenuePage (PDF/CSV export)
- MarketplacePage (Stripe integration)
- ThemesPage (12 themes)
- TemplatesPage
- StatsPage (leaderboards)
- BookPage, FoodPage, InfoPilotPage
- **SubscriptionDashboard** (NEW)
- **SubscriptionCheckout** (NEW)
- PaymentSuccess, PaymentCancel

---

## 3. API Endpoints

### Stripe (`/api/stripe`)
- `GET /config` - Check Stripe configuration
- `POST /create-checkout` - Create checkout session
- `GET /status/{session_id}` - Get payment status
- `GET /transactions` - User's transaction history
- `GET /subscription` - Get subscription details (NEW)
- `GET /billing-history` - Get billing history (NEW)
- `POST /cancel-subscription` - Cancel subscription (NEW)
- `POST /reactivate-subscription` - Reactivate cancelled subscription (NEW)
- `POST /upgrade-subscription` - Change subscription plan (NEW)
- `POST /webhook` - Stripe webhooks

### Email (`/api/email`)
- `POST /subscribe` - Subscribe to newsletter
- `DELETE /unsubscribe` - Unsubscribe
- `GET /subscribers` - Get subscribers (admin)
- `POST /send-newsletter` - Send newsletter (admin)
- `GET /test` - Check config status

### PayPal (`/api/paypal`) - BLOCKED
- Backend routes ready but non-functional due to user account issues

---

## 4. Environment Variables

```env
# Backend .env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"

# Stripe - CONFIGURED ✅
STRIPE_API_KEY=sk_test_emergent

# Resend - CONFIGURED ✅
RESEND_API_KEY=re_8pZDKmjw_BvsDbpB5nJvK8K8SVAz4TMUM
SENDER_EMAIL=onboarding@resend.dev

# PayPal - BLOCKED (user account issues)
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_MODE=sandbox
PAYPAL_BUSINESS_EMAIL=JJspilot24@gmail.com
FRONTEND_URL=https://infojethub.preview.emergentagent.com
```

---

## 5. Test Results

**Latest Test: iteration_12.json**
- Backend: **13/13 subscription tests passed (100%)**
- Frontend: **All subscription pages and flows working**
- Stripe: **LIVE** - Checkout sessions working in Sandbox mode
- Email: **LIVE** - Welcome emails sent successfully

---

## 6. Credentials

```
Test User: testuser_new@example.com / password123
Admin: admin@infopilot.com / admin123
Stripe Test Card: 4242 4242 4242 4242 (any future date, any CVC)
```

---

## 7. Code Architecture

```
/app
├── backend/
│   ├── models/schemas.py
│   ├── routes/
│   │   ├── stripe.py       # Stripe payments + subscription management
│   │   ├── email.py        # Resend integration
│   │   ├── paypal.py       # PayPal (blocked)
│   │   └── ...
│   ├── .env
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── SubscriptionDashboard.js  # NEW
│   │   │   ├── PaymentPages.js           # Stripe pages
│   │   │   ├── MarketplacePage.js
│   │   │   └── ...
│   │   ├── components/
│   │   │   ├── Navbar.js                 # Updated with Subscription link
│   │   │   └── ...
│   │   └── App.js                        # Updated routes
│   └── package.json
├── tests/
│   └── test_subscription_management.py   # NEW
└── memory/PRD.md
```

---

## 8. Blocked Issues

### PayPal Account (P0)
- User cannot access PayPal Developer Dashboard ("Unauthorized")
- Payment links failing
- **Action Required:** User must contact PayPal Business Support
- Once resolved, provide `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET`

---

## 9. Next Steps

- [x] Stripe Subscription Management Dashboard
- [ ] PayPal account resolution (blocked on user)
- [ ] WebSocket real-time chat upgrade
- [ ] Additional search engines (Brave, Bing)
- [ ] Mobile app versions
- [ ] Process oversized document (user to break down file)

---

*Last Updated: January 18, 2026*  
*Version: 3.4 - Stripe Subscription Management Complete*  
*Test Status: 100% Pass Rate (iteration_12.json)*
