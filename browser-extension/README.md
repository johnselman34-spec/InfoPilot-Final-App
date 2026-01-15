# InfoJet Browser Extension

InfoJet is the official Chrome browser extension for InfoPilot Explorer, enabling quick search functionality right from your browser.

## Features

- 🔍 **Quick Search Popup** - Click the extension icon to search instantly
- 📋 **Protocol Selection** - Choose from your saved protocols for customized searches
- 🖱️ **Context Menu Search** - Right-click selected text to search with InfoJet
- 🚀 **Floating Search Button** - Select text on any page and click the floating button
- ⌨️ **Keyboard Shortcuts** - Use Ctrl/Cmd + Shift + S for quick search
- ⚙️ **Customizable Settings** - Configure default protocols and behavior

## Installation

### From Chrome Web Store (Coming Soon)
1. Visit the Chrome Web Store
2. Search for "InfoJet"
3. Click "Add to Chrome"

### Manual Installation (Developer Mode)
1. Download or clone this repository
2. Open Chrome and go to `chrome://extensions/`
3. Enable "Developer mode" (top right toggle)
4. Click "Load unpacked"
5. Select the `browser-extension` folder

## Usage

### Quick Search
1. Click the InfoJet icon in your toolbar
2. Type your search query
3. (Optional) Select a protocol from your list
4. Press Enter or click the search button

### Context Menu
1. Select any text on a webpage
2. Right-click
3. Choose "Search with InfoJet"

### Floating Button
1. Select text on any webpage
2. A small rocket button appears
3. Click it to search the selected text

### Keyboard Shortcut
- Press `Ctrl + Shift + S` (Windows/Linux) or `Cmd + Shift + S` (Mac)
- With text selected, it will search that text
- Without selection, it opens the popup

## Settings

Access settings by clicking "⚙️ Settings" in the popup or right-clicking the extension icon and selecting "Options".

### Available Settings
- **Show floating search button** - Toggle the floating button on text selection
- **Open results in new tab** - Control where search results open
- **Default search protocol** - Set a protocol to use by default
- **Enable notifications** - Receive notifications from InfoPilot

## Permissions

The extension requires:
- `storage` - Save your settings and cached protocols
- `activeTab` - Access current tab for context menu functionality
- `contextMenus` - Add right-click menu options

## Privacy

- Your search queries are sent to InfoPilot Explorer servers
- Local storage is used for caching protocols and settings
- No data is shared with third parties

## Support

For help or feedback:
- Visit [InfoPilot Explorer](https://infopilot-explorer.com)
- Email: support@infopilot.com

## Version History

### v1.0.0
- Initial release
- Quick search popup
- Context menu integration
- Floating search button
- Protocol selection
- Settings page
