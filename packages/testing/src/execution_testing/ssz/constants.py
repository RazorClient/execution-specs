"""SSZ size limits and byte-vector aliases for the REST+SSZ Engine API."""

from remerkleable.byte_arrays import ByteVector

# Payload / envelope limits.
MAX_BYTES_PER_TX = 2**30
MAX_TXS_PER_PAYLOAD = 2**20
MAX_WITHDRAWALS_PER_PAYLOAD = 2**4
BYTES_PER_LOGS_BLOOM = 256
MAX_EXTRA_DATA_BYTES = 2**5
MAX_BAL_BYTES = MAX_BYTES_PER_TX
MAX_EXECUTION_REQUESTS_PER_PAYLOAD = 2**8
MAX_BYTES_PER_EXECUTION_REQUEST = MAX_BYTES_PER_TX

# Blob / cell limits
MAX_BLOB_COMMITMENTS_PER_BLOCK = 2**12
FIELD_ELEMENTS_PER_BLOB = 4096
BYTES_PER_FIELD_ELEMENT = 32
BYTES_PER_BLOB = FIELD_ELEMENTS_PER_BLOB * BYTES_PER_FIELD_ELEMENT
CELLS_PER_EXT_BLOB = 128
FIELD_ELEMENTS_PER_CELL = 64
BYTES_PER_CELL = FIELD_ELEMENTS_PER_CELL * BYTES_PER_FIELD_ELEMENT

# Blob-pool / bodies.
MAX_VERSIONED_HASHES_PER_REQUEST = 128
MAX_BLOBS_REQUEST = MAX_VERSIONED_HASHES_PER_REQUEST
MAX_BODIES_REQUEST = 2**5

# Status / error limits.
MAX_ERROR_BYTES = 1024

# Identity / capabilities limits.
MAX_CLIENT_CODE_LENGTH = 2
MAX_CLIENT_NAME_LENGTH = 64
MAX_CLIENT_VERSION_LENGTH = 64
MAX_CLIENT_VERSIONS = 4
MAX_CAPABILITY_NAME_LENGTH = 64
MAX_CAPABILITIES = 64


class Hash32(ByteVector[32]):
    """A 32-byte hash (`Hash32`, `Root` and `Bytes32` share this layout)."""


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
    """An 8-byte value (e.g. `payload_id`)."""


class Bytes4(ByteVector[4]):
    """A 4-byte value (e.g. a client commit hash)."""


class Bytes48(ByteVector[48]):
    """A 48-byte value (KZG commitments and proofs)."""
