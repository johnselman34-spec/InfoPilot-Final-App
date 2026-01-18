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
- [x] **Real DuckDuckGo Search Integration** ✨ NOW LIVE - Returns 20+ real results

### ✅ Search & Collate
- [x] **Real DuckDuckGo Search** - Uses `ddgs` package v9.10.0
- [x] Automatic categorization based on protocols
- [x] Document type classification (PhD, News, Blog, Forum, etc.)
- [x] Location extraction from content
- [x] Quick Search within results
- [x] Search Aggregation modes (And/Or, And, Or)

### ✅ Personal Reports with Image Upload
- [x] Create personal reports with title, content
- [x] **Image upload** (up to 3 images per report, max 5MB each)
- [x] Supported formats: JPEG, PNG, GIF, WebP
- [x] Category tagging for reports
- [x] Word count display
- [x] Image preview and removal

### ✅ Groups & Social Features
- [x] **Create Groups** (public/private)
- [x] Join groups
- [x] Leave groups
- [x] View member counts
- [x] My Groups / Discover Groups sections
- [x] Group cards with gradient avatars

### ✅ Pages & Social Features
- [x] **Create Pages** with categories (Tech, News, Education, etc.)
- [x] Follow pages
- [x] View follower counts
- [x] My Pages / Following / Discover sections
- [x] Category-based color coding

### ✅ Revenue Dashboard with PDF Export
- [x] Total earnings display (85% commission)
- [x] Total sales count
- [x] Pending payout balance
- [x] Top selling protocols leaderboard
- [x] Monthly revenue chart
- [x] **PDF Export** with InfoPilot branding
- [x] **CSV Export** for spreadsheets

### ✅ Theme Gallery (12 Themes)
- [x] **Dark Themes (10):** Cosmic Gold, Royal Purple, Hot Red, Ocean Blue, Forest Green, Sunset Pink, Ruby Red, Midnight, Pure Gold, Cyberpunk
- [x] **Light Themes (2):** Light Mode, Cream
- [x] Dark/Light mode toggle
- [x] Theme preview with component samples

### ✅ Marketplace
- [x] List protocols for sale
- [x] Buy protocols via PayPal
- [x] **Category filters** (History, Tech, Science, Business, Health, Sports, Education, Entertainment)
- [x] **PayPal Connect** modal (85% commission info)
- [x] Protocol preview and copy

### ✅ Chat System
- [x] Create chat rooms (public/private)
- [x] Send messages
- [x] View message history
- [x] Room member tracking

### ✅ Protocol Templates
- [x] 8 official templates
- [x] Create custom templates
- [x] Community templates gallery
- [x] Recommended protocols section

### ✅ Easter Eggs & Laughter Points
- [x] Floating Easter Eggs
- [x] 8 unique jokes
- [x] Catch eggs for points
- [x] Points displayed in navbar

### ✅ Interactive Map
- [x] Leaflet integration
- [x] Color-coded dots by category
- [x] Improved popups
- [x] Personal/Worldwide toggle

### ✅ Statistics & Leaderboard
- [x] Platform statistics (users, categories, results, reports)
- [x] Top Laughter Points leaderboard
- [x] Top Protocol Creators leaderboard

### ✅ Book & Food Sections
- [x] Letters to Evelyn - Full book info, reviews, purchase links
- [x] Maestro Bistro - Menu items with prices and taglines

### ✅ Legal Pages
- [x] User Agreement
- [x] Privacy Policy

---

## 3. Code Architecture (REFACTORED January 18, 2026)

### Backend Structure
```
/app/backend/
├── models/
│   ├── __init__.py
│   └── schemas.py          # Pydantic models
├── routes/
│   ├── __init__.py
│   ├── auth.py             # Authentication
│   ├── categories.py       # Category management
│   ├── chat.py             # Chat rooms
│   ├── groups.py           # Groups social feature
│   ├── marketplace.py      # Protocol marketplace
│   ├── misc.py             # Easter eggs, stats, legal, MAP DATA, LEADERBOARD
│   ├── pages.py            # Pages social feature
│   ├── reports.py          # Personal reports with images
│   ├── revenue.py          # Revenue dashboard
│   ├── search.py           # DuckDuckGo search
│   ├── templates.py        # Protocol templates
│   └── users.py            # User management
├── utils/
│   ├── __init__.py
│   ├── auth.py             # Auth utilities
│   ├── db.py               # Database connection
│   └── search.py           # Search utilities
├── server.py               # Main FastAPI app
└── requirements.txt
```

### Frontend Structure
```
/app/frontend/src/
├── components/
│   ├── ui/                 # Shadcn UI components
│   ├── Navbar.js
│   ├── FloatingEasterEgg.js
│   └── StarsBackground.js
├── context/
│   ├── AuthContext.js
│   ├── ThemeContext.js
│   └── ToastContext.js
├── pages/
│   ├── BookPage.js
│   ├── ChatPage.js
│   ├── FoodPage.js
│   ├── GroupsPage.js
│   ├── HomePage.js
│   ├── InfoPilotPage.js
│   ├── LoginPage.js
│   ├── MapPage.js          # RESTORED with full functionality
│   ├── MarketplacePage.js  # RESTORED with full functionality
│   ├── PagesPage.js
│   ├── ReportsPage.js      # RESTORED with full functionality
│   ├── RevenuePage.js      # RESTORED with full functionality
│   ├── StatsPage.js        # RESTORED with full functionality
│   ├── TemplatesPage.js    # RESTORED with full functionality
│   ├── ThemesPage.js       # RESTORED with full functionality
│   └── UltimateSearchPage.js
├── utils/
│   └── api.js
├── App.js                  # Main router with lazy loading
└── App.css
```

---

## 4. API Endpoints

### Auth
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Search
- `POST /api/search/collate` - Real DuckDuckGo search
- `GET /api/search/results` - Get filtered results

### Groups
- `POST /api/groups` - Create group
- `GET /api/groups` - List groups
- `POST /api/groups/{id}/join` - Join group
- `POST /api/groups/{id}/leave` - Leave group

### Pages
- `POST /api/pages` - Create page
- `GET /api/pages` - List pages
- `POST /api/pages/{id}/follow` - Follow page

### Reports & Images
- `POST /api/reports` - Create report
- `GET /api/reports` - Get reports
- `DELETE /api/reports/{id}` - Delete report
- `POST /api/reports/upload/image` - Upload image
- `GET /api/uploads/{filename}` - Get image

### Revenue
- `GET /api/revenue/dashboard` - Stats
- `GET /api/revenue/export?format=pdf|csv` - Export

### Marketplace
- `GET /api/marketplace/protocols` - Get protocols
- `POST /api/marketplace/buy/{id}` - Buy protocol

### Templates
- `GET /api/templates` - Get templates
- `POST /api/templates` - Create template

### Map & Stats
- `GET /api/map/data` - Get map data with location points
- `GET /api/stats` - Platform statistics
- `GET /api/leaderboard` - Laughter points & protocol creators leaderboard

---

## 5. PayPal Configuration

- **Business Email:** JJspilot24@gmail.com
- **Subscription:** https://www.paypal.com/ncp/payment/LZDBN3SQU4NWQ
- **Book Purchase (PayPal):** https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU
- **Book Purchase (Amazon):** https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J

---

## 6. Known Limitations

| Feature | Status | Notes |
|---------|--------|-------|
| Newsletter | MOCKED | Logged but no SMTP - User wants Resend integration |
| PayPal Connect | Placeholder | Info modal only - User has PayPal business account |
| Real-time Chat | Not yet | Uses polling |

---

## 7. Upcoming Tasks (P1)

- [ ] Real PayPal Connect integration (User has account: JJspilot24@gmail.com)
- [ ] Resend email integration for newsletters

---

## 8. Future/Backlog (P2)

- [ ] WebSocket real-time chat
- [ ] App Store listings (Google Play, Apple, Samsung)
- [ ] Additional search engines (Brave, Bing - requires API keys)
- [ ] Mobile app versions
- [ ] Process oversized document (InfoPilot Explorer information 7.docx)

---

## 9. Test Credentials

```
Test User: testuser_new@example.com / password123
Admin: admin@infopilot.com / admin123
```

---

*Last Updated: January 18, 2026*
*Version: 3.1 - Post-Refactoring Fix Complete - All 7 Pages Restored*
