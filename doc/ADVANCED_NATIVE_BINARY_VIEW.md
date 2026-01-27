# Advanced Native Binary View - Design Document

**Feature:** Interactive Binary Inspector with Side-by-Side Visualization  
**Date:** 2026-01-27  
**Status:** Design Phase

---

## Overview

An advanced binary inspection tool that provides a split-pane view showing the message structure (JSON/Tag format) alongside the raw binary representation with interactive highlighting and byte-level analysis.

### Key Features

1. **Split-Pane Layout**: Side-by-side view of message structure and binary data
2. **Color-Coded Sections**: Visual distinction between header, fields, and data
3. **Interactive Highlighting**: Click on JSON/Tag values to see corresponding bytes
4. **Byte-Level Analysis**: Detailed breakdown of selected bytes with type interpretation
5. **Format Toggle**: Switch between JSON and Tag format views
6. **Bidirectional Linking**: Click bytes to highlight corresponding field, or vice versa

---

## User Interface Design

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  Advanced Binary Inspector                          [Close]  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┬─────────────────────────────────┐  │
│  │ Message Structure   │ Binary Representation           │  │
│  │ [JSON] [Tag]        │ [Hex] [Decimal] [Binary]        │  │
│  ├─────────────────────┼─────────────────────────────────┤  │
│  │                     │                                 │  │
│  │ {                   │ 0000: 70 00 00 00 04 00 00 00  │  │
│  │   "$type": "Demo:   │       ^^^^^^^^ ^^^^^^^^         │  │
│  │     Company",       │       │ Size  │ Type ID         │  │
│  │   "CompanyName":    │                                 │  │
│  │     "TechCorp",     │ 0008: 00 00 00 00 08 54 65 63  │  │
│  │   "CEO": {          │       ^^^^^^^^    ^^^^^^^^^^^^  │  │
│  │     "Name": "Alice",│       │ Ext Off │ "TechCorp"    │  │
│  │     "Age": 45,      │                                 │  │
│  │     ...             │ 0010: 68 43 6F 72 70 05 41 6C  │  │
│  │   }                 │       ^^^^^^^^^^    ^^^^^^^^^^  │  │
│  │ }                   │       "hCorp"       "Alice"     │  │
│  │                     │                                 │  │
│  └─────────────────────┴─────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Byte Analysis Panel                                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Selected: Bytes 0-3 (Message Size)                    │  │
│  │ Hex:      70 00 00 00                                 │  │
│  │ Decimal:  112                                         │  │
│  │ Binary:   01110000 00000000 00000000 00000000         │  │
│  │ Type:     u32 (little-endian)                         │  │
│  │ Value:    112 bytes                                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Color Coding Scheme

**Binary Representation Colors:**
- **Header (Size, Type ID, Extension Offset)**: `bg-blue-100 text-blue-900`
- **Field Names/Indices**: `bg-purple-100 text-purple-900`
- **String Values**: `bg-green-100 text-green-900`
- **Numeric Values**: `bg-yellow-100 text-yellow-900`
- **Nested Objects**: `bg-pink-100 text-pink-900`
- **Selected/Hovered**: `bg-orange-200 border-2 border-orange-500`

**Message Structure Colors:**
- **Field Names**: `text-blue-700 font-semibold`
- **String Values**: `text-green-700`
- **Numeric Values**: `text-yellow-700`
- **Type Names**: `text-purple-700`
- **Selected**: `bg-orange-100 border-l-4 border-orange-500`

---

## Data Structure

### Binary Section Metadata

```typescript
interface BinarySection {
  id: string;                    // Unique identifier
  type: 'header' | 'field-name' | 'field-value' | 'nested';
  startOffset: number;           // Byte offset in binary data
  endOffset: number;             // End byte offset (exclusive)
  label: string;                 // Human-readable label
  fieldPath?: string;            // JSON path (e.g., "CEO.Name")
  dataType?: string;             // Data type (u32, string, etc.)
  rawValue?: string;             // Raw hex bytes
  interpretedValue?: string;     // Interpreted value
  color: string;                 // Tailwind color class
}

interface MessageField {
  path: string;                  // JSON path
  name: string;                  // Field name
  value: any;                    // Field value
  type: string;                  // Data type
  binarySection?: BinarySection; // Link to binary section
  children?: MessageField[];     // Nested fields
}
```

### Backend API Enhancement

New endpoint: `POST /api/analyze-binary`

**Request:**
```json
{
  "schema": "namespace Demo...",
  "binary_hex": "70000000...",
  "format": "native"
}
```

**Response:**
```json
{
  "success": true,
  "sections": [
    {
      "id": "header-size",
      "type": "header",
      "startOffset": 0,
      "endOffset": 4,
      "label": "Message Size",
      "dataType": "u32",
      "rawValue": "70000000",
      "interpretedValue": "112 bytes",
      "color": "blue"
    },
    {
      "id": "field-companyname",
      "type": "field-value",
      "startOffset": 12,
      "endOffset": 20,
      "label": "CompanyName",
      "fieldPath": "CompanyName",
      "dataType": "string",
      "rawValue": "5465636843...",
      "interpretedValue": "TechCorp",
      "color": "green"
    }
    // ... more sections
  ],
  "fields": [
    {
      "path": "CompanyName",
      "name": "CompanyName",
      "value": "TechCorp",
      "type": "string",
      "binarySectionId": "field-companyname"
    }
    // ... more fields
  ]
}
```

---

## Implementation Phases

### Phase 0: Quick Enhancements to Current Binary Viewer (Week 0 - 2-3 days) ✅ COMPLETE

**Goal:** Improve the existing `BinaryViewer.tsx` with immediate usability enhancements

**Tasks:**
- [x] Add byte-level hover tooltips showing offset, value, and ASCII
- [x] Implement click-to-select individual bytes with visual highlight
- [x] Add byte range selection (click and drag)
- [x] Show selected byte details in an info panel
- [x] Improve visual separation between hex bytes (grouping by 4 or 8)
- [x] Add byte position indicators (every 8 or 16 bytes)
- [x] Implement copy selected bytes functionality
- [x] Add search/find functionality for hex patterns
- [x] Improve color contrast and readability
- [ ] Add keyboard navigation (arrow keys to move between bytes) - Deferred to Phase 6

**Features:**
- **Hover Tooltips**: Show byte offset, hex value, decimal value, and ASCII character
- **Byte Selection**: Click to select single byte, drag to select range
- **Selection Info Panel**: Display details about selected bytes (hex, decimal, binary, ASCII)
- **Visual Grouping**: Group bytes by 4 or 8 for easier reading
- **Position Markers**: Add visual markers every 8/16 bytes
- **Copy Selection**: Copy selected bytes as hex string
- **Search**: Find specific hex patterns in the binary data
- **Keyboard Nav**: Use arrow keys to navigate between bytes

**UI Enhancements:**
```
┌─────────────────────────────────────────────────────────┐
│  Native Binary                          [Copy] [Download] │
├─────────────────────────────────────────────────────────┤
│  [Hex View] [Decoded View]                               │
├─────────────────────────────────────────────────────────┤
│  Hex View:                                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 0000: 70 00 00 00 │ 04 00 00 00 │ 00 00 00 00  │    │
│  │       ^^^^^^^^^^   (hover shows tooltip)         │    │
│  │ 0008: 08 54 65 63 │ 68 43 6F 72 │ 70 05 41 6C  │    │
│  │          ^^^^^^^^^ (selected range highlighted)  │    │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  Selection Info:                                         │
│  Bytes 9-16 (8 bytes)                                   │
│  Hex:     54 65 63 68 43 6F 72 70                       │
│  Decimal: 84 101 99 104 67 111 114 112                  │
│  ASCII:   TechCorp                                       │
│  [Copy Hex] [Copy ASCII]                                │
└─────────────────────────────────────────────────────────┘
```

**Deliverables:**
- Enhanced `BinaryViewer.tsx` with interactive features
- `ByteSelectionPanel.tsx` component for showing selection details
- Improved UX for binary inspection
- Foundation for Phase 1 advanced features

**Success Criteria:**
- Users can hover over bytes to see details
- Users can select byte ranges with mouse
- Selection info panel shows accurate data
- Visual grouping improves readability
- Search finds hex patterns correctly
- Keyboard navigation works smoothly

**Technical Notes:**
- Use React state for selection tracking
- Implement efficient re-rendering for hover effects
- Add debouncing for search functionality
- Use CSS for visual grouping and highlighting

---

### Phase 1: Backend Binary Analysis Service (Week 1)

**Goal:** Create backend service to parse binary data and generate section metadata

**Tasks:**
- [ ] Create `backend/app/services/binary_analyzer.py`
- [ ] Implement Native Binary parser with offset tracking
- [ ] Generate section metadata for header, fields, and values
- [ ] Map binary sections to JSON field paths
- [ ] Create `/api/analyze-binary` endpoint
- [ ] Add comprehensive tests

**Deliverables:**
- Binary analysis service with offset tracking
- API endpoint returning section metadata
- Unit tests for various message types

**Success Criteria:**
- Can parse any valid Native Binary message
- Correctly identifies all sections with byte offsets
- Maps sections to JSON field paths accurately

---

### Phase 2: Frontend Component Structure (Week 2)

**Goal:** Build the basic UI components and layout

**Tasks:**
- [ ] Create `AdvancedBinaryView.tsx` main component
- [ ] Create `MessageStructurePane.tsx` (left pane)
- [ ] Create `BinaryHexPane.tsx` (right pane)
- [ ] Create `ByteAnalysisPanel.tsx` (bottom panel)
- [ ] Implement split-pane layout with resizable divider
- [ ] Add format toggle (JSON/Tag)
- [ ] Add view mode toggle (Hex/Decimal/Binary)

**Component Hierarchy:**
```
AdvancedBinaryView
├── Header (title, close button, format toggles)
├── SplitPane
│   ├── MessageStructurePane
│   │   ├── FormatToggle (JSON/Tag)
│   │   └── StructureTree
│   └── BinaryHexPane
│       ├── ViewModeToggle (Hex/Decimal/Binary)
│       └── HexGrid
└── ByteAnalysisPanel
    └── SelectedByteDetails
```

**Deliverables:**
- Basic component structure
- Split-pane layout
- Format and view mode toggles

**Success Criteria:**
- Layout renders correctly
- Toggles switch between formats/views
- Components are responsive

---

### Phase 3: Color Coding & Section Rendering (Week 3)

**Goal:** Implement color-coded binary sections and message structure

**Tasks:**
- [ ] Implement color coding for binary sections
- [ ] Render hex bytes with section-based colors
- [ ] Implement JSON syntax highlighting
- [ ] Implement Tag format syntax highlighting
- [ ] Add section labels and annotations
- [ ] Add hover effects showing section info

**Features:**
- Color-coded hex bytes by section type
- Syntax-highlighted JSON/Tag display
- Hover tooltips showing section details
- Visual grouping of related bytes

**Deliverables:**
- Color-coded binary view
- Syntax-highlighted message structure
- Interactive hover effects

**Success Criteria:**
- Each section has distinct color
- Colors are consistent and readable
- Hover shows relevant information

---

### Phase 4: Interactive Highlighting (Week 4)

**Goal:** Implement bidirectional click-to-highlight functionality

**Tasks:**
- [ ] Implement click handler on JSON/Tag fields
- [ ] Highlight corresponding binary sections on field click
- [ ] Implement click handler on binary bytes
- [ ] Highlight corresponding JSON/Tag field on byte click
- [ ] Add smooth scroll-to-view for highlighted sections
- [ ] Implement multi-byte selection in hex view
- [ ] Add keyboard navigation (arrow keys, tab)

**Interaction Flow:**
1. User clicks on JSON field "CompanyName": "TechCorp"
2. Corresponding bytes in hex view highlight in orange
3. Hex view scrolls to show highlighted bytes
4. Byte analysis panel updates with byte details

**Deliverables:**
- Click-to-highlight in both directions
- Smooth scrolling to highlighted sections
- Keyboard navigation support

**Success Criteria:**
- Clicking field highlights correct bytes
- Clicking bytes highlights correct field
- Highlighting is visually clear
- Scrolling is smooth and accurate

---

### Phase 5: Byte Analysis Panel (Week 5)

**Goal:** Implement detailed byte-level analysis display

**Tasks:**
- [ ] Display selected byte range
- [ ] Show hex, decimal, and binary representations
- [ ] Interpret bytes based on data type
- [ ] Add endianness toggle (little/big)
- [ ] Show string interpretation for byte sequences
- [ ] Add copy-to-clipboard for byte values
- [ ] Display bit-level breakdown for flags/enums

**Analysis Features:**
- **Numeric Types**: Show as decimal, hex, binary
- **Strings**: Show as UTF-8 text with escape sequences
- **Timestamps**: Show as human-readable date/time
- **Enums**: Show enum name and value
- **Booleans**: Show as true/false
- **Binary**: Show as base64

**Deliverables:**
- Comprehensive byte analysis panel
- Type-aware interpretation
- Multiple representation formats

**Success Criteria:**
- Correctly interprets all data types
- Shows multiple representations
- Provides useful debugging information

---

### Phase 6: Advanced Features (Week 6)

**Goal:** Add advanced functionality and polish

**Tasks:**
- [ ] Add search functionality (find bytes or field names)
- [ ] Implement byte range selection with drag
- [ ] Add export functionality (selected bytes as hex/base64)
- [ ] Add diff view (compare two binary messages)
- [ ] Implement bookmarks for important byte offsets
- [ ] Add annotations (user notes on specific bytes)
- [ ] Performance optimization for large messages
- [ ] Add keyboard shortcuts reference

**Advanced Features:**
- **Search**: Find specific byte patterns or field names
- **Byte Selection**: Drag to select byte ranges
- **Export**: Export selected bytes in various formats
- **Diff View**: Side-by-side comparison of two messages
- **Bookmarks**: Save important byte offsets
- **Annotations**: Add notes to specific byte ranges

**Deliverables:**
- Search functionality
- Byte range selection
- Export and diff features
- Performance optimizations

**Success Criteria:**
- Search finds all matches
- Selection works smoothly
- Export produces correct output
- Performance is acceptable for 10KB+ messages

---

## Technical Specifications

### Performance Considerations

**Large Message Handling:**
- Virtual scrolling for hex view (only render visible bytes)
- Lazy loading of nested structures
- Debounced highlighting updates
- Memoized section calculations

**Optimization Targets:**
- Render 100KB message in < 500ms
- Highlight update in < 100ms
- Smooth scrolling at 60fps

### Accessibility

- Keyboard navigation for all interactions
- ARIA labels for screen readers
- High contrast mode support
- Focus indicators for keyboard users

### Browser Compatibility

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Mobile: Read-only view (no editing)

---

## User Stories

### Story 1: Understanding Binary Structure
**As a** developer learning the Blink protocol  
**I want to** see how my message is encoded in binary  
**So that** I can understand the binary format specification

**Acceptance Criteria:**
- Can see color-coded sections in hex view
- Can click on JSON field to see its binary representation
- Can see byte offsets and data types

### Story 2: Debugging Message Issues
**As a** developer debugging a message parsing error  
**I want to** inspect specific byte ranges and their interpretation  
**So that** I can identify where the encoding went wrong

**Acceptance Criteria:**
- Can select byte ranges and see their interpretation
- Can switch between hex, decimal, and binary views
- Can see detailed analysis of selected bytes

### Story 3: Comparing Message Formats
**As a** developer comparing Compact vs Native Binary  
**I want to** see the same message in both formats side-by-side  
**So that** I can understand the trade-offs

**Acceptance Criteria:**
- Can open multiple binary views
- Can compare byte layouts
- Can see size differences highlighted

---

## Open Questions

1. **Should we support Compact Binary in addition to Native Binary?**
   - Native Binary is easier to parse due to fixed offsets
   - Compact Binary would require more complex analysis
   - **Decision**: Start with Native Binary, add Compact later if needed

2. **How should we handle very large messages (>1MB)?**
   - Virtual scrolling is essential
   - Consider pagination or lazy loading
   - **Decision**: Implement virtual scrolling from the start

3. **Should the advanced view be a modal or a separate page?**
   - Modal: Easier to compare with main view
   - Separate page: More screen space
   - **Decision**: Modal with maximize option

4. **How should we persist user preferences (color scheme, view mode)?**
   - localStorage for client-side persistence
   - **Decision**: Use localStorage, no backend needed

---

## Dependencies

**Frontend:**
- React 18+
- TypeScript 4.9+
- Tailwind CSS 3.4+
- react-split-pane (for resizable layout)
- react-window (for virtual scrolling)

**Backend:**
- FastAPI (existing)
- Python 3.11+ (existing)
- PyBlink codec library (existing)

---

## Success Metrics

**Usability:**
- Users can understand binary structure within 5 minutes
- 90% of users find the feature helpful for debugging

**Performance:**
- Renders 100KB message in < 500ms
- Highlighting updates in < 100ms
- No lag during scrolling

**Adoption:**
- 50% of users try the advanced view
- 25% of users use it regularly

---

## Future Enhancements (Post-MVP)

1. **Binary Editing**: Allow users to modify bytes and see updated message
2. **Template Library**: Save and load byte patterns for common structures
3. **Protocol Analyzer**: Detect and highlight protocol violations
4. **Performance Profiler**: Show encoding/decoding performance metrics
5. **Export to C/C++**: Generate struct definitions from binary layout
6. **Collaborative Annotations**: Share byte-level notes with team

---

## Conclusion

The Advanced Native Binary View will be a powerful tool for developers working with the Blink protocol. By providing interactive, color-coded visualization with bidirectional linking between message structure and binary representation, it will significantly improve the debugging and learning experience.

**Estimated Total Effort:** 6 weeks (1 developer)  
**Priority:** Medium (Enhancement, not critical for MVP)  
**Risk Level:** Low (well-defined scope, existing infrastructure)

---

**Next Steps:**
1. Review and approve this design document
2. Create detailed task breakdown for Phase 1
3. Set up project tracking (GitHub issues or similar)
4. Begin Phase 1 implementation

**Document Version:** 1.0  
**Last Updated:** 2026-01-27  
**Author:** AI Assistant
