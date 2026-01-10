# InfoPilot Explorer - Product Requirements Document

## Original Problem Statement
InfoPilot Explorer is a sophisticated information exchange social network with a custom search language. The application is now **COMPLETELY FREE** with monetization through book promotion. Features:
- Custom registration and Google OAuth authentication
- AI-powered intelligent search using Emergent LLM
- Hierarchical categories with custom InfoPilot 2.0 Protocol syntax
- Google Maps integration for location visualization
- Google Safe Browsing API for URL safety checks
- **Facebook-style social features** (Groups, Pages, Updates, Reactions, Comments)
- Book promotion for "Letters to Evelyn" by John Selman
- Ultimate Search Page with customization features

## User Personas
- **Information Researchers**: Users who need to collect, categorize, and analyze web content
- **Content Curators**: Users building knowledge bases across multiple topics
- **Social Networkers**: Users who want to share and engage with content in groups and pages

## Core Features

### Implemented ✅

#### Authentication
- [x] Email/password registration and login
- [x] Google OAuth integration (Client ID: 259303648252-gn1amf5qt9q82b0a7m2gr6cboskv912s)
- [x] JWT-based session management
- [x] Admin role support

#### App Access
- [x] **APP IS NOW COMPLETELY FREE** - No subscription required
- [x] All users get full access to all features
- [x] Book promotion replaces subscription prompts throughout the app
- [x] Admin (john_selman) added as first friend for new users

#### Social Features (NEW - Facebook-like)
- [x] **Groups**: Create/join groups (public/private/secret), post content
- [x] **Pages**: Create/follow pages with categories, post as admin
- [x] **Updates**: Post updates on Ultimate Search page
- [x] **Reactions**: Facebook-style emoji picker (👍 Like, ❤️ Love, 😂 Haha, 😮 Wow, 😢 Sad, 😠 Angry)
- [x] **Comments**: Nested replies on posts, updates, and search results
- [x] **Friends**: View and manage friend connections
- [x] **Protocol Recommendations**: Users can suggest changes to public protocols owned by others. Owners see recommendations via lightbulb badge and can Accept (apply change), Reject, or Delete

#### Ultimate Search Page
- [x] AI-powered intelligent search (Emergent LLM)
- [x] Hierarchical category tree with expand/collapse
- [x] AND/OR/AND search logic radio buttons
- [x] Document type checkboxes filtering
- [x] Search Only (preview) vs Search & Collate (save)
- [x] Session management with delete capability
- [x] Page customization (rename page, photo gallery up to 26 photos)
- [x] Google Maps with category-colored location markers
- [x] **Updates section** with reactions and comments
- [x] **Reactions/Comments on search results**

#### Security
- [x] Google Safe Browsing API integration
- [x] URL safety checks before categorization
- [x] Blocked words filtering (whole word matching only)
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
- [ ] Google Maps marker interaction enhancement

#### P2 - Medium Priority
- [ ] Admin Panel enhancements for managing social features
- [ ] Statistics page with social analytics
- [ ] Private messaging between friends

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

### Key Files
- `/app/frontend/src/App.js` - Monolithic React application (~3500 lines, needs refactoring)
- `/app/backend/server.py` - Monolithic FastAPI backend (~3700 lines, needs refactoring)
- `/app/backend/.env` - Backend environment variables
- `/app/frontend/.env` - Frontend environment variables

### Database Collections
- `users` - User accounts
- `categories` - User-created search categories with protocols
- `search_results` - Collated search results with locations
- `user_page_settings` - Ultimate Search page customization
- `user_photos` - Uploaded photos for page customization
- `groups` - Social groups
- `group_posts` - Posts in groups
- `pages` - Social pages
- `page_posts` - Posts on pages
- `page_followers` - Page follower relationships
- `updates` - User updates on Ultimate Search page
- `comments` - Comments on posts/updates/search results
- `friends` - Friend relationships
- `admin_settings` - Application configuration

## API Keys & Credentials

### Configured
- Google OAuth Client ID: `259303648252-gn1amf5qt9q82b0a7m2gr6cboskv912s.apps.googleusercontent.com`
- Google Search API Key: `AIzaSyCoAXxG2ye7azGmqmAcbSY33-FQpt5kQCo`
- Google Safe Browsing API Key: `AIzaSyCoAXxG2ye7azGmqmAcbSY33-FQpt5kQCo`
- Google Maps API Key: `AIzaSyCqxRaGx3E2taKtxNlX-TUwrYXHP8G5LR4`
- Emergent LLM Key: Configured

## Test Credentials
- Admin User: `john@infojet.com` / `password123`

## Last Updated
- Date: January 10, 2026
- Session: Implemented Protocol Recommendations feature
- Test Status: All 18 tests passed (100%)

## Test History
- Iteration 1: 18/18 tests passed - Initial feature verification
- Iteration 2: 26/26 tests passed - Extended edge case testing  
- Iteration 3: 26/26 tests passed - Thorough re-test of all features
- Iteration 4: 28/28 tests passed - Full painstaking test after Shopify integration
- Iteration 5-6: App converted to free model with book monetization
- **Iteration 7: 22/22 tests passed - Facebook-style social features (Groups, Pages, Reactions, Comments, Updates)**
- **Iteration 8: 18/18 tests passed - Protocol Recommendations feature**
