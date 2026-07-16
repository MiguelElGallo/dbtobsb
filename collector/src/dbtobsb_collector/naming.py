"""Fixed Unity Catalog object naming without executable user SQL."""

from __future__ import annotations


def quote_identifier(value: str) -> str:
    """Quote one nonempty Unity Catalog identifier component."""
    if not value or len(value) > 255 or any(ord(character) < 32 for character in value):
        raise ValueError("identifier must be a bounded nonempty printable value")
    return f"`{value.replace('`', '``')}`"


def qualify(catalog: str, schema: str, object_name: str) -> str:
    """Return one safely quoted three-part product object name."""
    return ".".join(
        (quote_identifier(catalog), quote_identifier(schema), quote_identifier(object_name))
    )
