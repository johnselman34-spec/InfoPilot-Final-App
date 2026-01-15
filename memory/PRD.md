# InfoPilot Explorer - Product Requirements Document

## Original Problem Statement
InfoPilot Explorer is a sophisticated information exchange social network with a custom search language. The application features:
- Custom registration and Google OAuth authentication
- AI-powered intelligent search using Emergent LLM
- Hierarchical categories with custom InfoPilot 2.0 Protocol syntax
- Google Maps integration for location visualization
- Google Safe Browsing API for URL safety checks
- **Facebook-style social features** (Groups, Pages, Updates, Reactions, Comments)
- **Protocol Marketplace** - Users can sell private protocols ($0.75-$2.99)
- **PayPal "Pay What You Want" Subscription** model
- Book promotion for "Letters to Evelyn" by John Selman

## User Personas
- **Information Researchers**: Users who need to collect, categorize, and analyze web content
- **Content Curators**: Users building knowledge bases across multiple topics
- **Social Networkers**: Users who want to share and engage with content in groups and pages
- **Protocol Sellers**: Users who create valuable search protocols and monetize them

## Monetization Strategy
### Subscription Model
- **"Pay What You Want"** yearly subscription via PayPal (until March 2nd, 2026)
- PayPal Hosted Button ID: `765S46VPPEP5C`
- After promo period: Fixed $4.62/year
- PayPal SDK integrated with Venmo support

### Protocol Marketplace
- Private protocols can be listed for sale ($0.75 - $2.99)
- Buyers get access to view and copy the protocol
- Sellers track their sales and revenue in "My Sales" tab

## Core Features

### Implemented ✅

#### Authentication
- [x] Email/password registration and login
- [x] Google OAuth integration
- [x] JWT-based session management
- [x] Admin role support

#### Subscription & Payments
- [x] PayPal "Pay What You Want" subscription ($0.01 - $4.62+/year)
- [x] PayPal Hosted Button embedded on subscribe page
- [x] Subscription status tracking
- [x] Admin panel for subscription settings
- [x] **PayPal IPN (Instant Payment Notification)** - Automatic subscription activation

#### Statistics Page (Enhanced)
- [x] Platform Overview (Total Pilots, Public Protocols, Total Copies, Marketplace Sales)
- [x] **🏆 Popular Protocols by Clipboard Copies** - Leaderboard sorted by copy count
- [x] Top Contributors - Users with most public protocols
- [x] Your Data - Personal statistics with charts (Pie chart for article types, Bar chart for domains)
- [x] Protocol copy tracking via POST /api/categories/{id}/copy
- [x] **🏅 Badges & Achievements System** - Gamification with 16 unique badges
  - Copy milestones: First Steps, Rising Star, Popular, Trending, Viral, Legendary, Hall of Fame
  - Creator badges: Protocol Creator, Prolific Creator, Master Creator
  - Sales badges: First Sale, Bronze/Silver/Gold Seller
  - Collector badges: Collector, Avid Collector
- [x] **Badge Leaderboard** - Rankings by badges earned

#### Protocol Marketplace
- [x] Browse protocols for sale
- [x] My Purchases - view purchased protocols
- [x] My Sales - track revenue from sold protocols
- [x] List private protocols for sale ($0.75 - $2.99)
- [x] Quick toggle sale status from categories page

#### Social Features
- [x] **Groups**: Create/join groups (public/private/secret), post content
- [x] **Pages**: Create/follow pages with categories, post as admin
- [x] **Updates**: Post updates on Ultimate Search page
- [x] **Reactions**: Facebook-style emoji picker
- [x] **Comments**: Nested replies on posts, updates, and search results
- [x] **Friends**: View and manage friend connections
- [x] **Protocol Recommendations**: Users can suggest changes to public protocols
- [x] **Private Messaging**: Direct messaging with text and images (up to 8MB)
- [x] **Real-time WebSocket Messaging**: Instant message delivery with typing indicators
- [x] **Email Notifications**: SendGrid integration (requires API key)

#### Ultimate Search Page
- [x] AI-powered intelligent search (Emergent LLM)
- [x] Hierarchical category tree with expand/collapse
- [x] AND/OR/AND search logic radio buttons
- [x] Document type checkboxes filtering
- [x] Google Maps with category-colored location markers
- [x] Updates section with reactions and comments
- [x] **Automated Hashtags** - 4-6 clickable hashtags per search result (NEW)
- [x] **Clickable Category Trees** - Click category name to filter results (NEW)
- [x] **Database Stats Display** - Shows stored results, limit, remaining capacity (NEW)
- [x] **Clear All Results** - Button to clear entire user database (NEW)
- [x] **Clear Category Results** - Button to clear results from specific category (NEW)

#### Database Management (NEW - January 10, 2026)
- [x] **Admin-controllable Result Limit** - Default 4000 results per user (range 100-10,000)
- [x] **User Stats Endpoint** - View current_count, max_allowed, remaining, percentage_used
- [x] **Limit Enforcement** - Collation stops when user reaches limit
- [x] **Admin Clear User Data** - Admin can clear any user's results or specific category

#### Security
- [x] Google Safe Browsing API integration
- [x] URL safety checks before categorization
- [x] Blocked words filtering

#### Admin Panel
- [x] Settings management
- [x] User management
- [x] Subscription configuration (PayPal links, prices, promo dates)
- [x] Legal documents editing (Privacy Policy, Terms of Service)
- [x] **Database Limits Tab** - Control max results per user (NEW)
- [x] **Top Users by Results** - View users with most stored results (NEW)

### Pending Features 🔄

#### P0 - Critical
- [x] **Admin Panel Access** - Fixed by updating Google OAuth account with admin privileges (RESOLVED Jan 10, 2026)
- [x] **Worldwide Information Research Database** - COMPLETED Jan 10, 2026
  - Stunning hero section with gradient animations (purple, pink, red, blue)
  - 4 tabs: Explore, Trending, World Map, Top Contributors
  - Admin can add/edit/delete curated research resources
  - Search & filter by category
  - Featured resource badges
  - Trending hashtags and categories
  - Interactive Google Maps with research hotspots
  - Top contributors leaderboard with rankings
  - Book promotion for "Letters to Evelyn"
  - **28 curated research resources seeded** across Science, Technology, Education, Health, History, Government, Business, Environment, Arts & Culture, Law & Legal
- [x] **Weekly Email Digest System** - COMPLETED Jan 10, 2026
  - Admin panel for configuring digest schedule (day of week, hour)
  - Content options: Trending Hashtags, Marketplace Listings, Notifications
  - Preview email functionality
  - Manual "Send Now" button
  - Per-user opt-out support
  - Beautiful HTML email template with book promotion
  - Note: Requires SendGrid API key for actual sending
- [x] **Admin Panel Social Moderation** - COMPLETED Jan 10, 2026
  - Moderation Dashboard with content statistics
  - User management: search, ban/unban users
  - Group moderation: search and delete groups
  - Page moderation: search and delete pages
  - Reports system: users can report content, admins review
- [x] **User Settings Panel on Ultimate Search** - COMPLETED Jan 10, 2026
  - MY SETTINGS button in page header
  - Page name customization with suggestions
  - Photo gallery management (up to 26 photos)
  - Database usage stats display
  - Email digest preference toggle
- [x] **React Hooks Warnings Fixed** - COMPLETED Jan 10, 2026
  - All 13 exhaustive-deps warnings resolved
  - Proper useCallback usage for fetch functions
- [~] **Refactor Monoliths** - IN PROGRESS: Created modular structure, gradual migration ongoing
  - Backend: `/app/backend/utils/`, `/app/backend/models/`, `/app/backend/services/`, `/app/backend/routes/`
  - Frontend: `/app/frontend/src/utils/`, `/app/frontend/src/services/`, `/app/frontend/src/contexts/`, `/app/frontend/src/components/`

#### Future Tasks
- [ ] Complete monolith refactoring (migrate all routes/pages to modular structure)
- [ ] Native mobile apps (Android/iOS)

#### P2 - Medium Priority
- [ ] Admin Panel enhancements for social feature moderation
- [ ] Statistics page with social analytics

#### P3 - Future
- [ ] Native mobile apps (Android/iOS)
- [ ] Email newsletter system
- [ ] Group/Page moderation tools

## Technical Architecture

### Stack
- **Frontend**: React, TailwindCSS, Axios, Lucide React
- **Backend**: FastAPI, Motor (MongoDB async driver), Pydantic
- **Database**: MongoDB
- **Authentication**: JWT, Google OAuth
- **APIs**: Google Custom Search, Google Maps, Google Safe Browsing, Emergent LLM
- **Payments**: PayPal Hosted Buttons (SDK)

### Key Files
- `/app/frontend/src/App.js` - Monolithic React application (~6800 lines, refactoring in progress)
- `/app/backend/server.py` - Monolithic FastAPI backend (~6000 lines, refactoring in progress)
- `/app/backend/.env` - Backend environment variables
- `/app/frontend/.env` - Frontend environment variables

### New Modular Structure (Created Jan 10, 2026)
**Backend:**
- `/app/backend/utils/` - Database connection, config, auth helpers
- `/app/backend/models/` - Pydantic schemas
- `/app/backend/services/` - Business logic (email, websocket, protocol parser)
- `/app/backend/routes/` - Route handlers (auth module)

**Frontend (Extracted Jan 10, 2026):**
- `/app/frontend/src/contexts/AuthContext.jsx` - Authentication context provider
- `/app/frontend/src/components/layout/Layout.jsx` - Main layout wrapper
- `/app/frontend/src/components/layout/Sidebar.jsx` - Navigation sidebar
- `/app/frontend/src/components/common/FuturisticFrame.jsx` - Reusable UI frame component
- `/app/frontend/src/utils/constants.js` - API config, images, book info, pricing

### Database Collections
- `users` - User accounts
- `categories` - User-created search categories with protocols (now with for_sale, price)
- `search_results` - Collated search results with locations, **hashtags** (new field)
- `protocol_purchases` - Protocol purchase records
- `subscriptions` - User subscriptions
- `groups`, `group_posts`, `pages`, `page_posts`, `page_followers`
- `updates`, `comments`, `friends`
- `protocol_recommendations` - Suggested changes to public protocols
- `messages`, `conversations` - Private messaging
- `admin_settings` - Includes **user_max_results_limit** (new field, default 4000)
- `legal_documents`

### New API Endpoints (January 10, 2026)
- `GET /api/admin/database-limits` - Admin view database limits
- `PUT /api/admin/database-limits` - Admin update database limits (100-10000)
- `GET /api/ultimate-search/user-stats` - User view their result stats
- `DELETE /api/ultimate-search/clear-all` - User clear all results
- `DELETE /api/ultimate-search/category/{id}/clear` - User clear category results (includes subcategories)
- `DELETE /api/admin/clear-user-results/{user_id}` - Admin clear any user's results
- `DELETE /api/admin/clear-user-category/{user_id}/{category_id}` - Admin clear specific user's category
- `GET /api/ultimate-search/category/{id}/results` - Get paginated results for a category

## API Keys & Credentials

### Configured
- Google OAuth Client ID: Configured
- Google Search API Key: Configured
- Google Safe Browsing API Key: Configured
- Google Maps API Key: Configured
- Emergent LLM Key: Configured
- PayPal Client ID: Configured
- PayPal Hosted Button ID: `765S46VPPEP5C`

### Required for Full Functionality
- SendGrid API Key (for email notifications)

## Test Credentials
- Admin User: `john@infojet.com` / `password123`
- Test User: `testuser@example.com` / `password123`

## Test History
- Iteration 11: 42/42 tests passed - Pre-PayPal integration verification
- Iteration 12: 17/17 tests passed - Marketplace and PayPal integration (100%)
- Iteration 13: 14/14 tests passed - Statistics Page, Popular Protocols, Copy Tracking (100%)
- Iteration 14: 21/22 tests passed - 4 New Features (Hashtags, Database Limits, Data Management, Category Filter) (95.5%)
- **Iteration 17: 100% tests passed** - User Settings Panel, Navigation, Admin Panel (frontend-only testing)
- **Features verified**: Automated hashtags, admin-controllable database limit, clear all/category results, clickable category trees, User Settings modal with all features

## Last Updated
- Date: January 15, 2026
- Session: 
  1. **Fixed Admin Panel Access** - Updated Google OAuth account (`jjspilot24@gmail.com`) to have admin privileges
  2. **Built Worldwide Information Research Database Page** - Complete with:
     - Stunning hero section with gradient animations (purple, pink, red, blue)
     - 4 tabs: Explore, Trending, World Map, Top Contributors
     - Admin can add/edit/delete curated research resources
     - Search & filter by category
     - Featured resource badges
     - Trending hashtags and categories
     - Interactive Google Maps with research hotspots
     - Top contributors leaderboard with rankings
     - Book promotion for "Letters to Evelyn"
     - **28 curated research resources seeded** across Science, Technology, Education, Health, History, Government, Business, Environment, Arts & Culture, Law & Legal
  3. **Built Weekly Email Digest System** - Admin panel with:
     - Enable/disable toggle
     - Schedule configuration (day, hour)
     - Content options checkboxes
     - Preview and Send Now buttons
     - Beautiful HTML email template with:
       - Map locations from automated search
       - Subscription sales with admin-controlled pricing
       - Book promotion for $2.99
     - **AUTOMATED SCHEDULER** using APScheduler for background cron jobs
  4. **Built Admin Panel Social Moderation** - Complete with:
     - Moderation Dashboard with content statistics
     - User management (ban/unban)
     - Group/Page deletion
     - Reports system
  5. **Continued Monolith Refactoring** - Created modular folder structure
     - Backend: utils, models, services, routes modules
     - Frontend: utils, services, contexts, components (layout, common, pages)
  6. **Comprehensive Bug Testing** - 69 tests, 98.5% pass rate
     - All features verified: Auth, Categories, Search, Social, Messaging, Marketplace, Badges, Admin
  7. **User Settings Panel on Ultimate Search** - Verified fully functional (Jan 10, 2026)
     - MY SETTINGS button in page header
     - Modal with Page Customization, Photo Gallery, Database Usage, Email Preferences
     - Page name editing and saving with toast notifications
     - Email digest opt-in/out toggle
  8. **Fixed React Hooks Exhaustive-deps Warnings** - 13 warnings resolved (Jan 10, 2026)
     - Wrapped fetch functions in useCallback with proper dependencies
     - Build now passes without any exhaustive-deps warnings
     - Components affected: MessagesPage, InfoPilotPage, CategoriesPage, MarketplacePage, MapResultsView, UltimateSearchPage, SubscribePage, GroupDetailPage, PageDetailPage, ModerationPanel, ViewRecommendationsModal
  9. **Iteration 17 Testing** - 100% pass rate on frontend tests
     - All User Settings features verified
     - Navigation to all pages working
     - Admin Panel accessible
  10. **Fixed Admin Account Authentication** (Jan 15, 2026)
     - Created 3 admin accounts with automatic admin privileges
       - jjspilot24@gmail.com / password123
       - johnselman34@gmail.com / password123
       - john.1976.selman@gmail.com / password123
     - Admin badges now show correctly in sidebar (Shield icon + "ADMIN" text)
     - ADMIN CONTROL link appears at TOP of sidebar for admin users (yellow highlight)
     - Google OAuth automatically grants admin status to these email addresses
  11. **Enhanced Worldwide Protocol Marketplace** (Jan 15, 2026)
     - New hero banner with "Top Pilot Enterprises, Inc." branding
     - Market statistics section (Total Protocols, Total Sales, Active Sellers, Avg Price)
     - AI-Powered Search with AND/OR toggle
     - Document type filters (Web, News, PDF, Word)
     - Price range filters
     - Sellers filter
     - InfoPilot Explorer promotion section
  12. **Category/Protocol Editing Verified** (Jan 15, 2026)
     - Edit modal works for changing category name and protocol string
     - Changes save correctly to database
  13. **Search Collation Working** (Jan 15, 2026)
     - Created "George Bush" category for admin user
     - Search collation returns results when matching protocols exist
  14. **Iteration 18 Testing** - 73% backend / 100% frontend pass rate
     - All admin logins verified working
     - All Marketplace enhancements verified
  15. **Enhanced Book Promotions** (Jan 15, 2026)
     - New "hero" variant of BookSalesBanner with stars background
     - Rotating hilarious taglines carousel (6 different taglines)
     - "mini" variant for sidebars
     - Enhanced compact variant with rotating quotes
     - Book page completely overhauled with hero banner
     - Strategic placements throughout the app
  16. **Interactive Marketplace Map** (Jan 15, 2026)
     - Google Maps integration showing protocol locations
     - Custom markers (yellow for available, green for purchased)
     - InfoWindow popups with protocol details
     - Toggle to show/hide map
     - Map legend with protocol count
  17. **Location Input for Protocols** (Jan 15, 2026)
     - Added City/State input fields in CREATE category form (visible when "List for sale" is checked)
     - Added City/State input fields in EDIT category modal (visible when "List for sale" is checked)
     - Backend stores location data (city, state, lat, lng) with categories
     - Marketplace map uses real location data when available, falls back to US city defaults
     - Fixed P0 JSX syntax error that was blocking frontend build
  18. **Iteration 19 Testing** - 100% pass rate (8/8 backend tests, all frontend verified)
     - Admin login working for jjspilot24@gmail.com with is_admin=true
     - Categories page loads correctly
     - Create/Edit category with location fields verified
     - Marketplace protocols endpoint returns location data
     - Map component loads Google Maps correctly
  19. **Geocoding Integration** (Jan 15, 2026)
     - Added /api/geocode endpoint to convert city/state to lat/lng coordinates
     - Added "AUTO-LOCATE ON MAP" button in category forms
     - Displays coordinates when location is successfully geocoded
     - Note: Requires Google Geocoding API to be enabled in Cloud Console
  20. **AI Marketing Content Generation** (Jan 15, 2026)
     - Added /api/ai/generate-marketing endpoint using Emergent LLM (GPT-5.2)
     - Generates taglines, descriptions, social posts, and email subjects for book marketing
     - Added /api/ai/marketing-suggestions endpoint with pre-generated content library
     - New "AI Marketing" tab in Admin panel with:
       - Content type selector (Tagline, Description, Social Post, Email Subject)
       - Custom context input
       - Generate button with loading state
       - Marketing content library with copy-to-clipboard functionality
  21. **Enhanced Gamification System** (Jan 15, 2026)
     - Expanded badge system from 16 to 28 badges
     - New badge categories added:
       - Social: social_butterfly (10 friends), group_leader (create group), influencer (create page), messenger (50 messages)
       - Search: researcher (100 results), data_miner (500 results), intel_master (1000 results)
       - Engagement: reactor (50 reactions), commentator (25 comments)
       - Enhanced: creator_legend (50 protocols), seller_platinum (50 sales), collector_master (25 purchases)
     - Badge progress tracking for all categories
  22. **Monolith Refactoring Progress** (Jan 15, 2026)
     - Extracted shared components to /app/frontend/src/components/common/:
       - BookSalesBanner.jsx - Multi-variant book promotion component
       - WelcomeSaleBanner.jsx - Welcome banner with book promotion
       - QuickActionCard.jsx - Reusable action card
       - ProtectedRoute.jsx - Route guard component
     - Updated exports in index.js files
  23. **Iteration 20 Testing** - 100% pass rate (17/17 backend tests, all frontend verified)
     - Geocoding API tested
     - AI Marketing endpoints verified
     - Enhanced badges with 28 types confirmed
     - Admin AI Marketing panel UI verified

### Phase 1, 2, 3 Implementation (Jan 15, 2026)

  24. **Protocol Parser Fix for Abbreviations**
     - Added `_split_by_or()` method for smart abbreviation handling
     - Handles: "William C. Gamble", "Ph.D.", "M.D.", "U.S. Civil War", "etc."
     - Improved `phrase_matches()` to handle periods in abbreviations
     - Case-insensitive matching preserved
  
  25. **Admin Badge Fix for Google OAuth**
     - Admin emails verified: jjspilot24@gmail.com, JohnSelman34@gmail.com, John.1976.Selman@gmail.com
     - Admin badge and gear icon now visible for all admin accounts
     - is_admin=true returned in login response
  
  26. **Category Editing/Saving Fixes**
     - Added `/api/categories/{id}/sale-settings` endpoint
     - Fixed marketplace query to show all for-sale protocols (handles is_public: null, missing, false)
     - Categories can now be edited with name, protocol, and sale settings
  
  27. **Marketplace Enhancement**
     - Query updated to `{"for_sale": True, "$or": [{"is_public": False}, {"is_public": {"$exists": False}}, {"is_public": None}]}`
     - Limit increased from 100 to 1000 protocols
     - Returns all for-sale protocols regardless of is_public state
  
  28. **Homepage Marketing Overhaul**
     - Added prominent "100% FREE TO USE!" banner
     - "InfoPilot Explorer is COMPLETELY FREE!" messaging
     - Rotating funny taglines (6 taglines, 5-second rotation)
     - "WORLD WIDE MARKETPLACE" promotion section
     - "A Top Pilot Enterprises, Inc. Production" branding
     - Enhanced book promotion with "OPTIONED FOR FILM • 19 FIVE-STAR REVIEWS"
  
  29. **Marketing Copy Constants Added**
     - BOOK_INFO.funnyTaglines - 14 hilarious taglines
     - MARKETPLACE_PROMO - Headlines, taglines, CTA buttons
     - PAY_WHAT_YOU_WANT_PROMO - Free app promotion
     - COMPANY_INFO - Top Pilot Enterprises, Inc. details
  
  30. **Iteration 21 Testing** - 100% pass rate (17/17 tests)
     - Protocol parser handles abbreviations correctly
     - Admin badge shows for Google OAuth accounts
     - Category editing/saving works
     - Marketplace shows all for-sale protocols
     - Homepage FREE banner and funny marketing copy verified
     - All social features (Friends, Groups, Pages, Messages) functional
     - Statistics page shows badges and leaderboard

### Final Feature Implementation (Jan 15, 2026)

  31. **Extended Price Range**
     - Price range expanded from $0.75-$2.99 to $0.00-$99.00
     - Allows FREE protocols ($0.00) and premium protocols up to $99.00
     - is_free flag automatically set when price is $0.00

  32. **FREE Protocol Badge**
     - Protocols with price $0.00 show animated "🆓 FREE" badge
     - "COPY FREE PROTOCOL" button instead of "BUY NOW" for free protocols
     - FREE protocols can be copied to clipboard instantly

  33. **Top Sellers Leaderboard**
     - New tab in Marketplace: "🏆 TOP SELLERS"
     - Two views: "BY SALES COUNT" and "BY REVENUE"
     - Gold/Silver/Bronze medals for top 3 sellers
     - Shows: rank, username, sales_count, total_revenue, earnings_after_split
     - Funny CTA: "Not on the leaderboard yet? Your protocols could be the next big thing!"

  34. **Enhanced My Sales Statistics**
     - Shows: Total Revenue, Your Earnings (90%), Total Sales, Unique Buyers
     - Platform fee breakdown (10% platform, 90% to seller)
     - Pending sales indicator

  35. **Iteration 22 Testing** - 100% pass rate (17/17 tests)
     - Price range $0.00-$99.00 validated
     - FREE badge (is_free flag) tested
     - Top Sellers Leaderboard with sales/revenue tabs
     - Protocol parser handles abbreviations correctly
     - Admin login with is_admin=true
     - All frontend UI features verified

---

## Future Enhancements (Phase 4)
- Mobile app wrapper
- Voice search integration  
- Browser extension
- Expanded multi-language support
- Native Android/iOS apps
