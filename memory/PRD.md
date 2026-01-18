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
| **DuckDuckGo Search** | ✅ **LIVE** | Real web search results (unlimited, no API key) |
| **Brave Search** | ⚠️ **READY** | Integrated, needs BRAVE_SEARCH_API_KEY (free: 2000/month) |
| **Bing Search** | ❌ **RETIRED** | Microsoft retired Bing Search API in Aug 2025 |
| **PayPal** | ⚠️ **BLOCKED** | User account issues - needs resolution |

---

## 2. All Implemented Features

### ✅ Core Platform
- User authentication (register/login/logout)
- JWT-based session management with MongoDB
- InfoJet 2.0 Protocol Parser (supports "and" as "&" synonym)
- Category/Subcategory hierarchy
- Select All / Deselect All buttons

### ✅ Multi-Engine Search Integration
- **DuckDuckGo** - Privacy-focused search (no API key required)
- **Brave Search** - Independent index with 30B+ pages (free tier: 2000/month)
- Search engine selector dropdown on Ultimate Search page
- Available engines status badges (configured/not configured)
- Source badges on search results (🦆 DuckDuckGo, 🦁 Brave)
- Engine parameter: "all", "duckduckgo", or "brave"

### ✅ Stripe Integration (Primary Payment) - LIVE
- Stripe Checkout for subscriptions and marketplace purchases
- **Subscription Management Dashboard** (`/subscription`)
  - View current subscription status
  - Cancel/reactivate subscription
  - Billing history with past transactions
  - Wallet balance from marketplace sales
  - Change plan (monthly/yearly)
- Monthly: $1.00/mo, Yearly: $9.98/yr (Save 17%)
- 85% seller / 15% platform fee structure

### ✅ Email Integration (Resend) - LIVE
- Newsletter subscription with welcome email
- Unsubscribe functionality
- Admin newsletter sending

### ✅ All Pages Working
- HomePage, LoginPage
- UltimateSearchPage (with multi-engine search + Select All/Deselect All)
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
- SubscriptionDashboard (NEW)
- SubscriptionCheckout

---

## 3. API Endpoints

### Search (`/api/search`)
- `GET /engines` - Get available search engines and status (NEW)
- `POST /collate` - Search and collate with engine parameter (UPDATED)
- `GET /results` - Get search results with filtering

### Stripe (`/api/stripe`)
- `GET /config` - Check Stripe configuration
- `POST /create-checkout` - Create checkout session
- `GET /subscription` - Get subscription details
- `GET /billing-history` - Get billing history
- `POST /cancel-subscription` - Cancel subscription
- `POST /reactivate-subscription` - Reactivate cancelled subscription

### Email (`/api/email`)
- `POST /subscribe` - Subscribe to newsletter
- `DELETE /unsubscribe` - Unsubscribe

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

# Brave Search (Optional - get free key at api-dashboard.search.brave.com)
BRAVE_SEARCH_API_KEY=

# PayPal - BLOCKED (user account issues)
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
```

---

## 5. Test Results

**Latest Test: iteration_13.json**
- Backend: **16/16 search engine tests passed (100%)**
- Frontend: **All search engine features working**
- Multi-engine search: DuckDuckGo ✅ LIVE, Brave ⚠️ needs API key

---

## 6. Credentials

```
Test User: testuser_new@example.com / password123
Admin: admin@infopilot.com / admin123
Stripe Test Card: 4242 4242 4242 4242 (any future date, any CVC)
```

---

## 7. Requirements from Documents (7, 8, 9)

### Completed Features:
- ✅ Multi-engine search (DuckDuckGo, Brave)
- ✅ Subscription management dashboard
- ✅ Protocol "and" → "&" synonym support
- ✅ Select All / Deselect All buttons
- ✅ Email newsletter integration

### Pending Features (from documents):
- User polls on pages/groups
- Voice search integration
- Browser extension
- Identity masking in Groups/Pages/Chat
- Quote gallery (50 quotes from manuscript)
- Maestro Bistro advertisements
- Mobile app wrapper

---

## 8. Setup Instructions for Brave Search

To enable Brave Search:
1. Go to https://api-dashboard.search.brave.com
2. Create a free account
3. Get your API key (free tier: 2000 queries/month)
4. Add to `/app/backend/.env`:
   ```
   BRAVE_SEARCH_API_KEY=your_api_key_here
   ```
5. Restart backend: `sudo supervisorctl restart backend`

---

## 9. Next Steps

- [x] Stripe Subscription Management Dashboard
- [x] Brave Search Integration
- [x] Multi-engine search selector
- [ ] PayPal account resolution (blocked on user)
- [ ] WebSocket real-time chat upgrade
- [ ] Mobile app versions
- [ ] Voice search integration

---

*Last Updated: January 18, 2026*  
*Version: 3.5 - Multi-Engine Search Complete*  
*Test Status: 100% Pass Rate (iteration_13.json)*
