"""
SSZ container types and helpers for the REST+SSZ Engine API.
"""

from typing import Any, Mapping, Sequence, Type, TypeVar

from remerkleable.core import View

from .constants import (
    MAX_BYTES_PER_EXECUTION_REQUEST,
    MAX_BYTES_PER_TX,
    MAX_EXECUTION_REQUESTS_PER_PAYLOAD,
    MAX_EXTRA_DATA_BYTES,
    MAX_TXS_PER_PAYLOAD,
    MAX_WITHDRAWALS_PER_PAYLOAD,
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
from .containers import (
    BUILT_PAYLOAD_BY_FORK,
    EXECUTION_PAYLOAD_BODY_BY_FORK,
    EXECUTION_PAYLOAD_BY_FORK,
    EXECUTION_PAYLOAD_ENVELOPE_BY_FORK,
    FORKCHOICE_UPDATE_BY_FORK,
    PAYLOAD_ATTRIBUTES_BY_FORK,
    BlobAndProofV1,
    BlobAndProofV2,
    BlobCellsAndProofs,
    BlobsBundleV1,
    BlobsBundleV2,
    BlobsV1Request,
    BlobsV1Response,
    BlobsV2Request,
    BlobsV2Response,
    BlobsV3Response,
    BlobsV4Request,
    BlobsV4Response,
    BlobV1Entry,
    BlobV2Entry,
    BlobV4Entry,
    BodiesByHashRequest,
    BodiesResponse,
    BodyEntry,
    BuiltPayloadAmsterdam,
    BuiltPayloadCancun,
    BuiltPayloadOsaka,
    BuiltPayloadParis,
    BuiltPayloadPrague,
    BuiltPayloadShanghai,
    CapabilitiesResponse,
    ClientVersion,
    ExecutionPayloadAmsterdam,
    ExecutionPayloadBodyAmsterdam,
    ExecutionPayloadBodyCancun,
    ExecutionPayloadBodyOsaka,
    ExecutionPayloadBodyParis,
    ExecutionPayloadBodyPrague,
    ExecutionPayloadBodyShanghai,
    ExecutionPayloadCancun,
    ExecutionPayloadEnvelopeAmsterdam,
    ExecutionPayloadEnvelopeCancun,
    ExecutionPayloadEnvelopeOsaka,
    ExecutionPayloadEnvelopeParis,
    ExecutionPayloadEnvelopePrague,
    ExecutionPayloadEnvelopeShanghai,
    ExecutionPayloadOsaka,
    ExecutionPayloadParis,
    ExecutionPayloadPrague,
    ExecutionPayloadShanghai,
    ForkchoiceState,
    ForkchoiceUpdateAmsterdam,
    ForkchoiceUpdateCancun,
    ForkchoiceUpdateOsaka,
    ForkchoiceUpdateParis,
    ForkchoiceUpdatePrague,
    ForkchoiceUpdateResponse,
    ForkchoiceUpdateShanghai,
    IdentityResponse,
    PayloadAttributesAmsterdam,
    PayloadAttributesCancun,
    PayloadAttributesOsaka,
    PayloadAttributesParis,
    PayloadAttributesPrague,
    PayloadAttributesShanghai,
    PayloadStatus,
    Withdrawal,
)
from .random_value import (
    RandomizationMode,
    deterministic_seed,
    get_random_ssz_object,
)

ViewT = TypeVar("ViewT", bound=View)

REFERENCE_SPEC_GIT_PATH = "src/engine/refactor-ssz.md"
REFERENCE_SPEC_VERSION = "4e0fed12d3ebc9d1ca8829331a82b97b1d1bd154"


def encode_bytes(value: View) -> bytes:
    """Serialize an SSZ value to its canonical byte encoding."""
    return value.encode_bytes()


def decode_bytes(ssz_type: Type[ViewT], data: bytes) -> ViewT:
    """Deserialize ``data`` into an SSZ value of ``ssz_type``."""
    return ssz_type.decode_bytes(data)


def hash_tree_root(value: View) -> bytes:
    """Return the 32-byte SSZ `hash_tree_root` of an SSZ value."""
    return bytes(value.hash_tree_root())


def _build(cls: Any, fork: str, candidates: Mapping[str, Any]) -> View:
    kwargs = {}
    for name in cls.fields():
        value = candidates.get(name)
        if value is None:
            raise ValueError(
                f"{cls.__name__} ({fork}) requires field {name!r}"
            )
        kwargs[name] = value
    return cls(**kwargs)


def envelope_bytes(
    fork: str,
    *,
    parent_hash: bytes,
    fee_recipient: bytes,
    state_root: bytes,
    receipts_root: bytes,
    logs_bloom: bytes,
    prev_randao: bytes,
    block_number: int,
    gas_limit: int,
    gas_used: int,
    timestamp: int,
    extra_data: bytes,
    base_fee_per_gas: int,
    block_hash: bytes,
    transactions: Sequence[bytes],
    withdrawals: Sequence[Mapping[str, Any]] | None = None,
    blob_gas_used: int | None = None,
    excess_blob_gas: int | None = None,
    block_access_list: bytes | None = None,
    slot_number: int | None = None,
    parent_beacon_block_root: bytes | None = None,
    execution_requests: Sequence[bytes] | None = None,
) -> bytes:
    """
    Build a fork's `newPayload` envelope from plain values and return its
    canonical SSZ byte encoding.
    """
    if fork not in EXECUTION_PAYLOAD_ENVELOPE_BY_FORK:
        raise ValueError(f"unknown fork: {fork!r}")

    def _opt_bytes(value: bytes | None) -> bytes | None:
        return None if value is None else bytes(value)

    payload_values: Mapping[str, Any] = {
        "parent_hash": bytes(parent_hash),
        "fee_recipient": bytes(fee_recipient),
        "state_root": bytes(state_root),
        "receipts_root": bytes(receipts_root),
        "logs_bloom": bytes(logs_bloom),
        "prev_randao": bytes(prev_randao),
        "block_number": block_number,
        "gas_limit": gas_limit,
        "gas_used": gas_used,
        "timestamp": timestamp,
        "extra_data": bytes(extra_data),
        "base_fee_per_gas": base_fee_per_gas,
        "block_hash": bytes(block_hash),
        "transactions": [bytes(tx) for tx in transactions],
        "withdrawals": (
            None
            if withdrawals is None
            else [Withdrawal(**w) for w in withdrawals]
        ),
        "blob_gas_used": blob_gas_used,
        "excess_blob_gas": excess_blob_gas,
        "block_access_list": _opt_bytes(block_access_list),
        "slot_number": slot_number,
    }
    payload = _build(EXECUTION_PAYLOAD_BY_FORK[fork], fork, payload_values)

    envelope_values: Mapping[str, Any] = {
        "payload": payload,
        "parent_beacon_block_root": _opt_bytes(parent_beacon_block_root),
        "execution_requests": (
            None
            if execution_requests is None
            else [bytes(r) for r in execution_requests]
        ),
    }
    envelope = _build(
        EXECUTION_PAYLOAD_ENVELOPE_BY_FORK[fork], fork, envelope_values
    )
    return encode_bytes(envelope)


__all__ = (
    "BUILT_PAYLOAD_BY_FORK",
    "EXECUTION_PAYLOAD_BODY_BY_FORK",
    "EXECUTION_PAYLOAD_BY_FORK",
    "EXECUTION_PAYLOAD_ENVELOPE_BY_FORK",
    "FORKCHOICE_UPDATE_BY_FORK",
    "PAYLOAD_ATTRIBUTES_BY_FORK",
    "Address",
    "BlobAndProofV1",
    "BlobAndProofV2",
    "BlobCellsAndProofs",
    "BlobsBundleV1",
    "BlobsBundleV2",
    "BlobsV1Request",
    "BlobsV1Response",
    "BlobsV2Request",
    "BlobsV2Response",
    "BlobsV3Response",
    "BlobsV4Request",
    "BlobsV4Response",
    "BlobV1Entry",
    "BlobV2Entry",
    "BlobV4Entry",
    "Bloom",
    "BodiesByHashRequest",
    "BodiesResponse",
    "BodyEntry",
    "BuiltPayloadAmsterdam",
    "BuiltPayloadCancun",
    "BuiltPayloadOsaka",
    "BuiltPayloadParis",
    "BuiltPayloadPrague",
    "BuiltPayloadShanghai",
    "Bytes32",
    "Bytes4",
    "Bytes48",
    "Bytes8",
    "CapabilitiesResponse",
    "ClientVersion",
    "ExecutionPayloadAmsterdam",
    "ExecutionPayloadBodyAmsterdam",
    "ExecutionPayloadBodyCancun",
    "ExecutionPayloadBodyOsaka",
    "ExecutionPayloadBodyParis",
    "ExecutionPayloadBodyPrague",
    "ExecutionPayloadBodyShanghai",
    "ExecutionPayloadCancun",
    "ExecutionPayloadEnvelopeAmsterdam",
    "ExecutionPayloadEnvelopeCancun",
    "ExecutionPayloadEnvelopeOsaka",
    "ExecutionPayloadEnvelopeParis",
    "ExecutionPayloadEnvelopePrague",
    "ExecutionPayloadEnvelopeShanghai",
    "ExecutionPayloadOsaka",
    "ExecutionPayloadParis",
    "ExecutionPayloadPrague",
    "ExecutionPayloadShanghai",
    "ForkchoiceState",
    "ForkchoiceUpdateAmsterdam",
    "ForkchoiceUpdateCancun",
    "ForkchoiceUpdateOsaka",
    "ForkchoiceUpdateParis",
    "ForkchoiceUpdatePrague",
    "ForkchoiceUpdateResponse",
    "ForkchoiceUpdateShanghai",
    "Hash32",
    "IdentityResponse",
    "MAX_BYTES_PER_EXECUTION_REQUEST",
    "MAX_BYTES_PER_TX",
    "MAX_EXECUTION_REQUESTS_PER_PAYLOAD",
    "MAX_EXTRA_DATA_BYTES",
    "MAX_TXS_PER_PAYLOAD",
    "MAX_WITHDRAWALS_PER_PAYLOAD",
    "PayloadAttributesAmsterdam",
    "PayloadAttributesCancun",
    "PayloadAttributesOsaka",
    "PayloadAttributesParis",
    "PayloadAttributesPrague",
    "PayloadAttributesShanghai",
    "PayloadStatus",
    "REFERENCE_SPEC_GIT_PATH",
    "REFERENCE_SPEC_VERSION",
    "RandomizationMode",
    "Root",
    "VersionedHash",
    "Withdrawal",
    "decode_bytes",
    "deterministic_seed",
    "encode_bytes",
    "envelope_bytes",
    "get_random_ssz_object",
    "hash_tree_root",
)
