"""
Deterministic random SSZ value generation for static test vectors.
"""

import hashlib
from enum import Enum
from random import Random
from typing import Any

from remerkleable.basic import boolean, uint
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container, List
from remerkleable.core import View

_MODE_NAMES = (
    "random",
    "zero",
    "max",
    "nil_count",
    "one_count",
    "max_count",
)


class RandomizationMode(Enum):
    """
    How a value's scalar and collection fields are filled.
    Mirrors the consensus-specs ``RandomizationMode``.
    """

    mode_random = 0
    mode_zero = 1
    mode_max = 2
    mode_nil_count = 3
    mode_one_count = 4
    mode_max_count = 5

    def is_changing(self) -> bool:
        """
        Return whether the mode yields varying values across cases.

        True for ``random``, ``one_count`` and ``max_count`` -- those randomize
        content, so several cases are worth generating; the rest are fully
        determined by a single case.
        """
        return self in (
            RandomizationMode.mode_random,
            RandomizationMode.mode_one_count,
            RandomizationMode.mode_max_count,
        )

    def to_name(self) -> str:
        """Return the canonical short name for this mode."""
        return _MODE_NAMES[self.value]


def deterministic_seed(*parts: object) -> int:
    """
    Return a stable integer seed derived from ``parts``.
    Uses SHA-256 over the slash-joined string parts.
    """
    joined = "/".join(str(part) for part in parts)
    digest = hashlib.sha256(joined.encode("utf-8")).digest()
    return int.from_bytes(digest, "big")


def get_random_ssz_object(
    rng: Random,
    typ: Any,
    max_bytes_length: int,
    max_list_length: int,
    mode: RandomizationMode,
    chaos: bool,
) -> View:
    """
    Build a value of ``typ`` filled with random data per ``mode``.
    """
    if chaos:
        mode = rng.choice(list(RandomizationMode))
    if issubclass(typ, ByteList):
        if mode == RandomizationMode.mode_nil_count:
            return typ(b"")
        elif mode == RandomizationMode.mode_max_count:
            return typ(_random_bytes(rng, min(max_bytes_length, typ.limit())))
        elif mode == RandomizationMode.mode_one_count:
            return typ(_random_bytes(rng, min(1, typ.limit())))
        elif mode == RandomizationMode.mode_zero:
            return typ(b"\x00" * min(1, typ.limit()))
        elif mode == RandomizationMode.mode_max:
            return typ(b"\xff" * min(1, typ.limit()))
        else:
            return typ(
                _random_bytes(
                    rng, rng.randint(0, min(max_bytes_length, typ.limit()))
                )
            )
    if issubclass(typ, ByteVector):
        # Byte vectors are fixed length; no max-bytes cap applies.
        if mode == RandomizationMode.mode_zero:
            return typ(b"\x00" * typ.type_byte_length())
        elif mode == RandomizationMode.mode_max:
            return typ(b"\xff" * typ.type_byte_length())
        else:
            return typ(_random_bytes(rng, typ.type_byte_length()))
    elif issubclass(typ, (boolean, uint)):
        if mode == RandomizationMode.mode_zero:
            return _min_basic_value(typ)
        elif mode == RandomizationMode.mode_max:
            return _max_basic_value(typ)
        else:
            return _random_basic_value(rng, typ)
    elif issubclass(typ, List):
        limit = max_list_length
        if typ.limit() < limit:
            limit = typ.limit()
        length = rng.randint(0, limit)
        if mode == RandomizationMode.mode_one_count:
            length = 1
        elif mode == RandomizationMode.mode_max_count:
            length = limit
        elif mode == RandomizationMode.mode_nil_count:
            length = 0
        element_type = typ.element_cls()
        max_list_length = 1 << (max_list_length.bit_length() >> 1)
        return typ(
            get_random_ssz_object(
                rng,
                element_type,
                max_bytes_length,
                max_list_length,
                mode,
                chaos,
            )
            for _ in range(length)
        )
    elif issubclass(typ, Container):
        return typ(
            **{
                field_name: get_random_ssz_object(
                    rng,
                    field_type,
                    max_bytes_length,
                    max_list_length,
                    mode,
                    chaos,
                )
                for field_name, field_type in typ.fields().items()
            }
        )
    else:
        raise TypeError(f"unsupported SSZ type: {typ!r}")


def _random_bytes(rng: Random, length: int) -> bytes:
    """Return ``length`` random bytes."""
    return bytes(rng.getrandbits(8) for _ in range(length))


def _random_basic_value(rng: Random, typ: Any) -> View:
    """Return a random ``boolean`` or ``uint`` value."""
    if issubclass(typ, boolean):
        return typ(rng.choice((True, False)))
    if issubclass(typ, uint):
        return typ(rng.randint(0, 2 ** (typ.type_byte_length() * 8) - 1))
    raise TypeError(f"not a basic type: {typ!r}")


def _min_basic_value(typ: Any) -> View:
    """Return the minimum (zero / False) value of a basic type."""
    if issubclass(typ, boolean):
        return typ(False)
    if issubclass(typ, uint):
        return typ(0)
    raise TypeError(f"not a basic type: {typ!r}")


def _max_basic_value(typ: Any) -> View:
    """Return the maximum (all-ones / True) value of a basic type."""
    if issubclass(typ, boolean):
        return typ(True)
    if issubclass(typ, uint):
        return typ(2 ** (typ.type_byte_length() * 8) - 1)
    raise TypeError(f"not a basic type: {typ!r}")
