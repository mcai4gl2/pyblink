# Blink Protocol Specification Files

This directory contains the Blink Protocol beta4 specification documents in both PDF and text formats.

## Available Specifications

All specifications are available in both PDF (original) and TXT (extracted) formats:

### Core Specification
- **BlinkSpec-beta4.pdf / .txt** (44KB text)
  - Main Blink protocol specification
  - Schema language definition
  - Core concepts and data types
  - Compact binary format

### Format Specifications

- **BlinkTagSpec-beta4.pdf / .txt** (21KB text)
  - Human-readable tag format
  - Syntax: `@Type|field=value|field=value`
  - Escaping rules and grammar
  - Suitable for testing and logging

- **BlinkJsonSpec-beta4.pdf / .txt** (9KB text)
  - JSON mapping specification
  - Message structure with `$type` property
  - Decimal and floating-point handling
  - Stream wrapper arrays

- **BlinkXmlSpec-beta4.pdf / .txt** (11KB text)
  - XML mapping specification
  - Namespace handling
  - Binary data encoding
  - Stream root element structure

- **BlinkNativeSpec-beta4.pdf / .txt** (24KB text)
  - Native Binary format specification
  - Fixed-width fields with predictable offsets
  - Little-endian byte order
  - Optimized for speed over size

### Schema Exchange
- **BlinkSchemaExchangeSpec-beta4.pdf / .txt** (10KB text)
  - Dynamic schema exchange protocol
  - Reserved type IDs (16000-16383)
  - Schema transport messages
  - Runtime schema updates

## Text Extraction

All text files were extracted from PDFs using pypdf for easy reference and searching:

```python
import pypdf
reader = pypdf.PdfReader('BlinkSpec-beta4.pdf')
text = '\n'.join(page.extract_text() for page in reader.pages)
```

## Usage

The text files are useful for:
- Quick reference without opening PDFs
- Text searching and grep operations
- Copy-pasting examples
- Integration with development tools
- Documentation generation

## Version

All specifications are **beta4** version dated 2013-06-05 (or 2013-06-14 for Tag spec).

## Copyright

Copyright © Pantor Engineering AB, All rights reserved

## References

Official Blink Protocol website: http://blinkprotocol.org/
