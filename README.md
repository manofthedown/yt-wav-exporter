# YouTube to WAV Converter

## Project Overview
- **Project name**: YouTube Audio Exporter
- **Type**: Web application (frontend + backend)
- **Core functionality**: User inputs a YouTube URL, clicks export button, downloads a .wav file of the audio
- **Target users**: Anyone who wants to extract audio from YouTube videos

## Technical Stack
- **Backend**: Python Flask + yt-dlp (for YouTube download)
- **Frontend**: HTML/CSS/Vanilla JS

## UI/UX Specification

### Layout Structure
- Single page, centered card layout
- Max-width: 500px, centered vertically and horizontally
- Dark theme with neon accents

### Visual Design
- **Background**: Deep charcoal (#0d0d0d) with subtle radial gradient
- **Card**: Dark gray (#1a1a1a) with soft shadow
- **Primary accent**: Electric cyan (#00f0ff)
- **Secondary**: Soft purple (#8b5cf6)
- **Text**: White (#ffffff) primary, gray (#888888) secondary
- **Font**: "Outfit" from Google Fonts (modern geometric sans)
- **Border radius**: 12px for card, 8px for inputs/buttons

### Components
1. **Header**: App title with icon
2. **URL Input**: Full-width text input with placeholder "Paste YouTube URL here..."
3. **Export Button**:
   - Full-width, cyan background
   - Hover: slight glow effect, brighten
   - Loading state: pulsing animation with "Converting..." text
4. **Status Message**: Shows download progress or errors
5. **Download Link**: Appears when ready, styled as secondary button

## Acceptance Criteria
- [ ] URL input accepts any YouTube URL format
- [ ] Clicking export shows loading state
- [ ] Valid YouTube video converts to WAV successfully
- [ ] WAV file downloads automatically
- [ ] Errors display user-friendly messages
- [ ] UI matches dark theme spec