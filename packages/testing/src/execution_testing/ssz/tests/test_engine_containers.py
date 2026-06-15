"""
Structural tests for the broader Engine API SSZ containers from PR #793.

Guards the load-bearing field order of every container beyond the core
payload/envelope set (those live in ``test_containers.py``), plus the subtle
``Optional``/``String`` encoding in ``PayloadStatus``.
"""

from .. import decode_bytes, encode_bytes
from ..containers import (
    BUILT_PAYLOAD_BY_FORK,
    EXECUTION_PAYLOAD_BODY_BY_FORK,
    FORKCHOICE_UPDATE_BY_FORK,
    PAYLOAD_ATTRIBUTES_BY_FORK,
    BlobAndProofV1,
    BlobAndProofV2,
    BlobCellsAndProofs,
    BlobsBundleV1,
    BlobsBundleV2,
    BlobsV1Request,
    BlobsV1Response,
    BlobsV4Request,
    BlobV1Entry,
    BlobV4Entry,
    BodiesByHashRequest,
    BodiesResponse,
    BodyEntry,
    CapabilitiesResponse,
    ClientVersion,
    ForkchoiceState,
    ForkchoiceUpdateResponse,
    IdentityResponse,
    PayloadStatus,
)

_FORKS = ["Paris", "Shanghai", "Cancun", "Prague", "Osaka", "Amsterdam"]


def _fields(cls: object) -> list:
    return list(cls.fields().keys())  # type: ignore[attr-defined]


def test_new_registries_cover_forks_in_order() -> None:
    """Every per-fork registry spans Paris..Amsterdam, oldest-first."""
    for reg in (
        PAYLOAD_ATTRIBUTES_BY_FORK,
        FORKCHOICE_UPDATE_BY_FORK,
        EXECUTION_PAYLOAD_BODY_BY_FORK,
        BUILT_PAYLOAD_BY_FORK,
    ):
        assert list(reg) == _FORKS


def test_payload_attributes_field_deltas() -> None:
    """PayloadAttributes grows by the fields each fork added."""
    expected = ["timestamp", "prev_randao", "suggested_fee_recipient"]
    additions = {
        "Paris": [],
        "Shanghai": ["withdrawals"],
        "Cancun": ["parent_beacon_block_root"],
        "Prague": [],
        "Osaka": [],
        "Amsterdam": ["slot_number", "target_gas_limit"],
    }
    for fork, cls in PAYLOAD_ATTRIBUTES_BY_FORK.items():
        expected = expected + additions[fork]
        assert _fields(cls) == expected, fork


def test_execution_payload_body_field_deltas() -> None:
    """ExecutionPayloadBody grows transactions -> withdrawals -> BAL."""
    expected = ["transactions"]
    additions = {
        "Paris": [],
        "Shanghai": ["withdrawals"],
        "Cancun": [],
        "Prague": [],
        "Osaka": [],
        "Amsterdam": ["block_access_list"],
    }
    for fork, cls in EXECUTION_PAYLOAD_BODY_BY_FORK.items():
        expected = expected + additions[fork]
        assert _fields(cls) == expected, fork


def test_built_payload_field_order() -> None:
    """
    BuiltPayload field order per fork.

    Not a simple prefix growth: ``execution_requests`` is inserted *before*
    ``should_override_builder`` (normative in #793).
    """
    expected = {
        "Paris": ["payload", "block_value"],
        "Shanghai": ["payload", "block_value", "should_override_builder"],
        "Cancun": [
            "payload",
            "block_value",
            "blobs_bundle",
            "should_override_builder",
        ],
        "Prague": [
            "payload",
            "block_value",
            "blobs_bundle",
            "execution_requests",
            "should_override_builder",
        ],
    }
    expected["Osaka"] = expected["Prague"]
    expected["Amsterdam"] = expected["Prague"]
    for fork, cls in BUILT_PAYLOAD_BY_FORK.items():
        assert _fields(cls) == expected[fork], fork


def test_forkchoice_update_field_order() -> None:
    """ForkchoiceUpdate gains custody_columns only at Amsterdam."""
    for fork, cls in FORKCHOICE_UPDATE_BY_FORK.items():
        base = ["forkchoice_state", "payload_attributes"]
        if fork == "Amsterdam":
            base = base + ["custody_columns"]
        assert _fields(cls) == base, fork


def test_single_container_field_orders() -> None:
    """Exact field order for the fork-independent containers."""
    assert _fields(ForkchoiceState) == [
        "head_block_hash",
        "safe_block_hash",
        "finalized_block_hash",
    ]
    assert _fields(PayloadStatus) == [
        "status",
        "latest_valid_hash",
        "validation_error",
    ]
    assert _fields(ForkchoiceUpdateResponse) == [
        "payload_status",
        "payload_id",
    ]
    assert _fields(BlobsBundleV1) == ["commitments", "proofs", "blobs"]
    assert _fields(BlobsBundleV2) == ["commitments", "proofs", "blobs"]
    assert _fields(BlobAndProofV1) == ["blob", "proof"]
    assert _fields(BlobAndProofV2) == ["blob", "proofs"]
    assert _fields(BlobCellsAndProofs) == ["blob_cells", "proofs"]
    assert _fields(BodiesByHashRequest) == ["block_hashes"]
    assert _fields(BodyEntry) == ["available", "body"]
    assert _fields(BodiesResponse) == ["entries"]
    assert _fields(BlobsV1Request) == ["versioned_hashes"]
    assert _fields(BlobV1Entry) == ["available", "contents"]
    assert _fields(BlobsV1Response) == ["entries"]
    assert _fields(BlobsV4Request) == [
        "versioned_hashes",
        "indices_bitarray",
    ]
    assert _fields(BlobV4Entry) == ["available", "contents"]
    assert _fields(ClientVersion) == ["code", "name", "version", "commit"]
    assert _fields(IdentityResponse) == ["versions"]
    assert _fields(CapabilitiesResponse) == ["capabilities"]


def test_payload_status_optional_encoding_matches_spec_examples() -> None:
    """
    The ``Optional``/``String`` wire shape matches PR #793's worked examples.

    Example A: VALID with a present ``latest_valid_hash`` and absent error is
    41 bytes. Example B: INVALID with a 14-byte error and absent hash is 27.
    """
    valid = PayloadStatus(
        status=0, latest_valid_hash=[b"\xaa" * 32], validation_error=[]
    )
    assert len(encode_bytes(valid)) == 41
    assert decode_bytes(PayloadStatus, encode_bytes(valid)) == valid

    invalid = PayloadStatus(
        status=1,
        latest_valid_hash=[],
        validation_error=[b"bad state root"],
    )
    assert len(encode_bytes(invalid)) == 27
    assert decode_bytes(PayloadStatus, encode_bytes(invalid)) == invalid


def test_per_fork_engine_containers_round_trip() -> None:
    """Zero-value encode -> decode for every per-fork engine container."""
    for reg in (
        PAYLOAD_ATTRIBUTES_BY_FORK,
        FORKCHOICE_UPDATE_BY_FORK,
        EXECUTION_PAYLOAD_BODY_BY_FORK,
        BUILT_PAYLOAD_BY_FORK,
    ):
        for fork, cls in reg.items():
            value = cls()
            assert decode_bytes(cls, encode_bytes(value)) == value, fork
