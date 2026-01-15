# Mobile App Build Guide

## InfoPilot Explorer - Capacitor Mobile App

This comprehensive guide covers building the InfoPilot Explorer mobile app for Android and iOS.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Android Build](#android-build)
4. [iOS Build](#ios-build)
5. [Testing](#testing)
6. [Publishing](#publishing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### For All Platforms
- Node.js 18+ and npm/yarn
- Git
- InfoPilot Explorer frontend source code

### For Android
- **Java JDK 17** (required by Android Gradle)
- **Android Studio** (latest version)
- **Android SDK** (API level 33+)
- **Gradle 8.0+**

### For iOS (macOS only)
- **macOS 13+** (Ventura or later)
- **Xcode 15+**
- **CocoaPods** (`sudo gem install cocoapods`)
- **Apple Developer Account** ($99/year for distribution)

---

## Environment Setup

### Step 1: Clone and Install Dependencies

```bash
cd /app/frontend
yarn install
```

### Step 2: Install Capacitor CLI (if not already installed)

```bash
yarn add @capacitor/core @capacitor/cli
yarn add @capacitor/android @capacitor/ios
```

### Step 3: Initialize Capacitor (already done)

The project already has `capacitor.config.json`:

```json
{
  "appId": "com.infopilot.explorer",
  "appName": "InfoPilot Explorer",
  "webDir": "build",
  "server": {
    "androidScheme": "https"
  }
}
```

---

## Android Build

### Step 1: Set Up Android Studio

1. Download Android Studio: https://developer.android.com/studio
2. Install and open Android Studio
3. Go to **SDK Manager** (Tools > SDK Manager)
4. Install:
   - Android SDK Platform 33 (Android 13)
   - Android SDK Build-Tools 33.0.0
   - Android Emulator
   - Android SDK Platform-Tools

### Step 2: Set Environment Variables

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
```

Then reload: `source ~/.bashrc`

### Step 3: Build the Web App

```bash
cd /app/frontend
yarn build
```

### Step 4: Add Android Platform

```bash
npx cap add android
```

### Step 5: Sync Web Assets

```bash
npx cap sync android
```

### Step 6: Open in Android Studio

```bash
npx cap open android
```

### Step 7: Build APK (Debug)

In Android Studio:
1. Go to **Build > Build Bundle(s) / APK(s) > Build APK(s)**
2. Wait for build to complete
3. Find APK at: `android/app/build/outputs/apk/debug/app-debug.apk`

### Step 8: Build APK (Release)

#### Generate Signing Key (one-time)

```bash
keytool -genkey -v -keystore infopilot-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias infopilot
```

Save the keystore file securely!

#### Configure Signing

Create `android/app/signing.properties`:
```properties
storeFile=../infopilot-release-key.jks
storePassword=YOUR_STORE_PASSWORD
keyAlias=infopilot
keyPassword=YOUR_KEY_PASSWORD
```

#### Build Signed APK

In Android Studio:
1. Go to **Build > Generate Signed Bundle / APK**
2. Select **APK**
3. Choose your keystore
4. Select **release** build variant
5. Click **Create**

Output: `android/app/build/outputs/apk/release/app-release.apk`

### Step 9: Build App Bundle (for Play Store)

```bash
cd android
./gradlew bundleRelease
```

Output: `android/app/build/outputs/bundle/release/app-release.aab`

---

## iOS Build

### Prerequisites Check

```bash
# Verify Xcode installation
xcode-select -p

# Install CocoaPods
sudo gem install cocoapods
```

### Step 1: Build Web App

```bash
cd /app/frontend
yarn build
```

### Step 2: Add iOS Platform

```bash
npx cap add ios
```

### Step 3: Sync and Install Pods

```bash
npx cap sync ios
cd ios/App
pod install
cd ../..
```

### Step 4: Open in Xcode

```bash
npx cap open ios
```

### Step 5: Configure Signing

In Xcode:
1. Select the **App** project in navigator
2. Select **App** target
3. Go to **Signing & Capabilities** tab
4. Select your **Team** (Apple Developer account)
5. Set **Bundle Identifier**: `com.infopilot.explorer`

### Step 6: Build for Simulator

1. Select a simulator (e.g., iPhone 15)
2. Press **Cmd + R** or click **Play** button

### Step 7: Build for Device

1. Connect your iPhone via USB
2. Select your device in the scheme
3. Press **Cmd + R**
4. Trust the developer on your iPhone (Settings > General > Device Management)

### Step 8: Archive for App Store

1. Select **Any iOS Device** as destination
2. Go to **Product > Archive**
3. In Organizer, click **Distribute App**
4. Choose **App Store Connect**
5. Follow the upload wizard

---

## Testing

### Android Testing

```bash
# List available emulators
emulator -list-avds

# Start emulator
emulator -avd Pixel_6_API_33

# Install APK on emulator
adb install android/app/build/outputs/apk/debug/app-debug.apk

# View logs
adb logcat | grep -i infopilot
```

### iOS Testing

```bash
# List available simulators
xcrun simctl list devices

# Boot simulator
xcrun simctl boot "iPhone 15"

# Open Simulator app
open -a Simulator
```

---

## Publishing

### Google Play Store

1. Go to https://play.google.com/console
2. Create new app
3. Fill in store listing:
   - App name: InfoPilot Explorer
   - Short description (80 chars)
   - Full description (4000 chars)
   - Screenshots (phone, tablet)
   - Feature graphic (1024x500)
   - App icon (512x512)
4. Upload AAB file
5. Set up pricing (free)
6. Complete content rating questionnaire
7. Submit for review

### Apple App Store

1. Go to https://appstoreconnect.apple.com
2. Create new app
3. Fill in App Information:
   - Name: InfoPilot Explorer
   - Subtitle
   - Description
   - Keywords
   - Screenshots (6.7", 6.5", 5.5")
   - App Preview videos (optional)
4. Upload build via Xcode
5. Submit for review

---

## Using the Build Script

The project includes an interactive build script:

```bash
cd /app/frontend
chmod +x scripts/build-mobile.sh
./scripts/build-mobile.sh
```

Options:
1. Build Web App
2. Sync to Android
3. Sync to iOS
4. Build Android Debug APK
5. Build Android Release Bundle
6. Open Android Studio
7. Open Xcode
8. Full Android Build
9. Full iOS Build

---

## Troubleshooting

### Common Android Issues

| Issue | Solution |
|-------|----------|
| "SDK location not found" | Set ANDROID_HOME environment variable |
| Gradle build fails | Update Gradle version in `android/gradle/wrapper/gradle-wrapper.properties` |
| "JAVA_HOME not set" | Install JDK 17 and set JAVA_HOME |
| APK too large | Enable ProGuard in `android/app/build.gradle` |

### Common iOS Issues

| Issue | Solution |
|-------|----------|
| "No signing certificate" | Add Apple Developer account in Xcode |
| Pod install fails | Run `pod repo update` then `pod install` |
| Build fails on M1/M2 | Run `arch -x86_64 pod install` |
| "App not trusted" | Go to Settings > General > Device Management on iPhone |

### Capacitor Issues

| Issue | Solution |
|-------|----------|
| Changes not showing | Run `npx cap sync` after `yarn build` |
| Plugins not working | Check `capacitor.config.json` and reinstall plugins |
| White screen | Check browser console in remote debugging |

---

## App Store Assets Checklist

### Android (Google Play)
- [ ] App icon (512x512 PNG)
- [ ] Feature graphic (1024x500 PNG)
- [ ] Screenshots (phone): 2-8 images
- [ ] Screenshots (tablet): 2-8 images (optional)
- [ ] Short description (80 chars)
- [ ] Full description (4000 chars)
- [ ] Privacy policy URL

### iOS (App Store)
- [ ] App icon (1024x1024 PNG, no alpha)
- [ ] Screenshots 6.7" (1290x2796)
- [ ] Screenshots 6.5" (1284x2778)
- [ ] Screenshots 5.5" (1242x2208)
- [ ] iPad screenshots (optional)
- [ ] Description (4000 chars)
- [ ] Keywords (100 chars)
- [ ] Privacy policy URL
- [ ] Support URL

---

## Version Management

Update version in these files before each release:
1. `package.json` - `version` field
2. `capacitor.config.json` - if needed
3. `android/app/build.gradle` - `versionCode` and `versionName`
4. `ios/App/App/Info.plist` - `CFBundleShortVersionString` and `CFBundleVersion`

---

*Last Updated: January 15, 2026*
