# InfoPilot Explorer - Product Requirements Document

**App Name:** InfoPilot Explorer
**Company:** Top Pilot Enterprises, Inc.
**Tagline:** "First in Flight with Monetization of Searches! It's a Bear! 🐻"
**Author/Owner:** John Selman (JJSpilot24@gmail.com, 207-522-0894)
**Location:** Brunswick, Maine

---

## 1. Core Product Vision

InfoPilot Explorer is a Worldwide Information Exchange Database providing users a "3D view of the internet" through custom Boolean search protocols (InfoJet 2.0). Users categorize web content, visualize on maps, and sell protocols in a marketplace.

---

## 2. Implemented Features (January 18, 2026)

### ✅ Core Platform
- [x] User authentication (register/login/logout)
- [x] JWT-based session management with MongoDB
- [x] InfoJet 2.0 Protocol Parser (`&`, `or`, `+`, `^` operators)
- [x] Category/Subcategory hierarchy (unlimited depth)
- [x] **Real DuckDuckGo Search Integration** - Returns 20+ real results

### ✅ Search & Collate
- [x] Real DuckDuckGo Search - Uses `ddgs` package
- [x] Automatic categorization based on protocols
- [x] Document type classification
- [x] Location extraction from content
- [x] Quick Search within results
- [x] Search Aggregation modes
- [x] **Select All / Deselect All** buttons for category selection

### ✅ Email Integration (Resend) - NEW!
- [x] Newsletter subscription endpoint `/api/email/subscribe`
- [x] Unsubscribe functionality `/api/email/unsubscribe`
- [x] Admin newsletter sending `/api/email/send-newsletter`
- [x] Welcome email on subscription
- [x] HTML branded email templates
- [x] **Status:** Mocked without API key, fully functional when RESEND_API_KEY is configured

### ✅ PayPal Integration - NEW!
- [x] PayPal Orders v2 REST API integration
- [x] Create order endpoint `/api/paypal/create-order`
- [x] Capture order endpoint `/api/paypal/capture-order`
- [x] Simple payment links fallback (works without API credentials)
- [x] Webhook endpoint for payment notifications
- [x] Purchase history `/api/paypal/purchases`
- [x] Sales history `/api/paypal/sales`
- [x] Marketplace success/cancel pages
- [x] **85% seller commission, 15% platform fee**
- [x] **Status:** Simple payments work now. Full API available when PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET are configured

### ✅ Personal Reports with Image Upload
- [x] Create personal reports with title, content
- [x] Image upload (up to 3 images per report, max 5MB each)
- [x] **Select All / Deselect All** for category tagging - NEW!
- [x] Word count display

### ✅ Groups & Social Features
- [x] Create Groups (public/private)
- [x] Join/Leave groups
- [x] View member counts

### ✅ Pages & Social Features
- [x] Create Pages with categories
- [x] Follow pages
- [x] View follower counts

### ✅ Revenue Dashboard
- [x] Total earnings display (85% commission)
- [x] Total sales count
- [x] Top selling protocols leaderboard
- [x] **PDF Export** with InfoPilot branding
- [x] **CSV Export** for spreadsheets

### ✅ Theme Gallery (12 Themes)
- [x] 10 Dark Themes + 2 Light Themes
- [x] Dark/Light mode toggle
- [x] Theme preview

### ✅ Marketplace
- [x] List protocols for sale
- [x] **PayPal Checkout integration** - NEW!
- [x] Category filters
- [x] Protocol preview and copy
- [x] Success/Cancel payment pages - NEW!

### ✅ Other Features
- [x] Chat System (rooms, messages)
- [x] Protocol Templates (8 official + community)
- [x] Easter Eggs & Laughter Points
- [x] Interactive Map (Leaflet)
- [x] Statistics & Leaderboard
- [x] Book & Food Sections
- [x] Legal Pages

---

## 3. Code Architecture

### Backend Structure
```
/app/backend/
├── models/
│   └── schemas.py
├── routes/
│   ├── auth.py
│   ├── categories.py
│   ├── chat.py
│   ├── email.py          # NEW - Resend integration
│   ├── groups.py
│   ├── marketplace.py
│   ├── misc.py
│   ├── pages.py
│   ├── paypal.py         # NEW - PayPal Orders v2 API
│   ├── reports.py
│   ├── revenue.py
│   ├── search.py
│   ├── templates.py
│   └── users.py
├── utils/
│   ├── auth.py
│   ├── db.py
│   └── search.py
├── server.py
└── requirements.txt
```

### Frontend Structure
```
/app/frontend/src/
├── components/
│   ├── ui/
│   ├── Navbar.js
│   ├── FloatingEasterEgg.js
│   └── StarsBackground.js
├── context/
│   ├── AuthContext.js
│   ├── ThemeContext.js
│   └── ToastContext.js
├── pages/
│   ├── ... (all existing pages)
│   └── MarketplaceResultPages.js  # NEW - Success/Cancel pages
├── App.js
└── App.css
```

---

## 4. New API Endpoints

### Email (Resend)
- `POST /api/email/subscribe` - Subscribe to newsletter
- `DELETE /api/email/unsubscribe` - Unsubscribe
- `GET /api/email/subscribers` - Get subscribers (admin)
- `POST /api/email/send-newsletter` - Send newsletter (admin)
- `GET /api/email/test` - Check email config status

### PayPal
- `GET /api/paypal/config` - Check PayPal config status
- `POST /api/paypal/create-order` - Create PayPal order
- `POST /api/paypal/capture-order` - Capture payment
- `GET /api/paypal/order/{id}` - Get order details
- `POST /api/paypal/webhook` - PayPal webhook handler
- `GET /api/paypal/purchases` - User's purchase history
- `GET /api/paypal/sales` - User's sales history

---

## 5. Environment Variables

### Backend `.env`
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"

# Resend Email (get from https://resend.com)
RESEND_API_KEY=          # Add your key
SENDER_EMAIL=onboarding@resend.dev

# PayPal (get from https://developer.paypal.com)
PAYPAL_CLIENT_ID=        # Add your client ID
PAYPAL_CLIENT_SECRET=    # Add your secret
PAYPAL_MODE=sandbox
PAYPAL_BUSINESS_EMAIL=JJspilot24@gmail.com

FRONTEND_URL=https://pilotdata.preview.emergentagent.com
```

---

## 6. PayPal Configuration

- **Business Email:** JJspilot24@gmail.com
- **Subscription:** https://www.paypal.com/ncp/payment/LZDBN3SQU4NWQ ($1/mo, $9.98/yr)
- **Book Purchase (PayPal):** https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU
- **Book Purchase (Amazon):** https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J

---

## 7. Integration Status

| Integration | Status | Notes |
|-------------|--------|-------|
| DuckDuckGo Search | ✅ LIVE | Real web results |
| Resend Email | ⚠️ READY | Needs RESEND_API_KEY |
| PayPal Simple | ✅ LIVE | Works with direct links |
| PayPal Orders API | ⚠️ READY | Needs CLIENT_ID + SECRET |

---

## 8. Upcoming Tasks (P1)

- [x] ~~Resend email integration~~ ✅ DONE
- [x] ~~PayPal Orders v2 API~~ ✅ DONE
- [ ] Configure Resend API key for live emails
- [ ] Configure PayPal API credentials for full checkout

---

## 9. Future/Backlog (P2)

- [ ] WebSocket real-time chat
- [ ] App Store listings
- [ ] Additional search engines (Brave, Bing)
- [ ] Mobile app versions
- [ ] Process oversized document

---

## 10. Test Credentials

```
Test User: testuser_new@example.com / password123
Admin: admin@infopilot.com / admin123
```

---

*Last Updated: January 18, 2026*
*Version: 3.2 - Resend Email + PayPal Integration*
