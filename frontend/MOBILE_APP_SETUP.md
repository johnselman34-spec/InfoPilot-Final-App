# InfoPilot Explorer - Mobile App Setup Guide

## Prerequisites
- Node.js 20+ installed locally
- Android Studio (for Android builds)
- Xcode (for iOS builds, Mac only)
- Capacitor CLI installed

## Initial Setup

### 1. Build the Web App
```bash
cd frontend
yarn build
```

### 2. Initialize Capacitor
```bash
npx cap init "InfoPilot Explorer" "com.infopilot.explorer"
```

### 3. Add Platforms
```bash
# Android
npx cap add android

# iOS (Mac only)
npx cap add ios
```

### 4. Sync and Build
```bash
# Sync web assets to native projects
npx cap sync

# Open in Android Studio
npx cap open android

# Open in Xcode (Mac only)
npx cap open ios
```

## App Store Configurations

### Google Play Store
- **Package Name:** com.infopilot.explorer
- **Category:** Productivity / Tools
- **Target SDK:** API 34 (Android 14)
- **Keywords:** InfoPilot, search engine, protocol, marketplace, social network

### Apple App Store
- **Bundle ID:** com.infopilot.explorer
- **Category:** Productivity
- **Target:** iOS 14.0+

## ASO Keywords (20 Keywords)
1. InfoPilot
2. Search Engine
3. Protocol Marketplace
4. Search Protocols
5. InfoJet
6. Custom Search
7. AI Search
8. Social Search
9. Search Community
10. Protocol Trading
11. Search Optimization
12. Advanced Search
13. Search Groups
14. Search Network
15. Multi-Engine Search
16. Search Builder
17. Protocol Creator
18. Search Tools
19. Information Discovery
20. Smart Search

## Build Commands

### Debug Builds
```bash
# Android
npx cap run android

# iOS
npx cap run ios
```

### Release Builds
```bash
# Android APK
cd android && ./gradlew assembleRelease

# Android Bundle (for Play Store)
cd android && ./gradlew bundleRelease

# iOS (use Xcode Archive)
```

## Push Notification Setup

### Firebase Cloud Messaging (Android)
1. Create Firebase project
2. Download google-services.json
3. Place in android/app/

### APNs (iOS)
1. Create APNs certificate in Apple Developer
2. Configure in Xcode

## Icon Assets Needed
- android/app/src/main/res/mipmap-hdpi/ic_launcher.png (72x72)
- android/app/src/main/res/mipmap-mdpi/ic_launcher.png (48x48)
- android/app/src/main/res/mipmap-xhdpi/ic_launcher.png (96x96)
- android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png (144x144)
- android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png (192x192)
- ios/App/App/Assets.xcassets/AppIcon.appiconset/ (various sizes)

## Splash Screen
- android/app/src/main/res/drawable/splash.png
- ios/App/App/Assets.xcassets/Splash.imageset/

## Testing
```bash
# Run on connected device
npx cap run android --target=DEVICE_ID
npx cap run ios --target=DEVICE_NAME

# List available devices
npx cap run android --list
npx cap run ios --list
```
