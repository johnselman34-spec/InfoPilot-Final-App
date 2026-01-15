# InfoJet - Chrome Web Store Submission Guide

## Prerequisites

1. **Google Developer Account** ($5 one-time fee)
   - Sign up at: https://chrome.google.com/webstore/devconsole

2. **Extension Package**
   - Run: `./package-extension.sh`
   - Output: `dist/infopilot-infojet-extension.zip`

3. **Required Assets**
   - Store icon: 128x128 PNG
   - Promotional images:
     - Small tile: 440x280 PNG
     - Large tile: 920x680 PNG (optional)
     - Marquee: 1400x560 PNG (optional)
   - Screenshots: 1280x800 or 640x400 PNG (1-5 images)

## Store Listing Content

### Basic Information

**Name**: InfoJet - InfoPilot Quick Search

**Summary** (132 chars max):
Quick search powered by InfoPilot Explorer. Search with custom protocols right from your browser!

**Description**:
🚀 **InfoJet** - Your Browser Search Companion by InfoPilot Explorer

Instantly search the web using your custom InfoPilot protocols without leaving your current page!

**FEATURES:**
✨ **Quick Search Popup** - Click the icon to search instantly
📋 **Your Protocols** - Access your saved search protocols
🖱️ **Context Menu** - Right-click selected text to search
🚀 **Floating Button** - Select text and click the rocket to search
⌨️ **Keyboard Shortcuts** - Ctrl+Shift+S for instant search
⚙️ **Customizable** - Set default protocols and preferences

**HOW IT WORKS:**
1. Install the extension
2. Log in with your InfoPilot Explorer account
3. Click the icon or select text to search
4. Results open in InfoPilot Explorer

**REQUIRES:**
- Free InfoPilot Explorer account
- Works with any website

**PRIVACY:**
- We only access data when you initiate a search
- Your protocols stay synced with InfoPilot Explorer
- No tracking or selling of your data

Part of the InfoPilot Explorer ecosystem - the world's first information exchange network!

📖 **Pro Tip**: Create custom protocols in InfoPilot Explorer and access them instantly from any webpage!

### Category
Productivity

### Language
English (United States)

## Privacy Practices

**Single Purpose Description**:
This extension allows users to quickly search the web using their custom InfoPilot Explorer search protocols directly from any webpage.

**Permissions Justification**:

| Permission | Justification |
|------------|---------------|
| storage | Store user preferences, cached protocols, and authentication tokens locally |
| activeTab | Access the current tab to get selected text for search functionality |
| contextMenus | Add right-click menu option for quick searching of selected text |
| host_permissions (emergentagent.com) | Connect to InfoPilot Explorer API to authenticate and fetch user protocols |

**Data Usage**:
- Search queries are sent to InfoPilot Explorer servers
- No data is sold to third parties
- Data collection is limited to functionality requirements

## Screenshots

### Screenshot 1: Popup
Show the extension popup with:
- Search input field
- Protocol list
- User stats

### Screenshot 2: Context Menu
Show right-click menu with "Search with InfoJet" option

### Screenshot 3: Floating Button
Show the floating rocket button on selected text

### Screenshot 4: Settings
Show the options/settings page

## Submission Checklist

- [ ] Replace placeholder icons with actual PNG files
- [ ] Test extension thoroughly
- [ ] Create screenshots
- [ ] Create promotional images
- [ ] Write privacy policy (host on your website)
- [ ] Verify all permissions are justified
- [ ] Submit for review

## After Submission

1. Review typically takes 1-3 business days
2. You'll receive email notification
3. If rejected, address feedback and resubmit
4. Once approved, extension goes live!

## Updating the Extension

1. Increment version in manifest.json
2. Re-run package script
3. Upload new ZIP to developer console
4. Submit update for review

## Support

- Website: https://infopilotexplorer.biz
- Email: support@infopilot.com
- Documentation: https://infopilotexplorer.biz/tutorials
