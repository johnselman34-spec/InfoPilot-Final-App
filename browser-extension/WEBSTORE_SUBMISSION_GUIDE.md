# Chrome Extension Web Store Submission Guide

## InfoPilot Explorer - InfoJet Browser Extension

This guide walks you through submitting the InfoJet Chrome extension to the Chrome Web Store.

---

## Prerequisites

1. **Google Developer Account** ($5 one-time fee)
   - Go to: https://chrome.google.com/webstore/devconsole/
   - Sign in with your Google account
   - Pay the $5 registration fee

2. **Extension ZIP File**
   - Location: `/app/browser-extension/dist/infopilot-infojet-extension.zip`
   - Size: ~12KB

---

## Step-by-Step Submission Process

### Step 1: Access the Developer Dashboard

1. Go to https://chrome.google.com/webstore/devconsole/
2. Click **"New Item"** button in the top right

### Step 2: Upload Your Extension

1. Click **"Browse"** or drag-and-drop the ZIP file
2. Upload: `infopilot-infojet-extension.zip`
3. Wait for upload to complete (usually a few seconds)

### Step 3: Fill in Store Listing

#### Basic Information
```
Name: InfoJet - InfoPilot Search Extension
Short Description (132 chars max):
Search the web using custom InfoPilot protocols. Quick access to your categories and results from any webpage.

Detailed Description:
InfoJet is the official browser extension for InfoPilot Explorer - your ultimate search companion.

🔍 FEATURES:
• Quick Search: Access InfoPilot search from any webpage
• Protocol Access: Use your custom search protocols instantly
• Context Menu: Right-click selected text to search
• Keyboard Shortcuts: Press Ctrl+Shift+S to open search
• Sync: All your categories and protocols synced

🚀 HOW TO USE:
1. Click the InfoJet icon in your browser toolbar
2. Enter your search query or select a saved protocol
3. View results instantly or open in InfoPilot

💡 TIPS:
• Select text on any page, right-click, and choose "Search with InfoJet"
• Pin the extension for quick access
• Log in to sync your protocols across devices

📱 PART OF THE INFOPILOT ECOSYSTEM:
InfoPilot Explorer offers advanced search capabilities with custom protocols, 
AI-powered suggestions, and a marketplace for search strategies.

🔐 PRIVACY:
• We only access the current tab URL when you initiate a search
• No browsing data is collected or stored
• Your protocols are encrypted in transit

Visit https://infoshare-4.preview.emergentagent.com for the full experience!
```

#### Category
- Select: **"Productivity"** or **"Search Tools"**

#### Language
- Primary: **English**

### Step 4: Upload Graphics

#### Store Icon (128x128 PNG)
- Use: `/app/browser-extension/icons/icon128.png`

#### Screenshots (1280x800 or 640x400)
Create screenshots showing:
1. Extension popup with search interface
2. Context menu integration
3. Results preview

#### Promotional Images (Optional but Recommended)
- Small Tile: 440x280 PNG
- Large Tile: 920x680 PNG
- Marquee: 1400x560 PNG

### Step 5: Privacy Practices

#### Single Purpose Description
```
This extension provides quick access to InfoPilot Explorer search functionality, 
allowing users to search using custom protocols from any webpage.
```

#### Permissions Justification
| Permission | Justification |
|------------|---------------|
| `activeTab` | Required to get the current page URL for contextual searches |
| `storage` | Stores user preferences and cached protocol data locally |
| `contextMenus` | Enables right-click "Search with InfoJet" functionality |

#### Data Usage Declaration
- [ ] Does NOT sell user data
- [ ] Does NOT use data for purposes unrelated to the extension
- [ ] Does NOT use data for creditworthiness or lending

### Step 6: Distribution

#### Visibility
- Select: **"Public"** (visible to everyone)

#### Countries
- Select: **"All regions"** or specific countries

### Step 7: Review and Submit

1. Click **"Preview"** to see how your listing will appear
2. Review all information for accuracy
3. Click **"Submit for Review"**

---

## Post-Submission

### Review Timeline
- Initial review: 1-3 business days
- May take longer if issues are found

### Common Rejection Reasons & Fixes

| Reason | Fix |
|--------|-----|
| Missing privacy policy | Add privacy policy URL |
| Unclear purpose | Improve description |
| Excessive permissions | Remove unnecessary permissions |
| Broken functionality | Test thoroughly before resubmission |

### After Approval

1. Your extension will be live on the Chrome Web Store
2. Share the store URL with users
3. Monitor reviews and ratings
4. Update regularly with new features

---

## Updating the Extension

1. Increment version in `manifest.json`
2. Run packaging script: `./package-extension.sh`
3. Go to Developer Dashboard
4. Click on your extension
5. Click "Package" tab
6. Upload new ZIP file
7. Submit for review

---

## Support Links

- Chrome Web Store Help: https://support.google.com/chrome_webstore
- Developer Documentation: https://developer.chrome.com/docs/webstore/
- Extension Policies: https://developer.chrome.com/docs/webstore/program-policies/

---

## Quick Checklist

- [ ] Google Developer account created and verified
- [ ] $5 registration fee paid
- [ ] Extension ZIP file ready
- [ ] 128x128 icon prepared
- [ ] Screenshots created (at least 1)
- [ ] Description written
- [ ] Privacy policy URL ready
- [ ] Permissions justified
- [ ] Tested on Chrome locally

---

*Last Updated: January 15, 2026*
