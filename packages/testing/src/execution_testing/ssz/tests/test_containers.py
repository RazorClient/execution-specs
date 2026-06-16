"""Round-trip and structural tests for the SSZ containers."""

from .. import decode_bytes, encode_bytes, hash_tree_root
from ..containers import (
    EXECUTION_PAYLOAD_BY_FORK,
    EXECUTION_PAYLOAD_ENVELOPE_BY_FORK,
    ExecutionPayloadAmsterdam,
    ExecutionPayloadEnvelopeAmsterdam,
    Withdrawal,
)

TRANSACTIONS = [
    bytes.fromhex("02f86b01"),
    bytes.fromhex("01" * 21),
    bytes.fromhex("03" * 5),
]


def _withdrawal() -> Withdrawal:
    return Withdrawal(
        index=7,
        validator_index=42,
        address=bytes.fromhex("11" * 20),
        amount=32_000_000_000,
    )


def _max_payload() -> ExecutionPayloadAmsterdam:
    """The maximal (Amsterdam) payload: populated, carrying every field."""
    return ExecutionPayloadAmsterdam(
        parent_hash=bytes.fromhex("aa" * 32),
        fee_recipient=bytes.fromhex("bb" * 20),
        state_root=bytes.fromhex("cc" * 32),
        receipts_root=bytes.fromhex("dd" * 32),
        logs_bloom=bytes.fromhex("00" * 256),
        prev_randao=bytes.fromhex("ee" * 32),
        block_number=21_000_000,
        gas_limit=30_000_000,
        gas_used=21_000,
        timestamp=1_700_000_000,
        extra_data=bytes.fromhex("dead"),
        base_fee_per_gas=10**18,
        block_hash=bytes.fromhex("ff" * 32),
        transactions=list(TRANSACTIONS),
        withdrawals=[_withdrawal()],
        blob_gas_used=131_072,
        excess_blob_gas=0,
        block_access_list=bytes.fromhex("c0de"),
        slot_number=9_999,
    )


def _max_envelope() -> ExecutionPayloadEnvelopeAmsterdam:
    """The maximal (Amsterdam) envelope wrapping :func:`_max_payload`."""
    return ExecutionPayloadEnvelopeAmsterdam(
        payload=_max_payload(),
        parent_beacon_block_root=bytes.fromhex("12" * 32),
        execution_requests=[bytes.fromhex("00aa"), bytes.fromhex("01bbcc")],
    )


def test_withdrawal_round_trip() -> None:
    """A withdrawal survives encode -> decode unchanged."""
    value = _withdrawal()
    raw = encode_bytes(value)
    assert decode_bytes(Withdrawal, raw) == value


def test_payload_round_trip() -> None:
    """An execution payload survives encode -> decode unchanged."""
    value = _max_payload()
    raw = encode_bytes(value)
    assert decode_bytes(ExecutionPayloadAmsterdam, raw) == value


def test_envelope_round_trip() -> None:
    """An envelope survives encode -> decode unchanged."""
    value = _max_envelope()
    raw = encode_bytes(value)
    assert decode_bytes(ExecutionPayloadEnvelopeAmsterdam, raw) == value


def test_hash_tree_root_is_32_bytes_and_deterministic() -> None:
    """`hash_tree_root` returns a stable 32-byte digest."""
    root = hash_tree_root(_max_envelope())
    assert isinstance(root, bytes)
    assert len(root) == 32
    assert root == hash_tree_root(_max_envelope())


def test_transactions_two_level_offsets() -> None:
    """
    Transactions of differing lengths round-trip exactly, and reordering them
    changes the root -- the inner offset table is order- and length-sensitive.
    """
    value = _max_payload()
    decoded = decode_bytes(ExecutionPayloadAmsterdam, encode_bytes(value))
    assert [bytes(tx) for tx in decoded.transactions] == TRANSACTIONS

    reordered = _max_payload()
    reordered.transactions = list(reversed(TRANSACTIONS))
    assert hash_tree_root(reordered) != hash_tree_root(value)


def test_every_fork_payload_round_trips() -> None:
    """Every modelled payload survives a zero-value encode -> decode."""
    for fork, cls in EXECUTION_PAYLOAD_BY_FORK.items():
        value = cls()
        assert decode_bytes(cls, encode_bytes(value)) == value, fork


def test_every_fork_envelope_round_trips() -> None:
    """Every modelled envelope survives a zero-value encode -> decode."""
    for fork, cls in EXECUTION_PAYLOAD_ENVELOPE_BY_FORK.items():
        value = cls()
        assert decode_bytes(cls, encode_bytes(value)) == value, fork


def test_per_fork_envelope_wraps_matching_payload() -> None:
    """Each envelope's ``payload`` field is its own fork's payload class."""
    for fork, cls in EXECUTION_PAYLOAD_ENVELOPE_BY_FORK.items():
        payload_type = dict(cls.fields())["payload"]
        assert payload_type is EXECUTION_PAYLOAD_BY_FORK[fork], fork
