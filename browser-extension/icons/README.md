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
