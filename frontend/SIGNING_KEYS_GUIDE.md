# InfoPilot Explorer - Signing Key Generation Guide

## Android Keystore Generation

### Generate Release Keystore
```bash
cd frontend

# Generate keystore (you'll be prompted for passwords)
keytool -genkey -v \
  -keystore android/release-key.keystore \
  -alias infopilot \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000
```

### Keystore Information to Record
After generation, save these details securely:
- **Keystore file**: `android/release-key.keystore`
- **Keystore password**: [your password]
- **Key alias**: `infopilot`
- **Key password**: [your password]

### Update capacitor.config.json
The config already has placeholders - update with your passwords:
```json
{
  "android": {
    "buildOptions": {
      "keystorePath": "release-key.keystore",
      "keystorePassword": "YOUR_KEYSTORE_PASSWORD",
      "keystoreAlias": "infopilot",
      "keystoreAliasPassword": "YOUR_KEY_PASSWORD"
    }
  }
}
```

## iOS Signing (macOS Required)

### Prerequisites
1. Apple Developer Account ($99/year)
2. Xcode installed
3. Valid provisioning profiles

### Steps
1. Open project in Xcode: `npx cap open ios`
2. Select your Team in Signing & Capabilities
3. Create App ID in Apple Developer Portal
4. Generate provisioning profiles
5. Archive and upload to App Store Connect

## Google Play Store Submission

### Prerequisites
- Google Play Developer Account ($25 one-time)
- Release AAB file
- App screenshots (phone + tablet)
- Privacy policy URL
- App icon (512x512 PNG)

### Submission Steps
1. Build release: `./scripts/build-mobile.sh` → Option 3
2. Go to [Google Play Console](https://play.google.com/console)
3. Create new app
4. Fill in store listing
5. Upload `dist/infopilot-explorer-release.aab`
6. Complete content rating questionnaire
7. Set up pricing & distribution
8. Submit for review

### Recommended Store Listing

**App Name**: InfoPilot Explorer - Information Exchange Network

**Short Description** (80 chars):
Search smarter with custom protocols. Buy, sell & share search algorithms.

**Full Description**:
🔍 **InfoPilot Explorer** - The Ultimate Information Exchange Network

Transform how you search the web with custom search protocols powered by InfoJet 2.0™!

**KEY FEATURES:**
✨ Ultimate Search - Create powerful search protocols with advanced operators
💰 Protocol Marketplace - Buy and sell search algorithms (earn 90% of sales!)
👥 Social Hub - Connect with researchers, join groups, create pages
🎤 Voice Search - AI-powered hands-free searching
🏆 Gamification - Earn points, unlock achievements, climb leaderboards
💬 Real-time Messaging - Chat with your network instantly
🗺️ Interactive Maps - Visualize search results geographically

**INFOPILOT EXPLORER HELPS YOU:**
• Find information faster with custom protocols
• Monetize your search expertise
• Build a community of researchers
• Track statistics and trends
• Access anywhere with our browser extension

Join thousands of information professionals using InfoPilot Explorer!

**Category**: Productivity
**Content Rating**: Everyone

## Apple App Store Submission

### Prerequisites
- Apple Developer Account ($99/year)
- Xcode on macOS
- App screenshots (6.5" and 5.5" displays)
- Privacy policy URL

### Submission Steps
1. Build in Xcode: Product → Archive
2. Upload to App Store Connect
3. Fill in app information
4. Submit for review

### Recommended App Store Listing

**App Name**: InfoPilot Explorer

**Subtitle**: Search Protocols & Marketplace

**Promotional Text**:
Create custom search protocols, trade algorithms, and connect with researchers worldwide!

**Keywords**:
search,protocol,marketplace,research,information,discovery,AI,voice,social,network

**Category**: Productivity
**Secondary Category**: Social Networking
