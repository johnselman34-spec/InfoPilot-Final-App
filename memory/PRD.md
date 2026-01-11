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

## Test Results
- Backend: 95.5% (21/22 tests passed)
- Frontend: 100% (all critical features working)

## What's Been Completed This Session
1. ✅ Resend email integration for newsletters (API key configured, WORKING)
2. ✅ Improved Protocol Parser (multi-word phrases, abbreviations, word boundaries)
3. ✅ Enhanced web search (DuckDuckGo + Google scraping)
4. ✅ Book promotion banner with rotating images (4 user-provided images)
5. ✅ Newsletter test email endpoint
6. ✅ Protocol debugging endpoint
7. ✅ **AUTOMATED WEEKLY NEWSLETTER SCHEDULE** - Admin can set day/time
8. ✅ Enhanced AI newsletter generation with actual book reviews:
   - Divine Zape quote: "This memoir is a profound and unforgettable literary piece."
   - 19 Five-Star Reviews from Readers' Favorite
   - Book plot details (Navy pilot, LSD poisoning, aliens, love story)
   - Rotating book advertisement images in emails
9. ✅ Crawled Amazon and Readers' Favorite pages for rich content
10. ✅ Admin Panel Newsletter tab with full scheduling UI

## Pending/Backlog

### P0 - Critical
- Interactive map with Leaflet (premium feature)
- Full social features (Groups, Pages, comments, reactions)
- Protocol Marketplace (users sell protocols)

### P1 - High Priority
- Better search API integration (SerpApi/DataForSEO) - Bing API retired
- Internet Robot for automated classification
- Access Google Doc manuscript content for newsletter (requires public sharing or content copy)

### P2 - Medium Priority
- Global Research Database
- Statistics pages
- Gamification (achievements, badges)
- Code refactoring (split monolithic files)

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
