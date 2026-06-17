"""Byte-vector type aliases for the REST+SSZ Engine API."""

from remerkleable.byte_arrays import ByteVector

from .constants import BYTES_PER_LOGS_BLOOM


class Hash32(ByteVector[32]):
    """A 32-byte hash."""


class Bytes32(ByteVector[32]):
    """A 32-byte fixed vector."""


class Root(ByteVector[32]):
    """A 32-byte merkle root."""


class Address(ByteVector[20]):
    """A 20-byte execution-layer address."""


class Bloom(ByteVector[BYTES_PER_LOGS_BLOOM]):
    """A 256-byte logs bloom filter."""


class VersionedHash(ByteVector[32]):
    """An EIP-4844 versioned blob hash."""


class Bytes8(ByteVector[8]):
    """An 8-byte value."""


class Bytes4(ByteVector[4]):
    """A 4-byte value."""


class Bytes48(ByteVector[48]):
    """A 48-byte value."""
