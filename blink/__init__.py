"""
Top-level package for the Blink Python implementation.

The modules follow the layout described in SPEC_ENHANCED.md and aim
to provide a clean public API surface for schema parsing, runtime
values, and binary codecs.
"""

from .runtime.values import DecimalValue, Message, StaticGroupValue
from .runtime.registry import TypeRegistry
from .schema.model import QName

__all__ = [
    "DecimalValue",
    "Message",
    "QName",
    "StaticGroupValue",
    "TypeRegistry",
]
