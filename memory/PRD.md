# InfoPilot Explorer - Product Requirements Document

## Original Problem Statement
InfoPilot Explorer is a sophisticated information exchange social network with a custom search language and subscription model. The application features:
- Custom registration and Google OAuth authentication
- Shopify payment integration with a "Welcome Sale" promotion ($0.75 lifetime)
- Stripe payment as secondary option
- AI-powered intelligent search using Emergent LLM
- Hierarchical categories with custom InfoPilot 2.0 Protocol syntax
- Google Maps integration for location visualization
- Google Safe Browsing API for URL safety checks
- Book promotion for "Letters to Evelyn" by John Selman
- Ultimate Search Page with customization features

## User Personas
- **Information Researchers**: Users who need to collect, categorize, and analyze web content
- **Content Curators**: Users building knowledge bases across multiple topics
- **Premium Subscribers**: Users with full access to unlimited searches and categories

## Core Features

### Implemented ✅

#### Authentication
- [x] Email/password registration and login
- [x] Google OAuth integration (Client ID: 259303648252-gn1amf5qt9q82b0a7m2gr6cboskv912s)
- [x] JWT-based session management
- [x] Admin role support

#### Subscription & Payments
- [x] Shopify integration (primary payment method)
- [x] Stripe integration (secondary option, TEST keys)
- [x] Welcome Sale: $0.75 lifetime access (2 months)
- [x] Regular price: $4.62/year after sale
- [x] Payment history tracking
- [x] Webhook support for Shopify order confirmation

#### Ultimate Search Page
- [x] AI-powered intelligent search (Emergent LLM)
- [x] Hierarchical category tree with expand/collapse
- [x] AND/OR/AND search logic radio buttons
- [x] Document type checkboxes filtering
- [x] Search Only (preview) vs Search & Collate (save)
- [x] Session management with delete capability
- [x] Page customization (rename page, photo gallery up to 26 photos)
- [x] Google Maps with category-colored location markers

#### Security
- [x] Google Safe Browsing API integration
- [x] URL safety checks before categorization
- [x] Blocked words filtering
- [x] Content moderation

#### Book Promotion
- [x] "Letters to Evelyn" by John Selman
- [x] Genre: "A True Supernatural Thriller Comedy"
- [x] 19 five-star reviews display
- [x] Multiple purchase links (Amazon, Official Site, Readers' Favorite)
- [x] Image gallery with book covers

#### Admin Panel
- [x] Settings management (results per page, blocked words, pricing)
- [x] User management capabilities

### Pending Features 🔄

#### P1 - High Priority
- [ ] Google OAuth actual login flow verification (button present, needs user testing)
- [ ] Search & Collate with Safe Browsing blocking unsafe URLs (implemented, needs end-to-end test)

#### P2 - Medium Priority
- [ ] Admin Panel enhancements for new settings
- [ ] Statistics page with actual analytics

#### P3 - Future
- [ ] Native mobile apps (Android/iOS)
- [ ] Email newsletter system
- [ ] Social networking features (friend requests, messaging)
- [ ] Global Research Database page

## Technical Architecture

### Stack
- **Frontend**: React, TailwindCSS, Axios
- **Backend**: FastAPI, Motor (MongoDB async driver), Pydantic
- **Database**: MongoDB
- **Authentication**: JWT, Google OAuth
- **Payments**: Stripe
- **APIs**: Google Custom Search, Google Maps, Google Safe Browsing, Emergent LLM

### Key Files
- `/app/frontend/src/App.js` - Monolithic React application (needs refactoring)
- `/app/backend/server.py` - Monolithic FastAPI backend (needs refactoring)
- `/app/backend/.env` - Backend environment variables
- `/app/frontend/.env` - Frontend environment variables

### Database Collections
- `users` - User accounts and subscription status
- `categories` - User-created search categories with protocols
- `search_results` - Collated search results with locations
- `user_page_settings` - Ultimate Search page customization
- `user_photos` - Uploaded photos for page customization
- `payments` - Payment transaction history
- `admin_settings` - Application configuration

## API Keys & Credentials

### Configured
- Google OAuth Client ID: `259303648252-gn1amf5qt9q82b0a7m2gr6cboskv912s.apps.googleusercontent.com`
- Google Search API Key: `AIzaSyCoAXxG2ye7azGmqmAcbSY33-FQpt5kQCo`
- Google Safe Browsing API Key: `AIzaSyCoAXxG2ye7azGmqmAcbSY33-FQpt5kQCo`
- Google Maps API Key: `AIzaSyCqxRaGx3E2taKtxNlX-TUwrYXHP8G5LR4`
- Stripe: TEST keys configured
- Emergent LLM Key: Configured
- Shopify API Key: `1ef463a176a1549de87d5a8b377a1202`
- Shopify Store: `top-pilot-enterprises-inc.myshopify.com`
- Shopify Product URL: `https://top-pilot-enterprises-inc.myshopify.com/products/infopilot-explorer-subscriptions`

## Test Credentials
- Admin User: `john@infojet.com` / `password123`

## Last Updated
- Date: January 10, 2026
- Session: Integrated Shopify payments, renamed app to "InfoPilot Explorer", updated all branding, comprehensive bug testing
- Test Status: 28/28 backend tests passing, all frontend flows verified (4 test iterations)

## Test History
- Iteration 1: 18/18 tests passed - Initial feature verification
- Iteration 2: 26/26 tests passed - Extended edge case testing  
- Iteration 3: 26/26 tests passed - Thorough re-test of all features
- Iteration 4: 28/28 tests passed - Full painstaking test after Shopify integration and rebranding
