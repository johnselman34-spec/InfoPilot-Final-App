# InfoPilot Explorer - Product Requirements Document

**App Name:** InfoPilot Explorer
**Company:** Top Pilot Enterprises, Inc.
**Tagline:** "First in Flight with Monetization of Searches! It's a Bear! 🐻"
**Author/Owner:** John Selman (john.1976.selman@gmail.com, 207-522-0894)
**Location:** Brunswick, Maine

---

## 1. Core Product Vision

InfoPilot Explorer is a Worldwide Information Exchange Database that provides users with a "3D view of the internet" through custom Boolean search protocols (InfoJet 2.0). Users can categorize web content into personal categories and subcategories, visualize results on interactive maps, and sell their protocols in a marketplace.

Additionally, the app promotes:
- **Letters to Evelyn** - A True Supernatural Thriller Comedy book by John Selman
- **Maestro Bistro** - A German food truck in Brunswick, Maine

---

## 2. Implemented Features (As of January 2026)

### ✅ Core Platform Features
- [x] User authentication (register/login/logout)
- [x] JWT-based session management with MongoDB
- [x] InfoJet 2.0 Protocol Parser (Boolean search with `&`, `or`, `+`, `^` operators)
- [x] Category/Subcategory hierarchy system (unlimited depth)
- [x] "and" as synonym for "&" in protocols
- [x] Search & Collate functionality (mock data)
- [x] Quick Search within collated results
- [x] Search Aggregation modes (And/Or, And, Or)
- [x] Select All / Deselect All category buttons
- [x] Category result counts shown in parentheses

### ✅ Document Type Classification
- [x] PhD Informative detection
- [x] Informative detection
- [x] News Article detection
- [x] Blog detection
- [x] Forum detection
- [x] Personal Report (Organic) - user-written
- [x] Personal Report (Collected) - auto-detected
- [x] InfoPilot/InfoBook Exclusive

### ✅ Easter Eggs & Laughter Points
- [x] Floating Easter Eggs that appear randomly
- [x] 8 unique jokes about John's stepmother and survival story
- [x] Protocol ideas in each egg
- [x] Pricing suggestions in each egg
- [x] Map instructions in eggs
- [x] Laughter Points earned by catching eggs
- [x] Points displayed in navbar

### ✅ Marketplace
- [x] List protocols for sale with prices
- [x] Browse marketplace
- [x] Buy protocols via PayPal redirect
- [x] 85% to seller, 15% platform fee concept

### ✅ Statistics & Leaderboard
- [x] Global statistics (users, categories, results)
- [x] User statistics (points, categories)
- [x] Top Laughter Points leaderboard
- [x] Top Protocol Creators leaderboard

### ✅ PayPal Integration
- [x] InfoPilot subscription: $1.00/month or $9.98/year
- [x] Book purchase via PayPal: https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU
- [x] Amazon book link: https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J
- [x] Protocol marketplace purchases via PayPal

### ✅ Book Section (Letters to Evelyn)
- [x] Full book information display
- [x] Genre badges (Supernatural, Thriller, Comedy, Navy Memoir)
- [x] Professional reviews from Readers' Favorite
- [x] Film production mention (Voyage Media)
- [x] Price options (ebook, paperback, hardcover)
- [x] Warning labels (humor safety warnings)
- [x] PayPal and Amazon buy buttons

### ✅ Food Section (Maestro Bistro)
- [x] Menu items with prices and descriptions
- [x] German Beef Rouladen, Vegetable Rouladen, Fish Chowder
- [x] Funny taglines for each item
- [x] Shopping cart functionality
- [x] Food emojis

### ✅ Admin Features
- [x] Admin settings panel concept
- [x] Collation limit control (default 40)
- [x] Newsletter times configuration
- [x] Document type protocol customization
- [x] Banned words system
- [x] User management (ban/mute/boot/delete)
- [x] Upgrade message customization

### ✅ Legal Pages
- [x] User Agreement with "First in Flight" language
- [x] Copyright notice (code cannot be emulated)
- [x] Privacy Policy
- [x] PayPal minimum price ($1.00) explanation

### ✅ News Headlines
- [x] AI-powered headlines section
- [x] 10 headlines from different topics
- [x] Excludes entertainment news
- [x] Refresh headlines button

### ✅ UI/UX
- [x] Cosmic/Space theme with stars background
- [x] Yellow/Gold gradient branding
- [x] Glass-morphism cards
- [x] Responsive design
- [x] Toast notifications
- [x] Floating animations

---

## 3. Pending/Future Features

### 🟡 P1 - High Priority
- [ ] Interactive Map View with Leaflet (Map page placeholder exists)
- [ ] Color-coded map dots by category
- [ ] Map popup windows for search results
- [ ] Real search engine integration (Google/SerpAPI, DuckDuckGo, Brave)
- [ ] Newsletter sending system (tri-weekly at configured times)
- [ ] Personal Reports creation UI
- [ ] Chat Rooms functionality
- [ ] Groups & Pages social features

### 🟠 P2 - Medium Priority
- [ ] Revenue Dashboard with PDF export
- [ ] Quote Gallery from Letters to Evelyn
- [ ] Community features (likes, reactions to results)
- [ ] User search by name/email/username
- [ ] Friend requests and messaging
- [ ] Category editing from Settings page
- [ ] Theme Gallery with custom presets

### 🟢 P3 - Future/Backlog
- [ ] Google Play Store / Apple App Store listing
- [ ] Samsung Marketplace listing
- [ ] Real-time newsletter scheduling
- [ ] In-app browser for search results
- [ ] PayPal Connect for protocol sellers
- [ ] Bing search integration
- [ ] App store optimization with provided keywords
- [ ] Dark mode / Light mode toggle

---

## 4. Technical Architecture

### Backend (FastAPI + MongoDB)
- `/app/backend/server.py` - Monolithic API with all routes
- MongoDB collections: users, sessions, categories, search_results, admin_settings, etc.
- InfoJet 2.0 protocol parser with regex-based parsing
- Document type classification system

### Frontend (React + TailwindCSS)
- `/app/frontend/src/App.js` - Main application with routing
- React Query for data fetching
- React Router for navigation
- Context providers for Auth and Toast

### Environment Variables
- `REACT_APP_BACKEND_URL` - Backend API URL
- `MONGO_URL` - MongoDB connection string
- `DB_NAME` - Database name

---

## 5. API Endpoints

### Auth
- POST `/api/auth/register` - Create account
- POST `/api/auth/login` - Login
- GET `/api/auth/me` - Get current user
- POST `/api/auth/logout` - Logout

### Categories
- POST `/api/categories` - Create category
- GET `/api/categories` - Get user's categories
- PUT `/api/categories/{id}` - Update category
- DELETE `/api/categories/{id}` - Delete category
- POST `/api/categories/{id}/clean` - Clear category results

### Search
- POST `/api/search/collate` - Search & Collate
- GET `/api/search/results` - Get filtered results

### Easter Eggs
- GET `/api/easter-eggs/random` - Get random egg
- POST `/api/easter-eggs/catch` - Catch egg and earn points

### Marketplace
- GET `/api/marketplace/protocols` - List protocols for sale
- POST `/api/marketplace/buy/{id}` - Purchase protocol

### Other
- GET `/api/leaderboard` - Community rankings
- GET `/api/stats` - Platform statistics
- GET `/api/news/headlines` - AI news headlines

---

## 6. PayPal Configuration

- **Business Email:** JJspilot24@gmail.com
- **Subscription Link:** https://www.paypal.com/ncp/payment/LZDBN3SQU4NWQ
- **Book Purchase Link:** https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU
- **Minimum Payment:** $1.00 (PayPal requirement)

---

## 7. Contact

**John Selman**
- Email: john.1976.selman@gmail.com
- Phone: 207-522-0894
- Location: Brunswick, Maine

---

*Last Updated: January 18, 2026*
