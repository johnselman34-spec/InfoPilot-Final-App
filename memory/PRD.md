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

#### Statistics Page (NEW - Enhanced)
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

#### Protocol Marketplace (NEW)
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

#### Security
- [x] Google Safe Browsing API integration
- [x] URL safety checks before categorization
- [x] Blocked words filtering

#### Admin Panel
- [x] Settings management
- [x] User management
- [x] Subscription configuration (PayPal links, prices, promo dates)
- [x] Legal documents editing (Privacy Policy, Terms of Service)

### Pending Features 🔄

#### P1 - High Priority
- [x] Real-time WebSocket messaging
- [ ] Automated PayPal IPN for subscription verification

#### P2 - Medium Priority
- [ ] Admin Panel enhancements for social feature moderation
- [ ] Statistics page with social analytics

#### P3 - Future
- [ ] Native mobile apps (Android/iOS)
- [ ] Email newsletter system
- [ ] Global Research Database page
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
- `/app/frontend/src/App.js` - Monolithic React application (~5000 lines, needs refactoring)
- `/app/backend/server.py` - Monolithic FastAPI backend (~4000 lines, needs refactoring)
- `/app/backend/.env` - Backend environment variables
- `/app/frontend/.env` - Frontend environment variables

### Database Collections
- `users` - User accounts
- `categories` - User-created search categories with protocols (now with for_sale, price)
- `search_results` - Collated search results with locations
- `protocol_purchases` - Protocol purchase records
- `subscriptions` - User subscriptions
- `groups`, `group_posts`, `pages`, `page_posts`, `page_followers`
- `updates`, `comments`, `friends`
- `protocol_recommendations` - Suggested changes to public protocols
- `messages`, `conversations` - Private messaging
- `admin_settings`, `legal_documents`

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
- Iteration 14: Badges & Achievements system implemented and verified
- Iteration 15: Badge notifications with book/subscription promotions implemented
- **Iteration 16: Real-time WebSocket messaging and PayPal IPN implemented**

## Last Updated
- Date: January 10, 2026
- Session: Added WebSocket real-time messaging with typing indicators, PayPal IPN for automatic subscriptions
- All features tested and working
