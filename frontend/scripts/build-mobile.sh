#!/bin/bash
# InfoPilot Explorer - Capacitor Build Script
# This script prepares and builds the mobile app for Android and iOS

set -e

echo "🚀 InfoPilot Explorer - Mobile Build Script"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Run this script from the frontend directory${NC}"
    exit 1
fi

# Function to check prerequisites
check_prerequisites() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Node.js is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Node.js $(node -v)${NC}"
    
    # Check npm/yarn
    if command -v yarn &> /dev/null; then
        echo -e "${GREEN}✓ Yarn $(yarn -v)${NC}"
        PKG_MANAGER="yarn"
    elif command -v npm &> /dev/null; then
        echo -e "${GREEN}✓ npm $(npm -v)${NC}"
        PKG_MANAGER="npm"
    else
        echo -e "${RED}Neither yarn nor npm found${NC}"
        exit 1
    fi
    
    # Check for Android SDK (optional)
    if [ -n "$ANDROID_HOME" ]; then
        echo -e "${GREEN}✓ Android SDK found at $ANDROID_HOME${NC}"
    else
        echo -e "${YELLOW}⚠ ANDROID_HOME not set - Android builds may fail${NC}"
    fi
    
    # Check for Xcode (macOS only)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v xcodebuild &> /dev/null; then
            echo -e "${GREEN}✓ Xcode $(xcodebuild -version | head -1)${NC}"
        else
            echo -e "${YELLOW}⚠ Xcode not found - iOS builds will fail${NC}"
        fi
    fi
}

# Function to build web app
build_web() {
    echo -e "\n${YELLOW}Building web app...${NC}"
    
    if [ "$PKG_MANAGER" == "yarn" ]; then
        yarn build
    else
        npm run build
    fi
    
    echo -e "${GREEN}✓ Web build complete${NC}"
}

# Function to sync Capacitor
sync_capacitor() {
    echo -e "\n${YELLOW}Syncing Capacitor...${NC}"
    npx cap sync
    echo -e "${GREEN}✓ Capacitor sync complete${NC}"
}

# Function to build Android
build_android() {
    echo -e "\n${YELLOW}Building Android APK...${NC}"
    
    # Add Android platform if not exists
    if [ ! -d "android" ]; then
        echo "Adding Android platform..."
        npx cap add android
    fi
    
    # Sync
    npx cap sync android
    
    # Build debug APK
    cd android
    ./gradlew assembleDebug
    
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
    if [ -f "$APK_PATH" ]; then
        echo -e "${GREEN}✓ Debug APK built: android/$APK_PATH${NC}"
        
        # Copy to dist folder
        mkdir -p ../dist
        cp "$APK_PATH" ../dist/infopilot-explorer-debug.apk
        echo -e "${GREEN}✓ APK copied to dist/infopilot-explorer-debug.apk${NC}"
    fi
    
    cd ..
}

# Function to build Android release
build_android_release() {
    echo -e "\n${YELLOW}Building Android Release Bundle...${NC}"
    
    if [ ! -f "android/release-key.keystore" ]; then
        echo -e "${RED}Error: Keystore not found. Generate one first:${NC}"
        echo "keytool -genkey -v -keystore android/release-key.keystore -alias infopilot -keyalg RSA -keysize 2048 -validity 10000"
        exit 1
    fi
    
    cd android
    ./gradlew bundleRelease
    
    AAB_PATH="app/build/outputs/bundle/release/app-release.aab"
    if [ -f "$AAB_PATH" ]; then
        echo -e "${GREEN}✓ Release bundle built: android/$AAB_PATH${NC}"
        
        mkdir -p ../dist
        cp "$AAB_PATH" ../dist/infopilot-explorer-release.aab
        echo -e "${GREEN}✓ Bundle copied to dist/infopilot-explorer-release.aab${NC}"
    fi
    
    cd ..
}

# Function to build iOS
build_ios() {
    echo -e "\n${YELLOW}Building iOS...${NC}"
    
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo -e "${RED}iOS builds require macOS${NC}"
        return
    fi
    
    # Add iOS platform if not exists
    if [ ! -d "ios" ]; then
        echo "Adding iOS platform..."
        npx cap add ios
    fi
    
    # Sync
    npx cap sync ios
    
    echo -e "${GREEN}✓ iOS project ready${NC}"
    echo -e "${YELLOW}To build IPA, open Xcode:${NC}"
    echo "npx cap open ios"
    echo "Then: Product > Archive"
}

# Function to open in IDE
open_android() {
    echo -e "\n${YELLOW}Opening Android Studio...${NC}"
    npx cap open android
}

open_ios() {
    echo -e "\n${YELLOW}Opening Xcode...${NC}"
    npx cap open ios
}

# Main menu
show_menu() {
    echo -e "\n${YELLOW}Select build option:${NC}"
    echo "1) Build web app only"
    echo "2) Build Android debug APK"
    echo "3) Build Android release bundle (Play Store)"
    echo "4) Build iOS (requires macOS)"
    echo "5) Full build (web + Android + iOS)"
    echo "6) Open Android Studio"
    echo "7) Open Xcode"
    echo "8) Check prerequisites"
    echo "0) Exit"
    echo ""
    read -p "Enter choice: " choice
    
    case $choice in
        1) build_web ;;
        2) build_web && sync_capacitor && build_android ;;
        3) build_web && sync_capacitor && build_android_release ;;
        4) build_web && sync_capacitor && build_ios ;;
        5) build_web && sync_capacitor && build_android && build_ios ;;
        6) open_android ;;
        7) open_ios ;;
        8) check_prerequisites ;;
        0) exit 0 ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
}

# Run
check_prerequisites
show_menu
