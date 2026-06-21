"""
SSZ (de)serialization for this package's containers.

Three representations of an SSZ value, each with an ``encode``/``decode`` pair
(except the one-way ``hash_tree_root``):

* **bytes**  -- the canonical SSZ wire encoding (``encode_bytes`` /
  ``decode_bytes``); thin wrappers over remerkleable's own methods.
* **value**  -- the consensus-spec canonical value: a tree of plain Python
  primitives (``dict`` / ``list`` / ``"0x..."`` / decimal-``str`` / ``bool``),
  the form written to ``value.yaml`` (``encode_value`` / ``decode_value``).
* **root**   -- the 32-byte ``hash_tree_root``.

``encode_value``/``decode_value`` (formerly ``to_json``/``from_json``) never
produced JSON -- only this serializer-agnostic primitive tree, which YAML and
JSON both serialize.
"""

from typing import Any, Type, TypeVar

from remerkleable.basic import boolean, uint
from remerkleable.bitfields import Bitlist, Bitvector
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container, List
from remerkleable.core import View

ViewT = TypeVar("ViewT", bound=View)


def encode_bytes(value: View) -> bytes:
    """Serialize an SSZ value to its canonical byte encoding."""
    return value.encode_bytes()


def decode_bytes(ssz_type: Type[ViewT], data: bytes) -> ViewT:
    """Deserialize ``data`` into an SSZ value of ``ssz_type``."""
    return ssz_type.decode_bytes(data)


def hash_tree_root(value: View) -> bytes:
    """Return the 32-byte SSZ `hash_tree_root` of an SSZ value."""
    return bytes(value.hash_tree_root())


def encode_value(value: Any) -> Any:
    """
    Encode an SSZ value to its canonical value tree (plain primitives).
    """
    if isinstance(value, Container):
        return {
            field: encode_value(getattr(value, field))
            for field in type(value).fields()
        }
    if isinstance(value, (Bitvector, Bitlist)):
        return "0x" + value.encode_bytes().hex()
    if isinstance(value, List):
        return [encode_value(element) for element in value]
    if isinstance(value, (ByteVector, ByteList)):
        return "0x" + bytes(value).hex()
    if isinstance(value, boolean):
        return bool(value)
    if isinstance(value, uint):
        return str(int(value))
    raise TypeError(f"unsupported SSZ value type: {type(value)!r}")


def decode_value(ssz_type: Any, obj: Any) -> Any:
    """
    Decode a canonical value tree into an SSZ value of ``ssz_type``.
    """
    if issubclass(ssz_type, Container):
        fields = ssz_type.fields()
        return ssz_type(
            **{
                field: decode_value(field_type, obj[field])
                for field, field_type in fields.items()
            }
        )
    if issubclass(ssz_type, (Bitvector, Bitlist)):
        return ssz_type.decode_bytes(bytes.fromhex(_strip_0x(obj)))
    if issubclass(ssz_type, List):
        element_type = ssz_type.element_cls()
        return ssz_type(*(decode_value(element_type, item) for item in obj))
    if issubclass(ssz_type, (ByteVector, ByteList)):
        return ssz_type(bytes.fromhex(_strip_0x(obj)))
    if issubclass(ssz_type, boolean):
        return ssz_type(bool(obj))
    if issubclass(ssz_type, uint):
        return ssz_type(int(obj))
    raise TypeError(f"unsupported SSZ type: {ssz_type!r}")


def _strip_0x(value: str) -> str:
    """Return ``value`` without a leading ``0x`` prefix."""
    return value[2:] if value.startswith("0x") else value
