# Blink Message Playground - Web Design Document

**Version:** 1.0  
**Date:** 2026-01-21  
**Status:** Design Approved - Ready for Implementation

## Technology Decisions ✅

- **Frontend:** React with TypeScript
- **Backend:** FastAPI with uv (Python)
- **Deployment:** Local development server (localhost)
- **Storage:** File-based JSON (30-day retention)
- **Implementation:** Phased approach (MVP → Enhanced features)

---

## 1. Project Overview

### 1.1 Purpose
Create an interactive single-page web application that allows users to:
- Define Blink schemas
- Input messages in any supported format
- Automatically convert between all formats (Compact Binary, Native Binary, Tag, JSON, XML)
- View binary formats in both hex and human-readable representations
- Save and share their work via persistent URLs

### 1.2 Target Users
- Blink protocol developers testing schemas
- Integration engineers validating message formats
- Students learning the Blink protocol
- API designers prototyping message structures

### 1.3 Key Value Proposition
**"Paste your schema and message once, see it in all formats instantly"**

---

## 2. User Interface Design

### 2.1 Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  🔷 Blink Message Playground                    [Save] [Load]│
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Schema Definition                                    │    │
│  │ ┌─────────────────────────────────────────────────┐ │    │
│  │ │ namespace Demo                                   │ │    │
│  │ │ Person/1 -> string Name, u32 Age                │ │    │
│  │ │                                                   │ │    │
│  │ └─────────────────────────────────────────────────┘ │    │
│  │                                        [Validate Schema]  │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Input Format: [JSON ▼]                    [Convert] │    │
│  │ ┌─────────────────────────────────────────────────┐ │    │
│  │ │ {                                                │ │    │
│  │ │   "$type": "Demo:Person",                       │ │    │
│  │ │   "Name": "Alice",                              │ │    │
│  │ │   "Age": 30                                     │ │    │
│  │ │ }                                               │ │    │
│  │ └─────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌──────────────────────────────────────────────────────────┤
│  │ Output Formats                                      [▼]   │
│  ├──────────────────────────────────────────────────────────┤
│  │                                                           │
│  │ ┌─ Tag Format ─────────────────────────────────────┐    │
│  │ │ @Demo:Person|Name=Alice|Age=30                   │    │
│  │ │                                        [Copy]     │    │
│  │ └──────────────────────────────────────────────────┘    │
│  │                                                           │
│  │ ┌─ JSON Format ────────────────────────────────────┐    │
│  │ │ {                                                 │    │
│  │ │   "$type": "Demo:Person",                        │    │
│  │ │   "Name": "Alice",                               │    │
│  │ │   "Age": 30                                      │    │
│  │ │ }                                    [Copy]      │    │
│  │ └──────────────────────────────────────────────────┘    │
│  │                                                           │
│  │ ┌─ XML Format ─────────────────────────────────────┐    │
│  │ │ <Demo:Person>                                     │    │
│  │ │   <Name>Alice</Name>                             │    │
│  │ │   <Age>30</Age>                                  │    │
│  │ │ </Demo:Person>                       [Copy]      │    │
│  │ └──────────────────────────────────────────────────┘    │
│  │                                                           │
│  │ ┌─ Compact Binary ─────────────────────────────────┐    │
│  │ │ Hex View:                                         │    │
│  │ │ 0000: 0F 01 05 41 6C 69 63 65 1E                 │    │
│  │ │                                                   │    │
│  │ │ Decoded View:                                     │    │
│  │ │ • Size: 15 bytes                                 │    │
│  │ │ • Type ID: 1 (Demo:Person)                       │    │
│  │ │ • Name: "Alice" (5 bytes)                        │    │
│  │ │ • Age: 30 (VLC: 0x1E)                           │    │
│  │ │                                        [Copy Hex] │    │
│  │ └──────────────────────────────────────────────────┘    │
│  │                                                           │
│  │ ┌─ Native Binary ──────────────────────────────────┐    │
│  │ │ Hex View:                                         │    │
│  │ │ 0000: 15 00 00 00 01 00 00 00 00 00 00 00 00 00 │    │
│  │ │ 0010: 00 00 1E 00 00 00 05 00 00 00 41 6C 69 63 │    │
│  │ │ 0020: 65                                          │    │
│  │ │                                                   │    │
│  │ │ Decoded View:                                     │    │
│  │ │ • Size: 21 bytes                                 │    │
│  │ │ • Type ID: 1 (Demo:Person)                       │    │
│  │ │ • Extension Offset: 0 (none)                     │    │
│  │ │ • Name offset: @0x0C → "Alice" (5 bytes)        │    │
│  │ │ • Age: 30 (u32 little-endian)                   │    │
│  │ │                                        [Copy Hex] │    │
│  │ └──────────────────────────────────────────────────┘    │
│  │                                                           │
│  └──────────────────────────────────────────────────────────┘
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Share Link: https://blink.example.com/p/a3f9d2e1    │    │
│  │                                        [Copy Link]   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Breakdown

#### 2.2.1 Schema Editor
- **Type:** Textarea with syntax highlighting
- **Features:**
  - Line numbers
  - Blink syntax highlighting (keywords, types, comments)
  - Auto-indent
  - Error highlighting (red underline for invalid syntax)
- **Validation:**
  - Real-time syntax checking
  - Display errors below editor with line numbers
  - Success indicator when valid

#### 2.2.2 Input Format Selector
- **Type:** Dropdown menu
- **Options:**
  - Tag Format
  - JSON Format
  - XML Format
  - Compact Binary (hex input)
  - Native Binary (hex input)
- **Behavior:**
  - Changes input editor mode (text vs hex)
  - Updates placeholder examples
  - Preserves content when switching if possible

#### 2.2.3 Input Editor
- **Type:** Textarea (adaptive)
- **Modes:**
  - **Text mode:** For Tag, JSON, XML
    - Syntax highlighting per format
    - Auto-formatting option
  - **Hex mode:** For binary formats
    - Hex input validation (0-9, A-F)
    - Auto-spacing (groups of 2 or 8)
    - Offset display

#### 2.2.4 Output Panels
- **Type:** Collapsible sections (accordion or tabs)
- **Features:**
  - Each format in separate panel
  - Read-only display with syntax highlighting
  - Copy button for each format
  - Download button (save as .txt, .json, .xml, .bin)
  - Toggle between "Pretty" and "Compact" for text formats

#### 2.2.5 Binary Viewers
- **Hex View:**
  - 16 bytes per row
  - Offset column (0000, 0010, etc.)
  - Hex values with spacing
  - ASCII preview column (printable chars only)
  
- **Decoded View:**
  - Human-readable structure breakdown
  - Field-by-field analysis
  - Offset annotations
  - Type information
  - Value interpretation

#### 2.2.6 Save/Load System
- **Save:**
  - Generates unique ID (8-char alphanumeric)
  - Stores schema + input format + input data
  - Returns shareable URL
  - Optional: Add title/description
  
- **Load:**
  - Parse ID from URL parameter
  - Restore schema and input
  - Auto-convert to all formats

---

## 3. Technical Architecture

### 3.1 Technology Stack

#### Frontend
- **Framework:** Vanilla JavaScript + HTML/CSS (or React/Vue if preferred)
- **Styling:** Modern CSS with:
  - CSS Grid/Flexbox for layout
  - CSS Variables for theming
  - Responsive design (mobile-friendly)
- **Code Highlighting:** 
  - Prism.js or Monaco Editor (VS Code editor)
  - Custom Blink schema grammar
- **Icons:** Lucide Icons or similar

#### Backend
- **Framework:** Python Flask or FastAPI
- **PyBlink Integration:** Direct import of existing codec modules
- **Storage:** File-based (JSON files in `data/` directory)
- **API Endpoints:**
  - `POST /api/convert` - Convert message between formats
  - `POST /api/validate-schema` - Validate schema syntax
  - `POST /api/save` - Save schema + message, return ID
  - `GET /api/load/{id}` - Load saved data by ID

#### Deployment
- **Option 1:** Standalone Flask app (simple, self-contained)
- **Option 2:** Static frontend + serverless backend (AWS Lambda, Vercel)
- **Option 3:** Docker container (easy deployment)

### 3.2 Data Flow

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ 1. User inputs schema + message
       ▼
┌─────────────────────────────────────┐
│  Frontend JavaScript                │
│  • Validate input                   │
│  • Send to backend API              │
└──────┬──────────────────────────────┘
       │
       │ 2. POST /api/convert
       │    { schema, format, data }
       ▼
┌─────────────────────────────────────┐
│  Backend (Flask/FastAPI)            │
│  • Parse schema                     │
│  • Decode input format              │
│  • Encode to all formats            │
│  • Return results                   │
└──────┬──────────────────────────────┘
       │
       │ 3. JSON response
       │    { tag, json, xml, compact, native }
       ▼
┌─────────────────────────────────────┐
│  Frontend JavaScript                │
│  • Update all output panels         │
│  • Render hex views                 │
│  • Enable copy buttons              │
└─────────────────────────────────────┘
```

### 3.3 API Specification

#### 3.3.1 Convert Message

**Endpoint:** `POST /api/convert`

**Request:**
```json
{
  "schema": "namespace Demo\nPerson/1 -> string Name, u32 Age",
  "input_format": "json",
  "input_data": "{\"$type\":\"Demo:Person\",\"Name\":\"Alice\",\"Age\":30}"
}
```

**Response:**
```json
{
  "success": true,
  "outputs": {
    "tag": "@Demo:Person|Name=Alice|Age=30",
    "json": "{\"$type\":\"Demo:Person\",\"Name\":\"Alice\",\"Age\":30}",
    "xml": "<Demo:Person><Name>Alice</Name><Age>30</Age></Demo:Person>",
    "compact_binary": {
      "hex": "0F010541 6C696365 1E",
      "decoded": {
        "size": 15,
        "type_id": 1,
        "fields": [
          {"name": "Name", "value": "Alice", "bytes": "05 41 6C 69 63 65"},
          {"name": "Age", "value": 30, "bytes": "1E"}
        ]
      }
    },
    "native_binary": {
      "hex": "15000000 01000000 00000000 00000000 1E000000 05000000 416C6963 65",
      "decoded": {
        "size": 21,
        "type_id": 1,
        "ext_offset": 0,
        "fields": [
          {"name": "Name", "offset": 12, "value": "Alice", "bytes": "05 00 00 00 41 6C 69 63 65"},
          {"name": "Age", "value": 30, "bytes": "1E 00 00 00"}
        ]
      }
    }
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Schema parsing failed: Unexpected token at line 2",
  "line": 2,
  "column": 15
}
```

#### 3.3.2 Validate Schema

**Endpoint:** `POST /api/validate-schema`

**Request:**
```json
{
  "schema": "namespace Demo\nPerson/1 -> string Name, u32 Age"
}
```

**Response:**
```json
{
  "valid": true,
  "groups": [
    {
      "name": "Demo:Person",
      "type_id": 1,
      "fields": [
        {"name": "Name", "type": "string"},
        {"name": "Age", "type": "u32"}
      ]
    }
  ]
}
```

#### 3.3.3 Save Playground State

**Endpoint:** `POST /api/save`

**Request:**
```json
{
  "schema": "namespace Demo\nPerson/1 -> string Name, u32 Age",
  "input_format": "json",
  "input_data": "{\"$type\":\"Demo:Person\",\"Name\":\"Alice\",\"Age\":30}",
  "title": "Person Example",
  "description": "Simple person message demo"
}
```

**Response:**
```json
{
  "success": true,
  "id": "a3f9d2e1",
  "url": "https://blink.example.com/p/a3f9d2e1",
  "expires": "2027-01-21T19:44:08Z"
}
```

#### 3.3.4 Load Playground State

**Endpoint:** `GET /api/load/{id}`

**Response:**
```json
{
  "success": true,
  "data": {
    "schema": "namespace Demo\nPerson/1 -> string Name, u32 Age",
    "input_format": "json",
    "input_data": "{\"$type\":\"Demo:Person\",\"Name\":\"Alice\",\"Age\":30}",
    "title": "Person Example",
    "description": "Simple person message demo",
    "created": "2026-01-21T19:44:08Z"
  }
}
```

### 3.4 File Storage Structure

```
data/
├── index.json              # Metadata index
└── playgrounds/
    ├── a3f9d2e1.json      # Saved playground state
    ├── b7k2m9x4.json
    └── ...
```

**Playground File Format:**
```json
{
  "id": "a3f9d2e1",
  "created": "2026-01-21T19:44:08Z",
  "title": "Person Example",
  "description": "Simple person message demo",
  "schema": "namespace Demo\nPerson/1 -> string Name, u32 Age",
  "input_format": "json",
  "input_data": "{\"$type\":\"Demo:Person\",\"Name\":\"Alice\",\"Age\":30}"
}
```

---

## 4. User Experience Flow

### 4.1 First-Time User Flow

1. **Landing Page:**
   - Pre-populated with example schema and message
   - "Try it now" button to convert
   - Brief explanation of Blink protocol

2. **Interaction:**
   - User clicks "Convert"
   - All output panels populate instantly
   - User can explore different formats

3. **Experimentation:**
   - User modifies schema or message
   - Real-time validation feedback
   - Re-convert to see changes

4. **Sharing:**
   - User clicks "Save"
   - Gets shareable link
   - Can share with colleagues

### 4.2 Returning User Flow (via Link)

1. **Load from URL:**
   - Page loads with ID parameter
   - Auto-fetches saved data
   - Restores schema and input
   - Auto-converts to all formats

2. **Modification:**
   - User can edit and re-convert
   - Can save as new version

### 4.3 Error Handling

**Schema Errors:**
- Highlight error line in schema editor
- Show error message with line/column
- Suggest fixes when possible

**Input Errors:**
- Show which format failed to parse
- Display specific error (e.g., "Invalid JSON at line 3")
- Offer to auto-format if possible

**Conversion Errors:**
- Show which output format failed
- Display error reason
- Continue with other formats that succeeded

---

## 5. Features & Functionality

### 5.1 Core Features (MVP)

✅ **Must Have:**
1. Schema editor with validation
2. Input editor with format selection
3. Convert to all 5 formats (Tag, JSON, XML, Compact, Native)
4. Hex view for binary formats
5. Decoded view for binary formats
6. Copy buttons for each output
7. Save/load via URL
8. Error handling and display

### 5.2 Enhanced Features (V1.1)

🔄 **Should Have:**
1. Syntax highlighting for all formats
2. Auto-formatting (prettify JSON/XML)
3. Download outputs as files
4. Example library (pre-made schemas)
5. Dark mode toggle
6. Responsive mobile layout
7. Keyboard shortcuts (Ctrl+Enter to convert)

### 5.3 Advanced Features (V2.0)

💡 **Nice to Have:**
1. Schema auto-complete
2. Field-level editing (GUI form)
3. Diff view (compare two messages)
4. Performance metrics (encode/decode time)
5. Batch conversion (multiple messages)
6. Schema versioning
7. Export as code (Python, Java, C++)
8. WebAssembly for client-side conversion

---

## 6. Design Aesthetics

### 6.1 Visual Style

**Theme:** Modern, clean, developer-focused

**Color Palette:**
- Primary: Deep blue (#2563eb)
- Secondary: Emerald green (#10b981)
- Background: Light gray (#f9fafb)
- Dark mode: Dark slate (#1e293b)
- Accent: Amber (#f59e0b) for highlights
- Error: Red (#ef4444)
- Success: Green (#22c55e)

**Typography:**
- Headers: Inter or Outfit (Google Fonts)
- Code: JetBrains Mono or Fira Code
- Body: System font stack

**Layout:**
- Generous whitespace
- Card-based sections with subtle shadows
- Smooth transitions and animations
- Sticky header for navigation

### 6.2 Responsive Breakpoints

- **Desktop:** 1200px+ (3-column layout)
- **Tablet:** 768px-1199px (2-column layout)
- **Mobile:** <768px (single column, stacked)

### 6.3 Accessibility

- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader friendly
- High contrast mode
- Focus indicators
- ARIA labels

---

## 7. Implementation Plan

### 7.1 Phase 1: Backend API (Week 1)

**Tasks:**
1. Set up Flask/FastAPI project structure
2. Integrate PyBlink codec modules
3. Implement `/api/convert` endpoint
4. Implement `/api/validate-schema` endpoint
5. Add error handling and logging
6. Write API tests
7. Create API documentation

**Deliverables:**
- Working REST API
- API documentation (OpenAPI/Swagger)
- Unit tests for all endpoints

### 7.2 Phase 2: Frontend Core (Week 2)

**Tasks:**
1. Create HTML structure
2. Implement CSS layout (responsive)
3. Build schema editor component
4. Build input editor component
5. Build output panels
6. Implement format conversion UI
7. Add copy-to-clipboard functionality

**Deliverables:**
- Functional single-page app
- All core UI components
- Format conversion working

### 7.3 Phase 3: Binary Viewers (Week 3)

**Tasks:**
1. Implement hex viewer component
2. Implement decoded view component
3. Add offset annotations
4. Add field highlighting
5. Implement hover tooltips
6. Add download functionality

**Deliverables:**
- Complete binary visualization
- Interactive hex view
- Detailed decoded view

### 7.4 Phase 4: Save/Load System (Week 4)

**Tasks:**
1. Implement file storage backend
2. Create unique ID generation
3. Build save API endpoint
4. Build load API endpoint
5. Add URL parameter handling
6. Implement share link UI
7. Add expiration logic (optional)

**Deliverables:**
- Working save/load system
- Shareable URLs
- Persistent storage

### 7.5 Phase 5: Polish & Deploy (Week 5)

**Tasks:**
1. Add syntax highlighting
2. Implement error handling UI
3. Add loading states
4. Optimize performance
5. Cross-browser testing
6. Mobile responsiveness
7. Deploy to production
8. Write user documentation

**Deliverables:**
- Production-ready application
- User guide
- Deployment documentation

---

## 8. Technical Considerations

### 8.1 Performance

**Frontend:**
- Debounce validation (500ms delay)
- Lazy load output panels
- Virtual scrolling for large hex dumps
- Web Workers for heavy parsing (optional)

**Backend:**
- Cache compiled schemas (LRU cache)
- Rate limiting (prevent abuse)
- Gzip compression for responses
- CDN for static assets

### 8.2 Security

**Input Validation:**
- Sanitize all user inputs
- Limit schema size (max 100KB)
- Limit message size (max 1MB)
- Validate hex input format

**Storage:**
- No sensitive data storage
- Auto-expire old playgrounds (90 days)
- Rate limit save operations
- Validate IDs before file access

**API:**
- CORS configuration
- Rate limiting per IP
- Request size limits
- Error message sanitization

### 8.3 Browser Compatibility

**Target Browsers:**
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Android)

**Polyfills:**
- Fetch API (if needed)
- Promise (if needed)
- CSS Grid (fallback to Flexbox)

---

## 9. Testing Strategy

### 9.1 Backend Testing

**Unit Tests:**
- Schema parsing
- Format conversion
- Error handling
- File storage operations

**Integration Tests:**
- API endpoints
- End-to-end conversion
- Save/load workflow

**Test Coverage Target:** 80%+

### 9.2 Frontend Testing

**Manual Testing:**
- All format conversions
- Error scenarios
- Mobile responsiveness
- Cross-browser compatibility

**Automated Testing (Optional):**
- Jest for JavaScript logic
- Cypress for E2E testing

### 9.3 User Acceptance Testing

**Test Scenarios:**
1. Convert simple message (all formats)
2. Convert complex message (nested groups, sequences)
3. Handle invalid schema
4. Handle invalid input
5. Save and load via URL
6. Copy outputs to clipboard
7. Mobile usage

---

## 10. Deployment Options

### 10.1 Option A: Simple Flask Deployment

**Pros:**
- Easy to set up
- Self-contained
- Direct PyBlink integration

**Cons:**
- Requires Python server
- Scaling limitations

**Hosting:**
- Heroku
- DigitalOcean App Platform
- AWS EC2 (small instance)

### 10.2 Option B: Static + Serverless

**Pros:**
- Highly scalable
- Low cost
- Fast global delivery

**Cons:**
- More complex setup
- Cold start latency

**Hosting:**
- Frontend: Vercel, Netlify, Cloudflare Pages
- Backend: AWS Lambda, Vercel Functions

### 10.3 Option C: Docker Container

**Pros:**
- Portable
- Easy deployment
- Consistent environment

**Cons:**
- Requires container hosting

**Hosting:**
- Docker Hub + any cloud provider
- Google Cloud Run
- AWS ECS/Fargate

---

## 11. Future Enhancements

### 11.1 Short-term (3-6 months)

1. **Example Library:**
   - Pre-built schemas for common use cases
   - One-click load examples
   - Community contributions

2. **Schema Validation:**
   - More detailed error messages
   - Suggestions for fixes
   - Schema linting

3. **Performance Metrics:**
   - Show encode/decode time
   - Message size comparison
   - Efficiency recommendations

### 11.2 Long-term (6-12 months)

1. **Collaborative Editing:**
   - Real-time collaboration (WebSocket)
   - Shared playgrounds
   - Comments and annotations

2. **Code Generation:**
   - Export schema as Python classes
   - Export as Java/C++ code
   - Generate documentation

3. **Advanced Visualization:**
   - Message structure tree view
   - Field dependency graph
   - Binary layout diagram

4. **Integration:**
   - REST API for programmatic access
   - CLI tool for local testing
   - IDE plugins (VS Code extension)

---

## 12. Success Metrics

### 12.1 Launch Metrics

- **Functionality:** All core features working
- **Performance:** Page load < 2s, conversion < 500ms
- **Reliability:** 99% uptime
- **Usability:** No critical bugs in UAT

### 12.2 Post-Launch Metrics

- **Usage:** Track conversions per day
- **Engagement:** Average session duration
- **Sharing:** Number of saved playgrounds
- **Errors:** Error rate < 5%

---

## 13. Open Questions

1. **Hosting Budget:** What's the budget for hosting? (affects deployment choice)
2. **Domain Name:** Do we have a domain, or use subdomain?
3. **Analytics:** Do we want usage analytics (Google Analytics, Plausible)?
4. **Authentication:** Do we need user accounts, or keep it anonymous?
5. **Storage Limits:** How many playgrounds can we store? (disk space)
6. **Expiration Policy:** Should saved playgrounds expire? If so, when?
7. **Rate Limiting:** What limits for API calls? (prevent abuse)

---

## 14. Next Steps

### 14.1 Design Review
- [ ] Review this document
- [ ] Gather feedback
- [ ] Refine requirements
- [ ] Finalize scope

### 14.2 Technical Decisions
- [ ] Choose frontend framework (Vanilla JS vs React/Vue)
- [ ] Choose deployment option (A, B, or C)
- [ ] Decide on storage strategy
- [ ] Set up development environment

### 14.3 Prototyping
- [ ] Create mockups (Figma/Sketch)
- [ ] Build simple proof-of-concept
- [ ] Test PyBlink integration
- [ ] Validate API design

### 14.4 Implementation
- [ ] Set up project structure
- [ ] Begin Phase 1 (Backend API)
- [ ] Iterate based on feedback

---

## Appendix A: Example Schemas

### A.1 Simple Person
```blink
namespace Demo
Person/1 -> string Name, u32 Age
```

### A.2 Trading Order
```blink
namespace Trading
Order/100 -> 
    string Symbol,
    decimal Price,
    u64 Quantity,
    string Side,
    millitime Timestamp
```

### A.3 Nested Groups
```blink
namespace Example
Address -> string Street, string City, u32 Zip
Person/1 -> string Name, u32 Age, Address HomeAddress
```

### A.4 Dynamic Groups
```blink
namespace Shapes
Shape
Circle/1 : Shape -> u32 Radius
Rectangle/2 : Shape -> u32 Width, u32 Height
Canvas/3 -> Shape* [] Shapes
```

---

## Appendix B: Technology Alternatives

### Frontend Frameworks
- **Vanilla JS:** Lightweight, no dependencies
- **React:** Component-based, large ecosystem
- **Vue:** Progressive, easier learning curve
- **Svelte:** Compiled, smallest bundle size

### Code Editors
- **Monaco Editor:** Full VS Code editor (heavy, 2MB)
- **CodeMirror:** Lightweight, customizable
- **Ace Editor:** Mature, feature-rich
- **Prism.js:** Syntax highlighting only (lightest)

### Backend Frameworks
- **Flask:** Minimal, flexible
- **FastAPI:** Modern, async, auto-docs
- **Django:** Full-featured (overkill for this)

### Styling Approaches
- **Vanilla CSS:** Full control, no dependencies
- **Tailwind CSS:** Utility-first, rapid development
- **Bootstrap:** Component library, consistent
- **Styled Components:** CSS-in-JS (if using React)

---

**End of Design Document**
