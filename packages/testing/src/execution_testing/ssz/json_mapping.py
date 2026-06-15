"""Consensus-spec canonical JSON mapping for SSZ values."""

from typing import Any

from remerkleable.basic import boolean, uint
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container, List


def to_json(value: Any) -> Any:
    """
    Convert an SSZ value to its canonical JSON representation.
    """
    if isinstance(value, Container):
        return {
            field: to_json(getattr(value, field))
            for field in type(value).fields()
        }
    if isinstance(value, List):
        return [to_json(element) for element in value]
    if isinstance(value, (ByteVector, ByteList)):
        return "0x" + bytes(value).hex()
    if isinstance(value, boolean):
        return bool(value)
    if isinstance(value, uint):
        return str(int(value))
    raise TypeError(f"unsupported SSZ value type: {type(value)!r}")


def from_json(ssz_type: Any, obj: Any) -> Any:
    """
    Parse consensus-spec canonical JSON into an SSZ value of ``ssz_type``.
    """
    if issubclass(ssz_type, Container):
        fields = ssz_type.fields()
        return ssz_type(
            **{
                field: from_json(field_type, obj[field])
                for field, field_type in fields.items()
            }
        )
    if issubclass(ssz_type, List):
        element_type = ssz_type.element_cls()
        return ssz_type(*(from_json(element_type, item) for item in obj))
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
