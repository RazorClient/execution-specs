"""
SSZ container definitions for the REST+SSZ Engine API.
"""

from remerkleable.basic import boolean, uint8, uint64, uint256
from remerkleable.bitfields import Bitvector
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container, List

from .constants import (
    BYTES_PER_BLOB,
    BYTES_PER_CELL,
    CELLS_PER_EXT_BLOB,
    MAX_BAL_BYTES,
    MAX_BLOB_COMMITMENTS_PER_BLOCK,
    MAX_BLOBS_REQUEST,
    MAX_BODIES_REQUEST,
    MAX_BYTES_PER_EXECUTION_REQUEST,
    MAX_BYTES_PER_TX,
    MAX_CAPABILITIES,
    MAX_CAPABILITY_NAME_LENGTH,
    MAX_CLIENT_CODE_LENGTH,
    MAX_CLIENT_NAME_LENGTH,
    MAX_CLIENT_VERSION_LENGTH,
    MAX_CLIENT_VERSIONS,
    MAX_ERROR_BYTES,
    MAX_EXECUTION_REQUESTS_PER_PAYLOAD,
    MAX_EXTRA_DATA_BYTES,
    MAX_TXS_PER_PAYLOAD,
    MAX_WITHDRAWALS_PER_PAYLOAD,
)
from .ssz_types import (
    Address,
    Bloom,
    Bytes4,
    Bytes8,
    Bytes32,
    Bytes48,
    Hash32,
    Root,
    VersionedHash,
)


class Withdrawal(Container):
    """A validator withdrawal pushed into an execution payload."""

    index: uint64
    validator_index: uint64
    address: Address
    amount: uint64


class ExecutionPayloadParis(Container):
    """The Paris execution payload."""

    parent_hash: Hash32
    fee_recipient: Address
    state_root: Hash32
    receipts_root: Hash32
    logs_bloom: Bloom
    prev_randao: Bytes32
    block_number: uint64
    gas_limit: uint64
    gas_used: uint64
    timestamp: uint64
    extra_data: ByteList[MAX_EXTRA_DATA_BYTES]
    base_fee_per_gas: uint256
    block_hash: Hash32
    transactions: List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]


class ExecutionPayloadShanghai(Container):
    """The Shanghai execution payload."""

    parent_hash: Hash32
    fee_recipient: Address
    state_root: Hash32
    receipts_root: Hash32
    logs_bloom: Bloom
    prev_randao: Bytes32
    block_number: uint64
    gas_limit: uint64
    gas_used: uint64
    timestamp: uint64
    extra_data: ByteList[MAX_EXTRA_DATA_BYTES]
    base_fee_per_gas: uint256
    block_hash: Hash32
    transactions: List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]


class ExecutionPayloadCancun(Container):
    """The Cancun execution payload."""

    parent_hash: Hash32
    fee_recipient: Address
    state_root: Hash32
    receipts_root: Hash32
    logs_bloom: Bloom
    prev_randao: Bytes32
    block_number: uint64
    gas_limit: uint64
    gas_used: uint64
    timestamp: uint64
    extra_data: ByteList[MAX_EXTRA_DATA_BYTES]
    base_fee_per_gas: uint256
    block_hash: Hash32
    transactions: List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]
    blob_gas_used: uint64
    excess_blob_gas: uint64


class ExecutionPayloadPrague(Container):
    """The Prague execution payload."""

    parent_hash: Hash32
    fee_recipient: Address
    state_root: Hash32
    receipts_root: Hash32
    logs_bloom: Bloom
    prev_randao: Bytes32
    block_number: uint64
    gas_limit: uint64
    gas_used: uint64
    timestamp: uint64
    extra_data: ByteList[MAX_EXTRA_DATA_BYTES]
    base_fee_per_gas: uint256
    block_hash: Hash32
    transactions: List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]
    blob_gas_used: uint64
    excess_blob_gas: uint64


class ExecutionPayloadOsaka(Container):
    """The Osaka execution payload."""

    parent_hash: Hash32
    fee_recipient: Address
    state_root: Hash32
    receipts_root: Hash32
    logs_bloom: Bloom
    prev_randao: Bytes32
    block_number: uint64
    gas_limit: uint64
    gas_used: uint64
    timestamp: uint64
    extra_data: ByteList[MAX_EXTRA_DATA_BYTES]
    base_fee_per_gas: uint256
    block_hash: Hash32
    transactions: List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]
    blob_gas_used: uint64
    excess_blob_gas: uint64


class ExecutionPayloadAmsterdam(Container):
    """The Amsterdam execution payload."""

    parent_hash: Hash32
    fee_recipient: Address
    state_root: Hash32
    receipts_root: Hash32
    logs_bloom: Bloom
    prev_randao: Bytes32
    block_number: uint64
    gas_limit: uint64
    gas_used: uint64
    timestamp: uint64
    extra_data: ByteList[MAX_EXTRA_DATA_BYTES]
    base_fee_per_gas: uint256
    block_hash: Hash32
    transactions: List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]
    blob_gas_used: uint64
    excess_blob_gas: uint64
    block_access_list: ByteList[MAX_BAL_BYTES]
    slot_number: uint64


class ExecutionPayloadEnvelopeParis(Container):
    """The Paris `newPayload` envelope."""

    payload: ExecutionPayloadParis


class ExecutionPayloadEnvelopeShanghai(Container):
    """The Shanghai `newPayload` envelope."""

    payload: ExecutionPayloadShanghai


class ExecutionPayloadEnvelopeCancun(Container):
    """The Cancun `newPayload` envelope."""

    payload: ExecutionPayloadCancun
    parent_beacon_block_root: Root


class ExecutionPayloadEnvelopePrague(Container):
    """The Prague `newPayload` envelope."""

    payload: ExecutionPayloadPrague
    parent_beacon_block_root: Root
    execution_requests: List[
        ByteList[MAX_BYTES_PER_EXECUTION_REQUEST],
        MAX_EXECUTION_REQUESTS_PER_PAYLOAD,
    ]


class ExecutionPayloadEnvelopeOsaka(Container):
    """The Osaka `newPayload` envelope."""

    payload: ExecutionPayloadOsaka
    parent_beacon_block_root: Root
    execution_requests: List[
        ByteList[MAX_BYTES_PER_EXECUTION_REQUEST],
        MAX_EXECUTION_REQUESTS_PER_PAYLOAD,
    ]


class ExecutionPayloadEnvelopeAmsterdam(Container):
    """The Amsterdam `newPayload` envelope."""

    payload: ExecutionPayloadAmsterdam
    parent_beacon_block_root: Root
    execution_requests: List[
        ByteList[MAX_BYTES_PER_EXECUTION_REQUEST],
        MAX_EXECUTION_REQUESTS_PER_PAYLOAD,
    ]


class PayloadAttributesParis(Container):
    """The Paris payload attributes."""

    timestamp: uint64
    prev_randao: Bytes32
    suggested_fee_recipient: Address


class PayloadAttributesShanghai(Container):
    """The Shanghai payload attributes."""

    timestamp: uint64
    prev_randao: Bytes32
    suggested_fee_recipient: Address
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]


class PayloadAttributesCancun(Container):
    """The Cancun payload attributes."""

    timestamp: uint64
    prev_randao: Bytes32
    suggested_fee_recipient: Address
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]
    parent_beacon_block_root: Root


class PayloadAttributesPrague(Container):
    """The Prague payload attributes."""

    timestamp: uint64
    prev_randao: Bytes32
    suggested_fee_recipient: Address
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]
    parent_beacon_block_root: Root


class PayloadAttributesOsaka(Container):
    """The Osaka payload attributes."""

    timestamp: uint64
    prev_randao: Bytes32
    suggested_fee_recipient: Address
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]
    parent_beacon_block_root: Root


class PayloadAttributesAmsterdam(Container):
    """The Amsterdam payload attributes."""

    timestamp: uint64
    prev_randao: Bytes32
    suggested_fee_recipient: Address
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]
    parent_beacon_block_root: Root
    slot_number: uint64
    target_gas_limit: uint64


class ForkchoiceState(Container):
    """The forkchoice head/safe/finalized triple."""

    head_block_hash: Hash32
    safe_block_hash: Hash32
    finalized_block_hash: Hash32


class PayloadStatus(Container):
    """A newPayload/forkchoice status."""

    status: uint8
    latest_valid_hash: List[Hash32, 1]
    validation_error: List[ByteList[MAX_ERROR_BYTES], 1]


class ForkchoiceUpdateParis(Container):
    """The Paris forkchoice update."""

    forkchoice_state: ForkchoiceState
    payload_attributes: List[PayloadAttributesParis, 1]


class ForkchoiceUpdateShanghai(Container):
    """The Shanghai forkchoice update."""

    forkchoice_state: ForkchoiceState
    payload_attributes: List[PayloadAttributesShanghai, 1]


class ForkchoiceUpdateCancun(Container):
    """The Cancun forkchoice update."""

    forkchoice_state: ForkchoiceState
    payload_attributes: List[PayloadAttributesCancun, 1]


class ForkchoiceUpdatePrague(Container):
    """The Prague forkchoice update."""

    forkchoice_state: ForkchoiceState
    payload_attributes: List[PayloadAttributesPrague, 1]


class ForkchoiceUpdateOsaka(Container):
    """The Osaka forkchoice update."""

    forkchoice_state: ForkchoiceState
    payload_attributes: List[PayloadAttributesOsaka, 1]


class ForkchoiceUpdateAmsterdam(Container):
    """The Amsterdam forkchoice update."""

    forkchoice_state: ForkchoiceState
    payload_attributes: List[PayloadAttributesAmsterdam, 1]
    custody_columns: List[Bitvector[CELLS_PER_EXT_BLOB], 1]


class ForkchoiceUpdateResponse(Container):
    """The forkchoice response: a status and an optional payload id."""

    payload_status: PayloadStatus
    payload_id: List[Bytes8, 1]


class ExecutionPayloadBodyParis(Container):
    """The Paris execution payload body."""

    transactions: List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]


class ExecutionPayloadBodyShanghai(Container):
    """The Shanghai execution payload body."""

    transactions: List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]


class ExecutionPayloadBodyCancun(Container):
    """The Cancun execution payload body."""

    transactions: List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]


class ExecutionPayloadBodyPrague(Container):
    """The Prague execution payload body."""

    transactions: List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]


class ExecutionPayloadBodyOsaka(Container):
    """The Osaka execution payload body."""

    transactions: List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]


class ExecutionPayloadBodyAmsterdam(Container):
    """The Amsterdam execution payload body."""

    transactions: List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]
    withdrawals: List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]
    block_access_list: ByteList[MAX_BAL_BYTES]


class BlobsBundleV1(Container):
    """The Cancun blobs bundle."""

    commitments: List[Bytes48, MAX_BLOB_COMMITMENTS_PER_BLOCK]
    proofs: List[Bytes48, MAX_BLOB_COMMITMENTS_PER_BLOCK]
    blobs: List[ByteVector[BYTES_PER_BLOB], MAX_BLOB_COMMITMENTS_PER_BLOCK]


class BlobsBundleV2(Container):
    """The Osaka+ blobs bundle."""

    commitments: List[Bytes48, MAX_BLOB_COMMITMENTS_PER_BLOCK]
    proofs: List[Bytes48, MAX_BLOB_COMMITMENTS_PER_BLOCK * CELLS_PER_EXT_BLOB]
    blobs: List[ByteVector[BYTES_PER_BLOB], MAX_BLOB_COMMITMENTS_PER_BLOCK]


class BuiltPayloadParis(Container):
    """The Paris getPayload response."""

    payload: ExecutionPayloadParis
    block_value: uint256


# Should not have the should_override_builder field,wrong in spec pr 793
class BuiltPayloadShanghai(Container):
    """The Shanghai getPayload response."""

    payload: ExecutionPayloadShanghai
    block_value: uint256


class BuiltPayloadCancun(Container):
    """The Cancun getPayload response."""

    payload: ExecutionPayloadCancun
    block_value: uint256
    blobs_bundle: BlobsBundleV1
    should_override_builder: boolean


class BuiltPayloadPrague(Container):
    """The Prague getPayload response."""

    payload: ExecutionPayloadPrague
    block_value: uint256
    blobs_bundle: BlobsBundleV1
    execution_requests: List[
        ByteList[MAX_BYTES_PER_EXECUTION_REQUEST],
        MAX_EXECUTION_REQUESTS_PER_PAYLOAD,
    ]
    should_override_builder: boolean


class BuiltPayloadOsaka(Container):
    """The Osaka getPayload response."""

    payload: ExecutionPayloadOsaka
    block_value: uint256
    blobs_bundle: BlobsBundleV2
    execution_requests: List[
        ByteList[MAX_BYTES_PER_EXECUTION_REQUEST],
        MAX_EXECUTION_REQUESTS_PER_PAYLOAD,
    ]
    should_override_builder: boolean


class BuiltPayloadAmsterdam(Container):
    """The Amsterdam getPayload response."""

    payload: ExecutionPayloadAmsterdam
    block_value: uint256
    blobs_bundle: BlobsBundleV2
    execution_requests: List[
        ByteList[MAX_BYTES_PER_EXECUTION_REQUEST],
        MAX_EXECUTION_REQUESTS_PER_PAYLOAD,
    ]
    should_override_builder: boolean


class BlobAndProofV1(Container):
    """A whole blob with a single proof."""

    blob: ByteVector[BYTES_PER_BLOB]
    proof: Bytes48


class BlobAndProofV2(Container):
    """A whole blob with cell proofs."""

    blob: ByteVector[BYTES_PER_BLOB]
    proofs: List[Bytes48, CELLS_PER_EXT_BLOB]


class BlobCellsAndProofs(Container):
    """Cell-range blob contents for /blobs/v4 (cells/proofs optional)."""

    blob_cells: List[List[ByteVector[BYTES_PER_CELL], 1], CELLS_PER_EXT_BLOB]
    proofs: List[List[Bytes48, 1], CELLS_PER_EXT_BLOB]


class BodiesByHashRequest(Container):
    """The /bodies/hash request body."""

    block_hashes: List[Hash32, MAX_BODIES_REQUEST]


class BodyEntry(Container):
    """One bodies-response entry."""

    available: boolean
    body: ExecutionPayloadBodyAmsterdam


class BodiesResponse(Container):
    """The /bodies response."""

    entries: List[BodyEntry, MAX_BODIES_REQUEST]


class BlobsV1Request(Container):
    """The /blobs/v1 request."""

    versioned_hashes: List[VersionedHash, MAX_BLOBS_REQUEST]


class BlobV1Entry(Container):
    """One /blobs/v1 response entry."""

    available: boolean
    contents: BlobAndProofV1


class BlobsV1Response(Container):
    """The /blobs/v1 response."""

    entries: List[BlobV1Entry, MAX_BLOBS_REQUEST]


class BlobsV2Request(Container):
    """The /blobs/v2 request."""

    versioned_hashes: List[VersionedHash, MAX_BLOBS_REQUEST]


class BlobV2Entry(Container):
    """One /blobs/v2 response entry."""

    available: boolean
    contents: BlobAndProofV2


class BlobsV2Response(Container):
    """The /blobs/v2 response."""

    entries: List[BlobV2Entry, MAX_BLOBS_REQUEST]


class BlobsV3Response(Container):
    """The /blobs/v3 response."""

    entries: List[BlobV2Entry, MAX_BLOBS_REQUEST]


class BlobsV4Request(Container):
    """The /blobs/v4 request."""

    versioned_hashes: List[VersionedHash, MAX_BLOBS_REQUEST]
    indices_bitarray: Bitvector[CELLS_PER_EXT_BLOB]


class BlobV4Entry(Container):
    """One /blobs/v4 response entry."""

    available: boolean
    contents: BlobCellsAndProofs


class BlobsV4Response(Container):
    """The /blobs/v4 response."""

    entries: List[BlobV4Entry, MAX_BLOBS_REQUEST]


class ClientVersion(Container):
    """A client identity entry."""

    code: ByteList[MAX_CLIENT_CODE_LENGTH]
    name: ByteList[MAX_CLIENT_NAME_LENGTH]
    version: ByteList[MAX_CLIENT_VERSION_LENGTH]
    commit: Bytes4


class IdentityResponse(Container):
    """The /identity response."""

    versions: List[ClientVersion, MAX_CLIENT_VERSIONS]


class CapabilitiesResponse(Container):
    """The /capabilities response (capability-name list)."""

    capabilities: List[ByteList[MAX_CAPABILITY_NAME_LENGTH], MAX_CAPABILITIES]
