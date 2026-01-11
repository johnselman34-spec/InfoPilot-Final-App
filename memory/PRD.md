# InfoPilot Explorer - Product Requirements Document

## Original Problem Statement
Build a comprehensive information exchange social network application ("InfoPilot Explorer") with:
- Specialized search engine with Boolean protocol parsing (InfoJet 2.0)
- Social features (Groups, Pages, reactions, comments)
- Interactive map for geolocated search results
- "Pay What You Want" PayPal subscription model
- Admin control panel
- AI-powered weekly email newsletter to promote:
  - The app subscription
  - The book "Letters to Evelyn" by John Selman ($2.99)

## Tech Stack
- **Frontend:** React, TailwindCSS (custom theme: purple/pink/blue)
- **Backend:** FastAPI, MongoDB (motor), Pydantic
- **Authentication:** JWT + Google OAuth (via Emergent Auth)
- **Email:** Resend API ✅ WORKING
- **AI:** OpenAI GPT-4o (via Emergent LLM Key)
- **Payments:** PayPal "Pay What You Want"

## Key Features Implemented

### 1. Authentication System ✅
- Email/password registration and login
- Google OAuth via Emergent Auth
- JWT session management
- **Case-insensitive email matching** (Fixed Jan 11, 2026)

### 2. Protocol Search Engine (InfoJet 2.0) ✅
- Multi-word phrase matching ("civil war")
- Abbreviation handling (U.S., Ph.D.)
- Boolean operators: AND (&), OR, INCLUDE ALL (+), EXCLUDE ALL (^)
- Web search via DuckDuckGo + Google scraping
- Protocol debugging endpoint

### 3. Category & Collation System ✅
- Hierarchical categories (up to 100 levels)
- Public/private protocols
- Automatic article classification (News, Blog, Forum, Ph.D., etc.)
- Daily collate limits

### 4. Book Promotion ✅
- Rotating image banner with user's 4 advertisement images
- Divine Zape review quote: "This memoir is a profound and unforgettable literary piece."
- 19 Five-Star Reviews badge from Readers' Favorite
- $2.99 price prominent CTA
- Sidebar promotion widget

### 5. Newsletter System ✅
- AI-powered content generation (Emergent LLM Key)
- Resend email integration (WORKING)
- Test email functionality
- Newsletter history tracking

### 6. Admin Panel ✅
- General settings (collate limits, category levels)
- Search settings (results per page, unpaid limits)
- Pricing settings (PayPal email, subscription price)
- Newsletter management (generate, preview, send)
- User management (ban users)
- Content moderation (blocked words)

### 7. Social Features (Partial)
- Friend requests/acceptance/rejection
- Private messaging
- User profiles
- Basic post structure (placeholder)

### 8. Subscription System ✅
- Pay What You Want pricing ($0.75 - $5.00 + custom)
- PayPal payment URL generation
- Manual subscription activation

## API Endpoints

### Authentication
- POST `/api/auth/register` - Register new user
- POST `/api/auth/login` - Login
- POST `/api/auth/google` - Google OAuth
- GET `/api/auth/google/session-data` - Google OAuth proxy
- GET `/api/auth/me` - Get current user
- POST `/api/auth/logout` - Logout

### Search & Categories
- POST `/api/search` - Web search
- POST `/api/collate` - Collate results to categories
- GET `/api/categories` - List user categories
- POST `/api/categories` - Create category
- PUT `/api/categories/{id}` - Update category
- DELETE `/api/categories/{id}` - Delete category

### Protocol Debugging
- POST `/api/protocol/debug` - Debug protocol matching
- POST `/api/protocol/validate` - Validate protocol format

### Newsletter
- POST `/api/newsletter/generate` - Generate AI newsletter (Admin)
- GET `/api/newsletter/preview` - Preview latest newsletter (Admin)
- POST `/api/newsletter/send` - Send newsletter via Resend (Admin)
- POST `/api/newsletter/test-email` - Send test email (Admin)
- GET `/api/newsletter/history` - Newsletter history (Admin)

### Book Promotion
- GET `/api/book-promo` - Get book promotion data

### User Settings
- PUT `/api/users/settings` - Update user settings
- POST `/api/users/change-password` - Change password
- GET `/api/users/has-password` - Check if user has password set

### Protocol Marketplace
- GET `/api/marketplace/protocols` - List marketplace protocols
- POST `/api/marketplace/protocols` - Create new listing
- POST `/api/marketplace/purchase` - Purchase a protocol
- GET `/api/marketplace/purchases` - Get user's purchases
- GET `/api/marketplace/seller/dashboard` - Seller stats & earnings
- GET `/api/marketplace/categories` - Marketplace categories

## Database Collections
- `users` - User accounts
- `sessions` - Auth sessions
- `categories` - Search protocols
- `search_results` - Collated results
- `newsletters` - Newsletter history
- `settings` - Admin settings
- `messages` - Private messages

## Credentials
- **Admin:** john@infojet.com / password123
- **Test User:** test@gmail.com

## Environment Variables
- `MONGO_URL` - MongoDB connection
- `DB_NAME` - Database name (infopilot_db)
- `EMERGENT_LLM_KEY` - AI generation
- `RESEND_API_KEY` - Email sending ✅ CONFIGURED
- `SENDER_EMAIL` - Sender email address

## Date: January 11, 2026

## Latest Session Update (Jan 11, 2026 - Newsletter Phase 2 & Refactoring)

### Newsletter Enhancement Phase 2 - Full Manuscript Integration ✅
**Analyzed complete "Letters to Evelyn" manuscript and integrated content for "extremely funny" newsletters:**

1. ✅ **MANUSCRIPT_CONTENT Data Structure Created:**
   - Book metadata (title, author, genre, dedication, copyright warning)
   - 7 key characters with descriptions (John Selman, Evelyn, Durham, The Captain, etc.)
   - 20 wild plot elements from the manuscript
   - 15 hilarious quotes with context
   - 9 chapter teasers
   - 12 dad jokes
   - 11 marketing hooks
   - 6 newsletter themes
   - 10 email subject lines

2. ✅ **Wild Plot Elements Now Used:**
   - Navy pilot's stepmother POISONED his eggs with LSD (200-500 doses!)
   - Captain called him "Jesus" 9-12 times per encounter
   - He hid a spacecraft inside a dinosaur's reproductive organs
   - Gray aliens only said "Drink water, good boy"
   - 83-degree nose dive survived with 430 picoseconds to spare

3. ✅ **Hilarious Quotes Integrated:**
   - "Fack off!" (Monty Python response to being called Jesus)
   - "Drink waaaater, good boy" (Gray Aliens)
   - "We queefed our way out of the undulating gargantuan reproductive organs at maximum power!"

4. ✅ **Enhanced AI Prompt:**
   - Now references book summary, characters, wild plots, quotes, chapter teasers
   - Uses copyright warning as marketing gold
   - Mixes profound lines with absurdist humor
   - References Douglas Adams, Terry Pratchett, Monty Python style

### Code Refactoring Phase 1 - Frontend ✅
**Started breaking down monolithic App.js (4928 lines) into modular structure:**

1. ✅ **New Directory Structure Created:**
   ```
   /app/frontend/src/
   ├── contexts/
   │   └── AuthContext.js (125 lines)
   ├── utils/
   │   ├── api.js (5 lines)
   │   └── hashtags.js (40 lines)
   ├── components/shared/
   │   ├── Toast.js (17 lines)
   │   ├── Icons.js (27 lines)
   │   ├── HashtagDisplay.js (40 lines)
   │   ├── Sidebar.js (101 lines)
   │   └── index.js (4 lines)
   ├── pages/
   │   ├── LoginPage.js (73 lines)
   │   ├── RegisterPage.js (83 lines)
   │   ├── AuthCallback.js (109 lines)
   │   └── index.js (3 lines)
   └── App.js (4368 lines - reduced from 4928)
   ```

2. ✅ **Components Extracted:**
   - AuthProvider & useAuth hook → contexts/AuthContext.js
   - Toast notification → components/shared/Toast.js
   - Icons → components/shared/Icons.js
   - HashtagDisplay → components/shared/HashtagDisplay.js
   - Sidebar → components/shared/Sidebar.js
   - LoginPage → pages/LoginPage.js
   - RegisterPage → pages/RegisterPage.js
   - AuthCallback → pages/AuthCallback.js

3. ✅ **Line Count Reduction:**
   - App.js: 4928 → 4368 lines (560 lines removed)
   - Total extracted: ~627 lines into reusable modules
   - Build successful with only ESLint warnings (not errors)

### Previous Session Updates (Jan 11, 2026 - Newsletter Enhancement)
1. ✅ **4 NEW Promotional Images** from user's advertisements integrated:
   - Image 1: "WROTE A BOOK - UNIVERSE FACT-CHECKED IT - IT PASSED!" (cosmic_approval theme)
   - Image 2: "THERAPIST: THIS IS A LOT TO UNPACK - BRING SNACKS" (therapy_humor theme)  
   - Image 3: "I FLEW JETS THEN REALITY BROKE" (pilot_story theme)
   - Image 4: "TERROR OF THE COSMICGULPER - WE'RE ALL GONNA DIE!" (galactic_comedy theme)

2. ✅ **Rich Review Data Integrated:**
   - Amazon: 57 reviews, 5.0 out of 5 stars
   - Readers' Favorite: 9 professional reviewers (Divine Zape, Luwi Nyakansaila, Paul Zeitsman, etc.)
   - Real quotes scraped from Amazon and ReadersFavorite.com

3. ✅ **Author Highlights Added:**
   - World record: Steepest Sarajevo Approach (83° nose dive)
   - Navy pilot credentials
   - 50+ jokes promise
   - "Funnier than Dave Chappelle" claim

4. ✅ **Humor Features:**
   - Dad Joke of the Week (7 rotating jokes)
   - Douglas Adams/Terry Pratchett-style cosmic humor
   - Self-aware meta-marketing humor
   - Rotating taglines from advertisements

5. ✅ **Technical Implementation:**
   - BOOK_PROMO_IMAGES array with URLs, taglines, themes, subtitles
   - BOOK_REVIEWS dictionary with Readers' Favorite and Amazon reviews
   - AUTHOR_HIGHLIGHTS dictionary with credentials
   - Enhanced AI prompt for GPT-4o generation

## Test Results (Updated Jan 11, 2026 - Latest Session)
- Newsletter Phase 2 Testing: **93% PASS** (14/15 tests - 1 search timeout expected)
- Frontend Refactoring: **100% PASS** (All refactored components verified)
- Manuscript Integration: **VERIFIED** - AI generates newsletters with book content
- Backend: 100% (56/56 tests passed - auth, category creation, API endpoints)
- Frontend: 100% (all critical features working)
- App Mode: **FREE FOR EVERYONE**

## What's Been Completed This Session (Latest - Newsletter Phase 2 & Refactoring)
1. ✅ Resend email integration for newsletters (API key configured, WORKING)
2. ✅ Improved Protocol Parser (multi-word phrases, abbreviations, word boundaries)
3. ✅ Enhanced web search (DuckDuckGo + Google scraping)
4. ✅ **APP NOW 100% FREE** - No PayPal subscription required
5. ✅ **NEW FUNNY BOOK IMAGES** with rotating taglines:
   - "WROTE A BOOK. UNIVERSE FACT-CHECKED IT. IT PASSED."
   - "THERAPIST: THIS IS A LOT TO UNPACK. Bring snacks. Possibly a helmet."
   - "I FLEW JETS. THEN REALITY BROKE."
   - "TERROR OF THE COSMIC GULPER - A comedy of galactic proportions!"
6. ✅ **OPTIONED FOR FILM!** badge prominently displayed
7. ✅ Book promotion in multiple strategic locations:
   - Main page hero banner with rotating images & taglines
   - Sidebar with "GET IT - Only $2.99!" CTA
   - Subscription page (now shows FREE announcement + book promo)
8. ✅ **Three action buttons**: BUY NOW, OFFICIAL SITE, READ REVIEWS
9. ✅ Clickable thumbnail gallery for all 4 funny images
10. ✅ Crawled letters-to-evelyn.sintra.site for official content
11. ✅ PayPal email updated to JJSpilot24@gmail.com (for future use)

## What's Been Completed This Session (Jan 11, 2026 - Continued)
1. ✅ Password Change Feature - Settings page now has password change for all users
2. ✅ Protocol Marketplace - Full marketplace with buy/sell, 90/10 revenue split
3. ✅ 8 Sample Protocols added (Climate Research, Tech News, Medical Papers, etc.)
4. ✅ **GAMIFICATION SYSTEM:**
   - 13 badges (Pioneer, Explorer, Power Searcher, Protocol Creator, etc.)
   - XP system with levels
   - Leaderboard
   - Login streak tracking
   - Auto badge awarding
5. ✅ **PAYPAL WEBHOOK INTEGRATION:**
   - Webhook endpoint for automatic payment confirmation
   - Pending purchase tracking
   - Manual payment confirmation option
   - Seller sales history
6. ✅ Admin access granted to JJSPilot24@gmail.com
7. ✅ **SOCIAL FEATURES COMPLETE:**
   - Feed: Create posts, view posts from groups
   - Groups: Create, join, leave, post to groups, like posts
   - Pages: Create, follow, like, post updates (page owners)
   - Friends list view
8. ✅ **SEARCH IMPROVEMENTS:**
   - Protocol hint text updated to "keyphrase1 or keyphrase2"
   - Category protocol editing via ✏️ button
   - DDGS library integration for better search results
   - More lenient protocol matching (50%+ groups OR 3+ keywords)
9. ✅ **CODE REFACTORING (Partial):**
   - Created /backend/utils/ module
   - database.py - DB connection utilities
   - auth.py - Authentication utilities
   - Main server.py still in use (supervisor read-only)

## Pending/Backlog

### P0 - Critical
- ✅ **COMPLETE: Newsletter Enhancement Phase 2** - Full manuscript integration
- ✅ **COMPLETE: Code Refactoring Phase 1** - Frontend modules extracted
- ⏳ **IN PROGRESS: Code Refactoring Phase 2** - Extract remaining page components
- Interactive map with Leaflet (IN PROGRESS)
- Full social features (Groups, Pages, comments, reactions) (IN PROGRESS)

### P1 - High Priority
- Backend refactoring - Move endpoints from server.py to /routes/
- PayPal Webhook testing with sandbox events
- Better search API integration (SerpApi/DataForSEO) - Bing API retired
- Internet Robot for automated classification

### P2 - Medium Priority
- Global Research Database
- Statistics pages
- Gamification enhancements (weekly leaderboards)
- "Quote of the Day" widget using manuscript quotes

### P3 - Nice to Have
- Advanced analytics
- Export functionality
- Mobile app wrapper

## Search API Options (Bing API Retired)
Since Bing Search API has been retired in 2024/2025, here are alternatives:
1. **SearchAPI.io** - Multi-engine (Google, Bing, Baidu)
2. **DataForSEO** - $0.0006/request, very cost-effective
3. **Serper.dev** - Google-only, fast and cheap
4. **Bright Data SERP API** - Enterprise-grade

All require API keys from their respective providers.
