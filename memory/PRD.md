# InfoPilot - Product Requirements Document

## Overview
InfoPilot is a web-based information search, categorization, and social networking platform. It enables users to search the web using SerpAPI, automatically classify and collate results using custom Boolean protocols (InfoPilot 2.0), and interact with a community of researchers and information seekers.

## Product Vision
"The Galactic Archivist" - A cosmic-themed knowledge discovery platform that transforms web research into an organized, visual, and social experience.

## Target Audience
- Researchers and academics
- Information seekers who want organized search results
- Users interested in social features around information sharing
- Premium users who want geographic visualization of data

---

## Core Features

### 1. Authentication System ✅
- Email/password registration and login
- JWT token-based authentication
- Premium user status tracking
- Admin role support

### 2. Search & Collation (InfoJet) ✅
- **Web Search**: Powered by SerpAPI for Google search results
- **InfoPilot 2.0 Protocol**: Boolean logic for automatic categorization
  - Supports: AND (&), OR (|), NOT (-), parentheses for grouping
  - Example: `(artificial intelligence | machine learning) & research`
- **Automatic Collation**: Results matched against user-defined categories

### 3. Categories System ✅
- Create custom categories with Boolean protocols
- Public/private categories
- Category hierarchy support (parent categories)
- Level indicators for nested categories

### 4. Interactive World Map (Premium) ✅
- **Technology**: Leaflet.js with react-leaflet v4.2.1
- Dark-themed CartoDB basemap matching app aesthetic
- Color-coded markers by category
- Click markers to open source articles
- Category filtering for map markers

### 5. Social Features ✅
- **Feed**: View posts from the community
- **Friends**: Friend list and friend requests
- **Groups**: Create and join Facebook-like groups
- **Pages**: Create and follow pages
- **Reactions**: 7 reaction types (Like, Love, Funny, Sad, Caution, Spam, Best)
- **Comments**: Comment on posts and search results

### 6. Settings & Profile ✅
- User profile display
- Premium status indicator
- Privacy toggles (show online status, show friend status)
- Account security information

### 7. Book Promotion - "Letters to Evelyn" ✅
- **Full Promo Section** on Dashboard with:
  - Beautiful book cover display with cosmic woman artwork
  - Gradient title with cosmic styling
  - Promotional taglines ("I FLEW JETS THEN REALITY BROKE", etc.)
  - Image carousel with 4 promotional images including "Terror of the Cosmic Gulper" dinosaur
  - "Get Your Copy on Amazon" CTA button linked to: https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191
- **Compact Promo** on Settings and InfoJet pages
- Book images from customer assets

### 8. Premium Subscription Upsell ✅
- **Enhanced Map Page Upsell** for non-premium users featuring:
  - Global Network globe background image
  - "Unlock the World Map" gradient title
  - Feature pills: Interactive Markers, Category Colors, One-Click Sources
  - "Upgrade for Only $0.99" CTA button
  - Book promo displayed below upsell for cross-selling

---

## Technical Architecture

### Frontend
- **Framework**: React 18
- **Styling**: Custom CSS with Tailwind utilities
- **Theme**: "Galactic Archivist" - dark cosmic theme
  - Colors: Purple (#8B5CF6), Blazing Pink (#F43F5E), Deep Blue (#3B82F6)
  - Glassmorphism effects with backdrop blur
  - Gradient buttons with glow effects
- **Map**: Leaflet.js via react-leaflet v4.2.1

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB with Motor async driver
- **Search API**: SerpAPI (Google Search)
- **Authentication**: JWT tokens

### Key Files
- `/app/frontend/src/App.js` - Main React application
- `/app/frontend/src/App.css` - Galactic Archivist theme styles
- `/app/backend/server.py` - FastAPI backend
- `/app/backend/.env` - Environment configuration

---

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Categories
- `GET /api/categories` - List user categories
- `POST /api/categories` - Create category
- `PUT /api/categories/{id}` - Update category
- `DELETE /api/categories/{id}` - Delete category

### Search
- `POST /api/search` - Web search via SerpAPI
- `POST /api/collate` - Collate results with categories
- `POST /api/search_and_collate` - Combined search and collate
- `GET /api/ultimate-search` - Get saved results
- `GET /api/ultimate-search/stats` - Get search statistics

### Social
- `GET /api/feed` - Get social feed
- `GET /api/posts` - Get posts
- `POST /api/posts` - Create post
- `POST /api/posts/{id}/react` - React to post
- `GET /api/friends` - Get friends list
- `GET /api/groups` - Get groups
- `GET /api/pages` - Get pages

### Map
- `GET /api/map-data` - Get geolocated results for map

### Settings
- `PUT /api/users/settings` - Update user settings
- `GET /api/payment/link` - Get PayPal payment link

---

## Completed Work (January 2026)

### Session 1 - Initial Setup
- [x] Imported codebase from GitHub
- [x] Converted React Native app to React web app
- [x] Set up FastAPI backend with MongoDB
- [x] Implemented basic authentication

### Session 2 - Feature Implementation & Design
- [x] Implemented SerpAPI integration with valid API key
- [x] Fixed ObjectId serialization issues in backend
- [x] Implemented interactive Leaflet.js map (premium feature)
- [x] Applied "Galactic Archivist" theme with dazzling purple/pink design
- [x] Verified all API endpoints return data correctly
- [x] All 17 backend tests passing
- [x] All frontend pages functioning correctly

---

## Upcoming Tasks (P0 - High Priority)

### Search Protocol Logic Enhancement
- Fix multi-word phrase handling in InfoPilot 2.0 protocol
- Support abbreviations with punctuation (e.g., "U.S.")
- Case-insensitive matching

### Social Features Completion
- Full Groups CRUD functionality
- Full Pages CRUD functionality
- User search and friend request system
- Admin as first friend for new users

---

## Future Tasks (P1 - Medium Priority)

### Monetization
- PayPal integration for subscriptions ($0.99)
- Allow users to sell access to their protocols
- "Letters to Evelyn" book promotion section

### Admin Panel
- User management
- Content moderation
- Feature flags (search limits for free users)
- Subscription price configuration

### Additional Features
- User achievements and badges
- User-to-user messaging with images
- Automated email newsletters
- Statistics page with charts
- Article type classification rules

---

## Known Issues

### Minor
- Some ESLint warnings (unused variables) - non-blocking
- Map markers show "0 locations" when no geolocated results exist

### Resolved
- ~~ObjectId serialization error~~ ✅ Fixed
- ~~Interactive map not working~~ ✅ Fixed with Leaflet.js
- ~~SerpAPI not configured~~ ✅ Fixed with valid API key

---

## Test Credentials
- **Email**: test@example.com
- **Password**: password123
- **Status**: Premium user (is_paid=true)

---

## Environment Variables

### Backend (.env)
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="infopilot_db"
CORS_ORIGINS="*"
SERPAPI_KEY="[configured]"
PAYPAL_CLIENT_ID="[configured]"
PAYPAL_SECRET="[configured]"
PAYPAL_BUTTON_ID="765S46VPPEP5C"
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=[preview URL]
```
