# Blink Message Playground - User Guide

## Welcome! 🎉

The **Blink Message Playground** is an interactive web application for working with Blink protocol messages. Convert messages between all supported formats, validate schemas, and share your work with others.

## Quick Start

### 1. Define Your Schema

In the **Schema Definition** panel (top-left), write your Blink schema:

```
namespace Demo

Person/1 -> string Name, u32 Age
```

Click **Validate Schema** to check for errors.

### 2. Enter Your Message

In the **Input Message** panel (bottom-left):
- Select your input format from the dropdown (JSON, Tag, XML, Compact Binary, Native Binary)
- Enter your message data

### 3. Convert

Click the **Convert** button (or press `Ctrl+Enter`) to convert your message to all formats.

### 4. View Results

The **Output Formats** panel (right side) shows your message in all 5 formats:
- **Tag Format**: Human-readable text format
- **JSON Format**: JSON representation
- **XML Format**: XML representation
- **Compact Binary**: Efficient binary encoding (with hex viewer)
- **Native Binary**: Fixed-width binary format (with hex viewer)

## Features

### 📚 Example Library

Click the **"📚 Load Example..."** dropdown in the header to load predefined examples:
- **Simple Person**: Basic example with primitive types
- **Nested Company**: Demonstrates nested classes and inheritance
- **Trading Order**: Financial trading order example
- **Dynamic Group**: Shows polymorphic fields
- **Sequence Example**: Demonstrates arrays
- **Optional Fields**: Shows nullable fields

### ⌨️ Keyboard Shortcuts

- **`Ctrl+Enter`** (or `Cmd+Enter` on Mac): Convert message
- **`Ctrl+S`** (or `Cmd+S` on Mac): Open Save & Share dialog
- **`Escape`**: Close modal dialogs

### 💾 Auto-Save

Your work is automatically saved to your browser's local storage as you type. If you close the browser and come back, your last session will be restored.

### 🔗 Save & Share

Click the **"Save & Share"** button to:
1. Give your playground an optional title and description
2. Get a shareable URL that lasts for 30 days
3. Share the link with colleagues or save it for later

### 🔍 Binary Viewers

For Compact Binary and Native Binary formats, use the tabbed interface:
- **Hex View**: See the raw bytes with memory offsets and ASCII preview
- **Decoded View**: See the message structure broken down field-by-field

Features:
- **Copy**: Copy hex bytes to clipboard
- **Download**: Save as `.bin` file
- **Field Breakdown**: Expandable field details

### 📋 Copy to Clipboard

Every output format has a **Copy** button for quick copying to clipboard.

## Blink Schema Syntax

### Basic Types

```
namespace MyApp

# Primitive types
Person/1 -> string Name, u32 Age, bool Active
```

**Supported types:**
- Integers: `i8`, `i16`, `i32`, `i64`, `u8`, `u16`, `u32`, `u64`
- Floating point: `f32`, `f64`, `decimal`
- Other: `bool`, `string`, `binary`, `timestamp`

### Nested Classes

```
Address/1 -> string Street, string City

Person/2 -> string Name, Address HomeAddress
```

### Inheritance (Subclasses)

```
Employee/1 -> string Name, u32 Age

Manager/2 : Employee -> string Department, u32 TeamSize
```

The `:` operator indicates inheritance. `Manager` inherits all fields from `Employee`.

### Optional Fields

```
User/1 -> string Username, string? MiddleName, u32? Age
```

The `?` suffix makes a field optional (nullable).

### Sequences (Arrays)

```
Student/1 -> string Name, u32[] Grades, string[] Courses
```

The `[]` suffix creates a sequence (array) of that type.

### Dynamic Groups

```
Shape/1 -> string Color

Rect/2 : Shape -> u32 Width, u32 Height

Frame/3 -> Shape* Content
```

The `*` suffix creates a dynamic group field that can hold any subclass of `Shape`.

## Format Details

### Tag Format

Human-readable text format:
```
@Demo:Person|Name=Alice|Age=30
```

Nested objects use curly braces:
```
@Demo:Company|Name=TechCorp|CEO={Name=Alice,Age=45}
```

### JSON Format

Standard JSON with special `$type` field:
```json
{
  "$type": "Demo:Person",
  "Name": "Alice",
  "Age": 30
}
```

### XML Format

XML with Blink namespaces:
```xml
<ns0:Person xmlns:ns0="Demo">
  <Name>Alice</Name>
  <Age>30</Age>
</ns0:Person>
```

### Binary Formats

**Compact Binary**: Variable-length encoding, optimized for size
**Native Binary**: Fixed-width fields, optimized for speed

Both show:
- Hex dump with offsets
- Decoded message structure
- Field-by-field breakdown

## Tips & Tricks

1. **Start with Examples**: Use the Examples dropdown to learn Blink syntax
2. **Validate Often**: Click "Validate Schema" to catch errors early
3. **Use Keyboard Shortcuts**: `Ctrl+Enter` to convert is much faster than clicking
4. **Save Your Work**: Use "Save & Share" to create permanent links
5. **Explore Binary Formats**: Switch between Hex View and Decoded View to understand the binary structure

## Troubleshooting

### "Schema validation failed"
- Check for syntax errors in your schema
- Ensure all type IDs are unique
- Make sure namespace is defined

### "Conversion failed"
- Verify your input data matches the schema
- Check that the `$type` field (in JSON) matches your schema
- Ensure all required fields are present

### "Failed to connect to API server"
- Make sure the backend is running on `http://127.0.0.1:8000`
- Check your network connection
- Try refreshing the page

## Technical Details

### Data Retention

- **Saved Playgrounds**: 30 days
- **Auto-saved Drafts**: Stored in browser localStorage (indefinite, but browser-specific)

### Browser Support

- Chrome/Edge: ✅ Fully supported
- Firefox: ✅ Fully supported
- Safari: ✅ Fully supported
- IE11: ❌ Not supported

### Privacy

- All data is stored locally in your browser or on the server (for saved playgrounds)
- No analytics or tracking
- Saved playgrounds are accessible to anyone with the link

## Keyboard Reference

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` / `Cmd+Enter` | Convert message |
| `Ctrl+S` / `Cmd+S` | Open Save & Share dialog |
| `Escape` | Close modal |

## Getting Help

- **Schema Syntax**: See the Blink specification documentation
- **Examples**: Use the Examples dropdown to see working schemas
- **Issues**: Report bugs or request features on GitHub

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-23

Enjoy using the Blink Message Playground! 🚀
