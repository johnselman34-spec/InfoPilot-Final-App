# InfoPilot Explorer - Product Requirements Document

## Original Problem Statement
Build a comprehensive web application called "InfoPilot Explorer" featuring:
- **InfoJet 2.0™** - A proprietary search and categorization language
- **Protocol Marketplace** - Buy/sell search protocols (90/10 revenue split)
- **Social Features** - Friends, Groups, Pages, Feeds, Direct Messages
- **Interactive Map** - Geolocated search results with auto-detection
- **Gamification** - Points, levels, badges, leaderboards
- **Voice Search** - OpenAI Whisper integration
- **AI Newsletters** - GPT-5.2 generated marketing content
- **Collaborative Editing** - Real-time protocol collaboration
- **Promotional Content** - Letters to Evelyn book, InfoPilot, Maestro Bistro

## Parent Company
**Top Pilot Enterprises, Inc.**
- "Three ventures. One mission. Zero turbulence."

## Three Business Ventures
1. **Letters to Evelyn** by John Selman - Supernatural Thriller Comedy Memoir
   - eBook: $2.99 on Amazon: https://a.co/d/gsRLapf
   - Hardcover: $250 special edition: https://a.co/d/g0aeHkI
   - 19 Five-Star Reviews on Readers' Favorite
   - Optioned for Film by Voyage Media
2. **InfoPilot Explorer** - World Wide Information Exchange Platform
   - InfoJet 2.0™ proprietary search language
   - Protocol Marketplace
   - Interactive Maps
3. **Maestro Bistro** - On the Mall, Brunswick, Maine
   - deLectaBLe Beef Rouladen - Evenly spiced perfection
   - Beef Rouladen with Vegetables and Carrots - It's German Cuisine! (Yes, really!)
   - Fresh Fish Chowder - Maine's finest catch

## User Accounts
### Admin Accounts (All have is_admin: true)
- **jjspilot24@gmail.com** - Primary Admin (Password: InfoPilot2024!)
- **JohnSelman34@gmail.com** - Admin (Password: InfoPilot2024!)
- **john.1976.selman@gmail.com** - Admin (Password: InfoPilot2024!)

### Test Account
- **test@infojet.com** / testpass123

## What's Been Implemented (January 15, 2026)

### Core Features ✅
- [x] User authentication (Google OAuth + Email/Password)
- [x] Admin badge displays correctly for Google OAuth logins
- [x] Ultimate Search with InfoJet 2.0 protocol language
- [x] Category editing saves name, protocol, AND visibility
- [x] Protocol parsing with abbreviation support
- [x] Collate button showing selected category count
- [x] Interactive Map for geolocated results
- [x] **Category Filtering on Ultimate Search (AND/OR logic)**

### Enhanced Marketplace ✅ (COMPLETED January 15, 2026)
- [x] World Wide Protocol Map - Interactive map with markers
- [x] Statistics Dashboard - Total Protocols, Total Sales, Avg Price, Top Category
- [x] AI-Powered Search - Intelligent search input
- [x] Search Logic Radio Buttons - AND/OR, AND, OR
- [x] Document Type Checkboxes - Webpage, News Article, PDF, MS Word
- [x] Protocol Selection Checkboxes - Select multiple protocols with Select All/Deselect All buttons
- [x] Protocol Bundles - Buy curated collections at discount
- [x] **Pay-What-You-Want Model** - Users can pay any amount including $0 (FREE)
- [x] **Admin Revenue Split Control** - Configurable 5-30% platform fee (default 10%)
- [x] **PayPal Minimum Payout Handling** - Accumulated earnings below $1.00 threshold
- [x] **Payout Ledger Tracking** - Full audit trail of all earnings
- [x] **Category Tree with Expansion** - Expandable categories with + buttons
- [x] Revenue Distribution Display - Shows creator % vs platform fee %

### Real-Time Chat ✅ (NEW)
- [x] Chat page with sidebar and main chat area
- [x] WebSocket real-time messaging
- [x] Create new chat rooms
- [x] Online users indicator
- [x] Typing indicators
- [x] Message timestamps

### Advanced Analytics Dashboard ✅ (NEW)
- [x] Recharts integration - Beautiful charts
- [x] Summary cards (6 metrics: Users, Active, Searches, Protocols, Revenue, Avg Session)
- [x] Time range selector (7, 30, 90 days)
- [x] Chart tabs (Overview, Revenue, Users, Categories, Top Protocols)
- [x] Area charts, Bar charts, Line charts, Pie charts
- [x] Export to JSON/CSV

### Statistics Page ✅ (NEW - January 15, 2026)
- [x] Statistics Central hero banner with funny facts
- [x] Quick Stats Grid: Total Users, Active (7d), Protocols, Searches, Purchases, Revenue
- [x] Countries Pie Chart - 10 countries with percentages
- [x] US States Bar Chart - 11 states including Maine (Brunswick connection!)
- [x] Document Types Donut Chart - Webpage, News, PDF, Academic, MS Word
- [x] Top 10 Words in Protocols - Horizontal bar chart
- [x] **Top Sellers Leaderboard** with tabs:
  - By Sales Count tab
  - By Revenue tab
- [x] Funny titles for top sellers: "The Protocol Overlord 🦁", "The Protocol Billionaire 🏦", "The Silver Searcher 🥈", "The Search Tycoon 🎩"
- [x] Badges: 👑 (Legend 500+ sales), 💎 (Diamond 200+), 🏆 (Champion 100+), ⭐ (Star 50+), 🔥 (Hot 20+)
- [x] Revenue badges: 💰 ($1000+), 💵 ($500+), 💲 ($200+), 🤑 ($100+)
- [x] Book promo section with supernatural comedy marketing

### Push Notifications ✅ (NEW)
- [x] VAPID key endpoint
- [x] Push subscription management
- [x] Admin broadcast capability
- [x] Push notification stats

### Multi-Language Support (i18n) ✅ (NEW)
- [x] English (default)
- [x] Spanish (Español)
- [x] French (Français)
- [x] German (Deutsch)
- [x] Language switcher helper

### Promotional Content ✅
- [x] Top Pilot Enterprises, Inc. banner and branding
- [x] Letters to Evelyn - Rotating book images, reviews, buy links ($2.99 eBook)
- [x] InfoPilot Explorer - InfoJet 2.0™, Interactive Maps, Protocol Marketplace
- [x] Maestro Bistro - Brunswick, ME with chowder menu

### Social Features ✅ (MAJOR UPDATE - January 15, 2026)
- [x] **Friends System** - Search users, send/accept/reject requests, friends list
- [x] **Groups** - Create, join, leave, member management
- [x] **Pages** - Create, follow, unfollow, category support
- [x] **Social Feed** - Personalized posts from friends/groups/pages
- [x] **Posts with Photos** - Up to 6.9MB per photo, up to 10 photos per post
- [x] **Reactions** - Like, Love, Haha, Wow, Sad, Angry (Facebook-style)
- [x] **Comments** - Comment on posts with reactions
- [x] Real-time notifications (WebSockets)

### Direct Messaging ✅ (NEW - January 15, 2026)
- [x] **Private Conversations** - 1-on-1 messaging
- [x] **Real-time Chat** - WebSocket updates
- [x] **Image Sharing** - Up to 6.9MB per image
- [x] **Read Receipts** - Know when messages are read
- [x] **Typing Indicators** - See when someone is typing
- [x] **Online Status** - See who's online
- [x] **Conversation List** - Unread counts, last message preview

### AI Newsletter System ✅ (NEW - January 15, 2026)
- [x] **GPT-5.2 Integration** - AI-generated funny marketing content
- [x] **Newsletter Drafts** - Save and edit before sending
- [x] **Subscriber Management** - Subscribe/unsubscribe
- [x] **Campaign History** - Track sent newsletters
- [x] **Batch Sending** - Send to all subscribers
- [x] **Test Emails** - Send test before broadcast

### Voice Search ✅ (NEW - January 15, 2026)
- [x] **OpenAI Whisper** - Speech-to-text transcription
- [x] **Browser Recording** - Record audio directly in browser
- [x] **Voice History** - Track past voice searches
- [x] **Voice Stats** - Admin analytics on voice usage

### Collaborative Protocol Editing ✅ (NEW - January 15, 2026)
- [x] **Real-time Collaboration** - Multiple users editing same protocol
- [x] **User Cursors** - See where others are editing
- [x] **Version History** - Restore previous versions
- [x] **Protocol Comments** - Comment on specific lines
- [x] **Resolve Comments** - Mark comments as resolved

### Location Auto-Detection ✅ (NEW - January 15, 2026)
- [x] **Geo-extraction** - Extract locations from search results
- [x] **50 US States** - Full state coordinate database
- [x] **Major US Cities** - 20+ city coordinates
- [x] **Countries** - World coverage
- [x] **Auto-populate Map** - Results appear on map automatically

### Gamification ✅ (ENHANCED - January 15, 2026)
- [x] **22 Achievements** across 6 categories
- [x] **Level System** - 10 levels with fun names
- [x] **Points System** - 2,895 total possible points
- [x] **Shareable Badges** - Twitter/Facebook share
- [x] **Weekly/All-Time Leaderboards**

### Quick Win Features ✅ (NEW - January 15, 2026)
- [x] **Polls Feature** - Create polls in Groups, Pages, USP
  - Full CRUD API (create, read, vote, delete, close)
  - Validation (2-10 options, expiration)
  - Frontend UI with poll buttons for admins
  - PollCard component with voting functionality
- [x] **Default Admin Friend** - New users get jjspilot24@gmail.com as first friend
  - Automatic friendship upon registration
  - Works for both email/password and Google OAuth registrations
- [x] **Push Notifications for DMs** - Offline user notifications
  - send_dm_push_notification helper function
  - VAPID-based web push (simulation mode without keys)
  - Triggers when recipient is offline

### Admin Features ✅
- [x] Admin dashboard with statistics
- [x] User management
- [x] System settings
- [x] Newsletter management

## Architecture

```
/app/
├── backend/
│   ├── server.py           # Main FastAPI app
│   ├── routes/
│   │   ├── auth.py         # Authentication
│   │   ├── categories.py   # Category CRUD
│   │   ├── search.py       # Search endpoints
│   │   ├── social.py       # Friends, Groups, Pages, Posts (ENHANCED)
│   │   ├── messages.py     # Direct Messaging + Push Notifications (ENHANCED)
│   │   ├── polls.py        # Polls CRUD (NEW)
│   │   ├── marketplace.py  # Protocol marketplace
│   │   ├── bundles.py      # Protocol bundles
│   │   ├── chat.py         # Real-time group chat
│   │   ├── newsletter.py   # AI Newsletter system (NEW)
│   │   ├── voice.py        # Voice Search (NEW)
│   │   ├── collaborate.py  # Collaborative Editing (NEW)
│   │   ├── statistics.py   # Statistics dashboard
│   │   ├── gamification.py # Achievements system
│   │   ├── push_notifications.py  # Web push
│   │   └── notifications.py # WebSocket notifications
│   └── services/
│       ├── ai_service.py      # GPT-5.2 for newsletters (NEW)
│       ├── voice_service.py   # Whisper transcription (NEW)
│       ├── location_service.py # Geo-extraction (NEW)
│       ├── auth_service.py    # Authentication + Default Friend (ENHANCED)
│       ├── gamification_service.py # Achievement logic
│       └── protocol_service.py # Protocol parsing
└── frontend/
    └── src/
        ├── pages/
        │   ├── SocialPage.js       # Social Hub with tabs + Polls (ENHANCED)
        │   ├── MessagesPage.js     # Direct Messages (ENHANCED)
        │   ├── UltimateSearchPage.js # Search with map
        │   ├── MarketplacePage.js  # Protocol marketplace
        │   ├── StatisticsPage.js   # Statistics dashboard
        │   ├── AchievementsPage.js # Gamification
        │   └── ChatPage.js         # Group chat
        ├── components/
        │   ├── shared/
        │   │   ├── PollCard.js     # Poll display + voting (NEW)
        │   │   └── VoiceSearchButton.js # Voice input (NEW)
        │   └── AdvancedAnalytics.js  # Recharts dashboard
        └── i18n.js                 # Multi-language support
```

## API Endpoints

### Marketplace (ENHANCED January 15, 2026)
- `GET /api/marketplace/protocols` - List marketplace protocols
- `GET /api/marketplace/protocols/{id}` - Get protocol details
- `POST /api/marketplace/protocols` - List a new protocol for sale
- `POST /api/marketplace/initiate-purchase` - Start Pay-What-You-Want purchase
- `POST /api/marketplace/confirm-payment` - Confirm PayPal payment with revenue split
- `GET /api/marketplace/purchases` - Get user's purchased protocols
- `GET /api/marketplace/categories` - Get marketplace categories with counts
- `GET /api/marketplace/admin/revenue-settings` - Get revenue split (admin)
- `PUT /api/marketplace/admin/revenue-settings` - Set platform fee 5-30% (admin)
- `GET /api/marketplace/admin/payouts` - Get pending payouts (admin)
- `POST /api/marketplace/admin/process-payout` - Mark payout processed (admin)
- `GET /api/marketplace/my-earnings` - Get user's accumulated earnings
- `PUT /api/marketplace/my-paypal-email` - Update PayPal email for payouts
- `GET /api/marketplace/map-data` - Get protocol locations for map
- `GET /api/marketplace/seller/dashboard` - Get seller stats
- `GET /api/marketplace/paypal-config` - Get PayPal client config

### Chat (NEW)
- `GET /api/chat/rooms` - Get user's chat rooms
- `POST /api/chat/rooms` - Create new room
- `GET /api/chat/rooms/{id}/messages` - Get room messages
- `GET /api/chat/online` - Get online users
- `WS /api/chat/ws/{room_id}` - WebSocket for real-time chat

### Protocol Bundles (NEW)
- `GET /api/bundles` - List all bundles
- `POST /api/bundles` - Create bundle
- `GET /api/bundles/{id}` - Get bundle details
- `POST /api/bundles/{id}/purchase` - Purchase bundle

### Push Notifications (NEW)
- `GET /api/push/vapid-key` - Get VAPID public key
- `POST /api/push/subscribe` - Subscribe to notifications
- `DELETE /api/push/unsubscribe` - Unsubscribe
- `POST /api/push/send` - Send notification (admin)
- `GET /api/push/stats` - Get push stats (admin)

## Testing Results (Iteration 20 - January 15, 2026)
- **Backend: 23/23 tests passed (100%)**
- **Frontend: All UI features working (100%)**
- Test report: `/app/test_reports/iteration_20.json`

### Major Features Implemented (January 15, 2026):

#### 1. Social Features
- Friends system with search, add, accept, reject
- Groups with create, join, leave, member management
- Pages with create, follow, unfollow
- Social Feed with personalized content
- Posts with photo uploads (up to 6.9MB)
- 6 reaction types (like, love, haha, wow, sad, angry)

#### 2. Direct Messaging
- Private 1-on-1 conversations
- Real-time WebSocket updates
- Image sharing in messages
- Read receipts and typing indicators
- Online status tracking

#### 3. AI Newsletter System (GPT-5.2)
- AI-generated "extremely funny" marketing content
- Newsletter draft management
- Subscriber management
- Campaign history and analytics
- Test email before broadcast

#### 4. Voice Search (OpenAI Whisper)
- Browser audio recording
- Speech-to-text transcription
- Voice search history
- Admin voice analytics

#### 5. Collaborative Protocol Editing
- Real-time multi-user editing
- User cursors with colors
- Version history with restore
- Protocol comments with resolve

#### 6. Location Auto-Detection
- Automatic geo-extraction from content
- 50 US states coordinate database
- 20+ major US cities
- World country coverage
- Auto-populate map with results

### Category Filtering Bug Fix (Iteration 19):
- Category checkboxes now filter results correctly
- AND/OR logic integrated
- Map updates with filtered results

### Previous Features (Iteration 18):
- 22 achievements across 6 categories
- 10 level system with points
- Weekly & All-Time leaderboards
- Shareable badges

## Preview URL
https://infopilot-network.preview.emergentagent.com

## Third-Party Integrations
- **OpenAI GPT-5.2** - Newsletter generation (via Emergent LLM Key)
- **OpenAI Whisper** - Voice transcription (via Emergent LLM Key)
- **SerpAPI** - Web search
- **ddgs** - DuckDuckGo fallback
- **Emergent Google Auth** - OAuth
- **PayPal** - Marketplace payments
- **Resend** - Newsletter emails
- **Recharts** - Analytics charts
- **Leaflet** - Map integration
- **i18next** - Multi-language
- **pywebpush** - Push notifications

## New API Endpoints (January 15, 2026)

### Social APIs
- `GET /api/friends` - Get friends list
- `GET /api/friends/requests` - Get pending requests
- `POST /api/friends/request/{id}` - Send friend request
- `POST /api/friends/accept/{id}` - Accept request
- `POST /api/friends/reject/{id}` - Reject request
- `DELETE /api/friends/{id}` - Remove friend
- `GET /api/friends/search` - Search users
- `GET /api/groups` - List groups
- `POST /api/groups` - Create group
- `GET /api/groups/{id}` - Get group details
- `POST /api/groups/{id}/join` - Join group
- `POST /api/groups/{id}/leave` - Leave group
- `GET /api/pages` - List pages
- `POST /api/pages` - Create page
- `GET /api/pages/{id}` - Get page details
- `POST /api/pages/{id}/follow` - Follow page
- `POST /api/pages/{id}/unfollow` - Unfollow page
- `GET /api/feed` - Get personalized feed
- `GET /api/posts` - Get posts
- `POST /api/posts` - Create post
- `POST /api/posts/with-photos` - Create post with photos
- `POST /api/posts/{id}/react` - Add reaction
- `DELETE /api/posts/{id}/react` - Remove reaction

### Direct Messaging APIs
- `GET /api/dm/conversations` - Get conversations
- `POST /api/dm/conversations/{id}` - Create/get conversation
- `GET /api/dm/conversations/{id}/messages` - Get messages
- `POST /api/dm/conversations/{id}/messages` - Send message
- `POST /api/dm/conversations/{id}/typing` - Typing indicator
- `POST /api/dm/conversations/{id}/read` - Mark as read
- `WS /api/dm/ws` - WebSocket for real-time DM

### Newsletter APIs
- `GET /api/newsletter/subscribers` - Get subscribers (admin)
- `POST /api/newsletter/subscribe` - Subscribe
- `POST /api/newsletter/unsubscribe` - Unsubscribe
- `POST /api/newsletter/generate` - Generate AI content (admin)
- `GET /api/newsletter/drafts` - Get drafts (admin)
- `POST /api/newsletter/send/{id}` - Send newsletter (admin)
- `GET /api/newsletter/campaigns` - Campaign history (admin)

### Voice Search APIs
- `POST /api/voice/transcribe` - Transcribe audio
- `POST /api/voice/search` - Voice search
- `GET /api/voice/history` - Get voice history
- `GET /api/voice/stats` - Admin voice stats

### Collaborative Editing APIs
- `POST /api/protocols/{id}/collaborate/start` - Start session
- `POST /api/protocols/{id}/collaborate/save` - Save changes
- `GET /api/protocols/{id}/collaborate/history` - Get history
- `POST /api/protocols/{id}/collaborate/restore/{id}` - Restore version
- `WS /api/protocols/{id}/collaborate/ws` - Real-time collaboration

### Polls APIs (NEW - January 15, 2026)
- `POST /api/polls?parent_type={type}&parent_id={id}` - Create poll
- `GET /api/polls/{poll_id}` - Get single poll
- `GET /api/polls/parent/{type}/{id}` - Get polls for group/page/USP
- `POST /api/polls/{poll_id}/vote` - Vote on poll
- `DELETE /api/polls/{poll_id}/vote` - Remove vote
- `DELETE /api/polls/{poll_id}` - Delete poll
- `PUT /api/polls/{poll_id}/close` - Close poll early

## Prioritized Backlog

### P1 (High Priority) - COMPLETED ✅
- [x] Social Features (Friends, Groups, Pages with reactions)
- [x] Direct Messaging with WebSockets
- [x] Voice search integration (OpenAI Whisper)
- [x] Collaborative protocol editing
- [x] AI Newsletter system (GPT-5.2)
- [x] Location auto-detection
- [x] Polls Feature for Groups, Pages, USP
- [x] Default Admin Friend for new users
- [x] Push Notifications for DMs

### P1 (Remaining)
- [ ] Mobile app wrapper (Capacitor) - Configuration ready
- [ ] Browser extension (Chrome)

### P2 (Medium Priority)
- [ ] Video tutorials
- [ ] API rate limiting dashboard
- [ ] Webhook integrations
- [ ] Direct Messaging with WebSockets

### P3 (Low Priority)
- [ ] Browser extension
- [ ] Slack/Discord integration
- [ ] AI-generated Email Newsletters
