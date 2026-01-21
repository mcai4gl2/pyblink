# Blink Message Playground - Frontend

React + TypeScript frontend for the Blink Message Playground.

## Features

- ✅ Schema editor with Monaco Editor
- ✅ Input panel with format selector
- ✅ Output display for all 5 formats
- ✅ Copy to clipboard functionality
- ✅ Collapsible output sections
- ✅ Binary hex and decoded views
- ✅ Responsive layout
- ✅ Tailwind CSS styling

## Setup

### Prerequisites

- Node.js 16+
- Backend API running on http://127.0.0.1:8000

### Installation

```bash
# Install dependencies (already done)
npm install

# Start development server
npm start
```

The app will open at http://localhost:3000

## Usage

1. **Edit Schema:** Modify the schema in the top-left editor
2. **Validate:** Click "Validate Schema" to check syntax
3. **Select Format:** Choose input format from dropdown
4. **Enter Message:** Type or paste your message
5. **Convert:** Click "Convert" to see all format outputs
6. **Copy:** Click "Copy" on any output to copy to clipboard

## Components

- **SchemaEditor** - Monaco editor for schema definition
- **InputPanel** - Format selector + input editor
- **OutputPanel** - Display all converted formats
- **API Service** - Axios-based backend communication

## Environment Variables

Create `.env` file:

```
REACT_APP_API_URL=http://127.0.0.1:8000
```

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests

## Tech Stack

- React 19
- TypeScript 4.9
- Monaco Editor
- Axios
- Tailwind CSS
- Lucide Icons

## Project Structure

```
src/
├── components/
│   ├── SchemaEditor.tsx
│   ├── InputPanel.tsx
│   └── OutputPanel.tsx
├── services/
│   └── api.ts
├── types/
│   └── index.ts
├── App.tsx
└── index.tsx
```

## Next Steps (Phase 3+)

- [ ] Enhanced binary viewers with byte-by-byte breakdown
- [ ] Save/load playground state
- [ ] Example library
- [ ] Keyboard shortcuts
- [ ] Dark mode

## Troubleshooting

**Monaco Editor not loading:**
- Clear browser cache and reload
- Check console for errors

**API connection failed:**
- Ensure backend is running on port 8000
- Check CORS settings in backend

**Tailwind styles not working:**
- Restart dev server after config changes
- Check tailwind.config.js content paths
