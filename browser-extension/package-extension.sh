#!/bin/bash
# InfoPilot Explorer - Chrome Extension Packaging Script
# Creates a ZIP file ready for Chrome Web Store submission

set -e

echo "🧩 InfoPilot Explorer - Chrome Extension Packager"
echo "================================================="

EXTENSION_DIR="/app/browser-extension"
OUTPUT_DIR="/app/browser-extension/dist"
ZIP_NAME="infopilot-infojet-extension.zip"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Create icons directory and generate placeholder icons
mkdir -p "$EXTENSION_DIR/icons"

# Generate SVG icons that can be converted to PNG
cat > "$EXTENSION_DIR/icons/icon.svg" << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#7c3aed"/>
      <stop offset="100%" style="stop-color:#a855f7"/>
    </linearGradient>
  </defs>
  <rect fill="url(#grad)" width="128" height="128" rx="24"/>
  <text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" font-size="70" fill="white">🚀</text>
</svg>
EOF

# Create PNG placeholders (these would normally be actual PNG files)
# For now, create a simple HTML file explaining icon requirements
cat > "$EXTENSION_DIR/icons/README.md" << 'EOF'
# Extension Icons

Replace these placeholder files with actual PNG icons:

- icon16.png (16x16 pixels)
- icon32.png (32x32 pixels)
- icon48.png (48x48 pixels)
- icon128.png (128x128 pixels)

## Quick Generation

Use the SVG file (icon.svg) to generate PNGs:

```bash
# Using ImageMagick
convert -background none icon.svg -resize 16x16 icon16.png
convert -background none icon.svg -resize 32x32 icon32.png
convert -background none icon.svg -resize 48x48 icon48.png
convert -background none icon.svg -resize 128x128 icon128.png

# Or use online tools like:
# - https://convertio.co/svg-png/
# - https://cloudconvert.com/svg-to-png
```

## Icon Requirements

- Format: PNG
- Background: Transparent or solid color
- Style: Match the InfoPilot purple gradient theme (#7c3aed to #a855f7)
EOF

# Create placeholder PNGs (1x1 pixel, will need to be replaced)
# Using base64 encoded minimal PNGs
echo "Creating placeholder icons..."

# 16x16 purple PNG (base64)
echo "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAKElEQVQ4jWNgGAXDADDi4/j//z8DAwMDAxMxhowCCgBRBowCCgBRBgAA1QECEVxTbQAAAABJRU5ErkJggg==" | base64 -d > "$EXTENSION_DIR/icons/icon16.png" 2>/dev/null || echo "⚠ Could not create icon16.png"

echo "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAKElEQVRYhe3BAQEAAACCIP+vbkhAAQAAAAAAAAAAAAAAAAAAAAB8GE4AAAFiS8lnAAAAAElFTkSuQmCC" | base64 -d > "$EXTENSION_DIR/icons/icon32.png" 2>/dev/null || echo "⚠ Could not create icon32.png"

echo "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAKElEQVRoge3BAQ0AAADCIPunfg43YAAAAAAAAAAAAAAAAAAAAAAA4Dd+AAABHckKtgAAAABJRU5ErkJggg==" | base64 -d > "$EXTENSION_DIR/icons/icon48.png" 2>/dev/null || echo "⚠ Could not create icon48.png"

echo "iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAAKklEQVR4nO3BAQ0AAADCoPdPbQ8HFAAAAAAAAAAAAAAAAAAAAAAAAO8GvIAAAYWPBLYAAAAASUVORK5CYII=" | base64 -d > "$EXTENSION_DIR/icons/icon128.png" 2>/dev/null || echo "⚠ Could not create icon128.png"

# Create the ZIP file
echo "Creating ZIP package..."
cd "$EXTENSION_DIR"

# Remove old zip if exists
rm -f "$OUTPUT_DIR/$ZIP_NAME"

# Create zip with all required files
zip -r "$OUTPUT_DIR/$ZIP_NAME" \
    manifest.json \
    popup.html \
    popup.js \
    background.js \
    content.js \
    content.css \
    options.html \
    options.js \
    icons/ \
    -x "*.DS_Store" \
    -x "dist/*"

echo ""
echo "✅ Extension packaged successfully!"
echo "📦 Output: $OUTPUT_DIR/$ZIP_NAME"
echo ""
echo "Next steps:"
echo "1. Replace placeholder icons with actual PNG files"
echo "2. Go to https://chrome.google.com/webstore/devconsole"
echo "3. Create new item"
echo "4. Upload the ZIP file"
echo "5. Fill in store listing"
echo "6. Submit for review"
