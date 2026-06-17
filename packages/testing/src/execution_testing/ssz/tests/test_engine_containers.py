"""
Structural tests for the broader Engine API SSZ containers from PR #793.
"""

import pytest

from .. import decode_bytes, encode_bytes, envelope_bytes
from ..containers import (
    BUILT_PAYLOAD_BY_FORK,
    EXECUTION_PAYLOAD_BODY_BY_FORK,
    FORKCHOICE_UPDATE_BY_FORK,
    PAYLOAD_ATTRIBUTES_BY_FORK,
    ExecutionPayloadEnvelopeAmsterdam,
    ExecutionPayloadEnvelopeParis,
    PayloadStatus,
)

_FORKS = ["Paris", "Shanghai", "Cancun", "Prague", "Osaka", "Amsterdam"]


def test_new_registries_cover_forks_in_order() -> None:
    """Every new per-fork registry spans Paris..Amsterdam."""
    for reg in (
        PAYLOAD_ATTRIBUTES_BY_FORK,
        FORKCHOICE_UPDATE_BY_FORK,
        EXECUTION_PAYLOAD_BODY_BY_FORK,
        BUILT_PAYLOAD_BY_FORK,
    ):
        assert list(reg) == _FORKS


def test_payload_status_optional_encoding_matches_spec_examples() -> None:
    """
    The ``Optional``/``String`` wire shape tests.
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


def _base_payload_fields() -> dict:
    """The fields every fork's payload carries, with valid dummy values."""
    return dict(
        parent_hash=b"\x00" * 32,
        fee_recipient=b"\x00" * 20,
        state_root=b"\x00" * 32,
        receipts_root=b"\x00" * 32,
        logs_bloom=b"\x00" * 256,
        prev_randao=b"\x00" * 32,
        block_number=1,
        gas_limit=1,
        gas_used=1,
        timestamp=1,
        extra_data=b"",
        base_fee_per_gas=1,
        block_hash=b"\x00" * 32,
        transactions=[],
    )


def test_envelope_bytes_dispatches_by_fork() -> None:
    """``envelope_bytes`` builds each fork's envelope from the registries."""
    paris = envelope_bytes("Paris", **_base_payload_fields())
    assert (
        encode_bytes(decode_bytes(ExecutionPayloadEnvelopeParis, paris))
        == paris
    )
    amsterdam = envelope_bytes(
        "Amsterdam",
        **_base_payload_fields(),
        withdrawals=[],
        blob_gas_used=0,
        excess_blob_gas=0,
        block_access_list=b"",
        slot_number=7,
        parent_beacon_block_root=b"\x00" * 32,
        execution_requests=[],
    )
    decoded = decode_bytes(ExecutionPayloadEnvelopeAmsterdam, amsterdam)
    assert int(decoded.payload.slot_number) == 7


def test_envelope_bytes_missing_required_field_raises() -> None:
    """Omitting a field the fork's container needs raises ``ValueError``."""
    with pytest.raises(ValueError, match="requires field"):
        envelope_bytes("Amsterdam", **_base_payload_fields())


def test_envelope_bytes_unknown_fork_raises() -> None:
    """An unknown fork name raises ``ValueError``."""
    with pytest.raises(ValueError, match="unknown fork"):
        envelope_bytes("Bogus", **_base_payload_fields())
