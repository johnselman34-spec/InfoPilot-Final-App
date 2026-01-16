# InfoPilot Explorer - Changelog

## January 16, 2026 - Batch 11 (Easter Eggs & Legal)

### New Features
- **Floating Easter Eggs Gamification**
  - FloatingEasterEggs.js - Colorful eggs float across screen
  - 6 reward types: Protocol Ideas (25 XP), Jokes (15 XP), Pricing Tips (20 XP), Motivation (10 XP), Fun Facts (15 XP), Secrets (30 XP)
  - EasterEggStats component in Settings page
  - Eggs spawn every 45 seconds from screen edges
  - Reward popup with XP earned and copy button for protocols

- **Protocol Parser Enhancement**
  - "and" now works as synonym for "&" (case-insensitive)
  - Example: (word1 or word2) and (word3 or word4) = (word1 or word2) & (word3 or word4)

- **Legal Components**
  - UserAgreement.js - Professional ToS for Top Pilot Enterprises, Inc.
  - PrivacyStatement.js - GDPR/CCPA compliant privacy policy
  - Accessible from Registration and Settings pages

### Files Changed
- `/app/frontend/src/components/Gamification/FloatingEasterEggs.js` (NEW)
- `/app/frontend/src/components/Legal/UserAgreement.js` (NEW)
- `/app/frontend/src/components/Legal/PrivacyStatement.js` (NEW)
- `/app/frontend/src/components/Legal/index.js` (NEW)
- `/app/frontend/src/App.js` (Added FloatingEasterEggsController)
- `/app/frontend/src/pages/SettingsPage.js` (Added EasterEggStats, Legal components)
- `/app/frontend/src/pages/RegisterPage.js` (Updated to use Legal components)

### Testing
- 14/14 backend tests passed (iteration_56)
- Frontend UI verified via Playwright

---

## January 16, 2026 - Batch 10 (Advanced Features & Testing Tools)

### New Features
- Bulk Document Type Testing Tool
- Map Export Features (JSON, GeoJSON, KML, CSV)
- PayPal Wallet Accumulation
- 15+ New Gamification Badges
- Personal Report Creator UI

---

## January 16, 2026 - Batch 9 (Admin Panel UI & Refactoring)

### New Features
- Admin Panel UI for Price Controls (PriceControlsAdmin.js)
- Admin Panel UI for Document Type Settings (DoctypeSettingsAdmin.js)
- MarketplacePage Refactoring (ProtocolCard.js, SellForm.js, SellerDashboard.js)
- Quick Category Search Filter

---

## January 16, 2026 - Batch 8 (Price Controls & Document Classification)

### New Features
- Admin Price Controls for Unpaid Users
- Global Price Controls for ALL Users
- Personal Report (Organic) Feature
- Document Type Auto-Categorization with Admin Protocols

---

## January 16, 2026 - Batch 7 (UI Enhancements & Admin Controls)

### New Features
- CollapsibleCategoryTree Component
- Map Filtering by User
- Newsletter Schedule Update (5:46 AM, 9:42 AM, 4:20 PM UTC)
- Enhanced Auto-Collate for AI Search
- Default Collation Limit changed to 40

---

## January 16, 2026 - Batch 6 (Laugh-O-Meter & Enhanced Promos)

### New Features
- Laugh-O-Meter Gamification System
- Enhanced Letters to Evelyn Promos
- Cross-Sell UI Component

---

## January 15-16, 2026 - Batches 1-5

### Major Features
- Copy to Clipboard
- Capacitor Mobile App Wrapper
- Chrome Browser Extension
- Partial Admin Roles
- Most Copied Protocols Leaderboard
- Video Tutorials System
- Rate Limiting Dashboard
- Webhook Integrations
- Protocol Bundles UI
- Tri-Weekly AI Newsletter Scheduler
- Map Auto-Update Feature
- FREE Protocols Badge
- Bundle of the Week
- Cross-Sell Recommendations
- Category Result Counts
- Admin Collation Settings
- Admin Payment Settings
- Category Hierarchy Fixes
- 100+ Funny Content Library
