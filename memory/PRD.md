# InfoPilot Explorer - Product Requirements Document

## Original Problem Statement
Build a comprehensive web application called "InfoPilot Explorer" featuring:
- **InfoJet 2.0™** - A proprietary search and categorization language
- **Protocol Marketplace** - Buy/sell search protocols (90/10 revenue split)
- **Social Features** - Groups, Pages, Feeds, Notifications
- **Interactive Map** - Geolocated search results
- **Gamification** - Points, levels, badges, leaderboards
- **Promotional Content** - Letters to Evelyn book, InfoPilot, Maestro Bistro

## Parent Company
**Top Pilot Enterprises, Inc.**
- "Three ventures. One mission. Zero turbulence."

## Three Business Ventures
1. **Letters to Evelyn** by John Selman - Supernatural Thriller Comedy Memoir (Amazon)
2. **InfoPilot Explorer** - World Wide Information Exchange Platform
3. **Maestro Bistro** - Brunswick, Maine (Beef, Vegetable, Fish Chowder)

## User Accounts
### Admin Accounts
- **jjspilot24@gmail.com** - Primary Admin (Password: InfoPilot2024!)
- **JohnSelman34@gmail.com** - Admin (Password: InfoPilot2024!)
- **john.1976.selman@gmail.com** - Admin (Password: InfoPilot2024!)

### Test Account
- **test@infojet.com** / testpass123

## What's Been Implemented (January 2026)

### Core Features ✅
- [x] User authentication (Google OAuth + Email/Password)
- [x] Admin badge display in sidebar
- [x] Ultimate Search with InfoJet 2.0 protocol language
- [x] Category creation, editing (name, protocol, visibility)
- [x] Protocol parsing with abbreviation support (William C. Gamble, etc.)
- [x] Collate button for batch search execution
- [x] Interactive Map for geolocated results
- [x] Statistics/Analytics page

### Marketplace ✅
- [x] Browse protocols with filtering/sorting
- [x] Sell protocols ($0.99-$99.99, 90% to creator)
- [x] PayPal integration for payments
- [x] Seller dashboard with earnings
- [x] Purchase history

### Social Features ✅
- [x] Groups (create, join, post)
- [x] Pages (create, follow)
- [x] Friends system
- [x] Real-time notifications (WebSockets)
- [x] Web Push notification infrastructure

### Gamification ✅
- [x] Points system
- [x] Badges (First Search, Power User, etc.)
- [x] Leaderboard
- [x] User profiles with stats

### Promotional Content ✅
- [x] Top Pilot Enterprises banner
- [x] Letters to Evelyn book promotion (images, reviews, buy links)
- [x] InfoPilot Explorer features section
- [x] Maestro Bistro menu section
- [x] Rotating taglines and quotes

### Admin Features ✅
- [x] Admin dashboard with statistics
- [x] User management
- [x] System settings (search pages, rate limits)
- [x] Newsletter management (Resend integration)

### Technical ✅
- [x] PWA support (manifest.json, sw.js)
- [x] Mobile responsiveness
- [x] User data export
- [x] Backend refactored into modular routes/services

## Architecture

```
/app/
├── backend/
│   ├── server.py           # Main FastAPI app (2.2k lines)
│   ├── routes/             # Modular API routes
│   │   ├── auth.py         # Authentication
│   │   ├── categories.py   # Category CRUD
│   │   ├── search.py       # Search endpoints
│   │   ├── social.py       # Groups, Pages, Posts
│   │   ├── notifications.py # WebSocket + Push
│   │   └── marketplace.py  # Protocol marketplace
│   └── services/           # Business logic
│       ├── protocol_service.py
│       └── search_service.py
└── frontend/
    └── src/
        ├── pages/          # React pages
        ├── components/     # Shared components
        ├── contexts/       # Auth, Theme contexts
        └── public/         # PWA assets
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Email/password login
- `POST /api/auth/register` - User registration
- `GET /api/auth/google` - Google OAuth initiation
- `GET /api/auth/google/callback` - OAuth callback

### Categories
- `GET /api/categories` - List user categories
- `POST /api/categories` - Create category
- `PUT /api/categories/{id}` - Update category (name, protocol, is_public)
- `DELETE /api/categories/{id}` - Delete category

### Search
- `POST /api/search` - Quick search
- `POST /api/collate` - Collate category results
- `GET /api/ultimate-search` - Get stored results
- `POST /api/protocol/debug` - Debug protocol parsing

### Marketplace
- `GET /api/marketplace/protocols` - Browse protocols
- `POST /api/marketplace/protocols` - List protocol for sale
- `POST /api/marketplace/purchase` - Purchase protocol

### Social
- `GET /api/groups` - List groups
- `POST /api/groups` - Create group
- `GET /api/pages` - List pages
- `WS /api/ws/{user_id}` - Real-time notifications

## Prioritized Backlog

### P0 (Critical)
- [x] Admin badge display - DONE
- [x] Category name editing - DONE
- [x] Search collation - DONE

### P1 (High Priority)
- [ ] Document type filters (webpage, news, PDF, MS Word)
- [ ] AI-powered search integration
- [ ] Map integration with category checkboxes
- [ ] Enhanced statistics on Marketplace

### P2 (Medium Priority)
- [ ] Web Push server-side notifications (VAPID)
- [ ] Real-time chat
- [ ] Advanced analytics visualizations
- [ ] Multi-language support

### P3 (Low Priority)
- [ ] Mobile app wrapper
- [ ] Voice search
- [ ] Collaborative protocol editing

## Third-Party Integrations
- **SerpAPI** - Web search
- **ddgs** - DuckDuckGo fallback
- **Emergent Google Auth** - OAuth
- **PayPal** - Marketplace payments
- **Resend** - Newsletter emails
- **MongoDB** - Database

## Testing
- Backend tests: `/app/tests/`
- Test reports: `/app/test_reports/iteration_*.json`
- Latest: iteration_12.json (21/21 tests passed)

## Preview URL
https://protocol-hub-5.preview.emergentagent.com
