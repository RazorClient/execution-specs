"""Round-trip and structural tests for the SSZ containers."""

from .. import decode_bytes, encode_bytes, hash_tree_root
from ..containers import (
    EXECUTION_PAYLOAD_BY_FORK,
    EXECUTION_PAYLOAD_ENVELOPE_BY_FORK,
    ExecutionPayloadAmsterdam,
    ExecutionPayloadEnvelopeAmsterdam,
    Withdrawal,
)
from ..json_mapping import from_json, to_json

# A spread of transaction lengths, on purpose: a two-level `List[ByteList, N]`
# only exercises its inner offset table when the elements differ in length.
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


def _payload() -> ExecutionPayloadAmsterdam:
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


def _envelope() -> ExecutionPayloadEnvelopeAmsterdam:
    return ExecutionPayloadEnvelopeAmsterdam(
        payload=_payload(),
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
    value = _payload()
    raw = encode_bytes(value)
    assert decode_bytes(ExecutionPayloadAmsterdam, raw) == value


def test_envelope_round_trip() -> None:
    """An envelope survives encode -> decode unchanged."""
    value = _envelope()
    raw = encode_bytes(value)
    assert decode_bytes(ExecutionPayloadEnvelopeAmsterdam, raw) == value


def test_hash_tree_root_is_32_bytes_and_deterministic() -> None:
    """`hash_tree_root` returns a stable 32-byte digest."""
    root = hash_tree_root(_envelope())
    assert isinstance(root, bytes)
    assert len(root) == 32
    assert root == hash_tree_root(_envelope())


def test_transactions_two_level_offsets() -> None:
    """
    Transactions of differing lengths round-trip exactly, and reordering them
    changes the root -- the inner offset table is order- and length-sensitive.
    """
    value = _payload()
    decoded = decode_bytes(ExecutionPayloadAmsterdam, encode_bytes(value))
    assert [bytes(tx) for tx in decoded.transactions] == TRANSACTIONS

    reordered = _payload()
    reordered.transactions = list(reversed(TRANSACTIONS))
    assert hash_tree_root(reordered) != hash_tree_root(value)


def test_execution_payload_field_order() -> None:
    """
    Guard the load-bearing field order against silent reordering.

    SSZ is order-sensitive: a wrong order produces a wrong but
    structurally-valid root.
    """
    assert list(ExecutionPayloadAmsterdam.fields().keys()) == [
        "parent_hash",
        "fee_recipient",
        "state_root",
        "receipts_root",
        "logs_bloom",
        "prev_randao",
        "block_number",
        "gas_limit",
        "gas_used",
        "timestamp",
        "extra_data",
        "base_fee_per_gas",
        "block_hash",
        "transactions",
        "withdrawals",
        "blob_gas_used",
        "excess_blob_gas",
        "block_access_list",
        "slot_number",
    ]


def test_execution_payload_registry_covers_forks_in_order() -> None:
    """The registry enumerates every payload fork, oldest-first."""
    assert list(EXECUTION_PAYLOAD_BY_FORK) == [
        "Paris",
        "Shanghai",
        "Cancun",
        "Prague",
        "Osaka",
        "Amsterdam",
    ]


def test_per_fork_field_deltas_match_consensus_specs() -> None:
    """
    Each fork's payload is its predecessor's fields plus exactly the fields the
    corresponding consensus fork added.

    This encodes the consensus-specs evolution as per-fork deltas (Paris is the
    Bellatrix base; Capella adds withdrawals; Deneb adds the blob-gas fields;
    Electra and Fulu add nothing; Amsterdam adds the two EL fields). SSZ is
    order-sensitive, so it guards both the additions and that nothing earlier
    was reordered or dropped.
    """
    expected = [
        "parent_hash",
        "fee_recipient",
        "state_root",
        "receipts_root",
        "logs_bloom",
        "prev_randao",
        "block_number",
        "gas_limit",
        "gas_used",
        "timestamp",
        "extra_data",
        "base_fee_per_gas",
        "block_hash",
        "transactions",
    ]
    additions = {
        "Paris": [],
        "Shanghai": ["withdrawals"],
        "Cancun": ["blob_gas_used", "excess_blob_gas"],
        "Prague": [],
        "Osaka": [],
        "Amsterdam": ["block_access_list", "slot_number"],
    }
    for fork, cls in EXECUTION_PAYLOAD_BY_FORK.items():
        expected = expected + additions[fork]
        assert list(cls.fields().keys()) == expected, fork


def test_every_fork_payload_round_trips() -> None:
    """Every modelled payload survives a zero-value encode -> decode."""
    for fork, cls in EXECUTION_PAYLOAD_BY_FORK.items():
        value = cls()
        assert decode_bytes(cls, encode_bytes(value)) == value, fork


def test_envelope_field_order() -> None:
    """Guard the envelope field order from PR #793."""
    assert list(ExecutionPayloadEnvelopeAmsterdam.fields().keys()) == [
        "payload",
        "parent_beacon_block_root",
        "execution_requests",
    ]


def test_json_round_trip_preserves_value() -> None:
    """to_json -> from_json reconstructs an equal envelope."""
    value = _envelope()
    assert (
        from_json(ExecutionPayloadEnvelopeAmsterdam, to_json(value)) == value
    )


def test_envelope_registry_covers_forks_in_order() -> None:
    """The envelope registry spans every payload fork, oldest-first."""
    assert list(EXECUTION_PAYLOAD_ENVELOPE_BY_FORK) == [
        "Paris",
        "Shanghai",
        "Cancun",
        "Prague",
        "Osaka",
        "Amsterdam",
    ]


def test_per_fork_envelope_field_deltas() -> None:
    """
    Each envelope is its predecessor's fields plus exactly the arguments the
    corresponding ``newPayloadVX`` gained.

    Paris/Shanghai wrap only the payload (V1/V2); Cancun introduces
    ``parent_beacon_block_root``; Prague adds ``execution_requests``; the field
    set is then stable through Amsterdam (later forks differ only by the inner
    payload type). ``expectedBlobVersionedHashes`` is omitted throughout,
    matching PR #793.
    """
    expected = ["payload"]
    additions = {
        "Paris": [],
        "Shanghai": [],
        "Cancun": ["parent_beacon_block_root"],
        "Prague": ["execution_requests"],
        "Osaka": [],
        "Amsterdam": [],
    }
    for fork, cls in EXECUTION_PAYLOAD_ENVELOPE_BY_FORK.items():
        expected = expected + additions[fork]
        assert list(cls.fields().keys()) == expected, fork


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
