"""Round-trip and structural tests for the SSZ containers."""

from remerkleable.basic import uint64, uint256
from remerkleable.byte_arrays import ByteList
from remerkleable.complex import List

from .. import (
    EXECUTION_PAYLOAD_BY_FORK,
    EXECUTION_PAYLOAD_ENVELOPE_BY_FORK,
    decode_bytes,
    encode_bytes,
    hash_tree_root,
)
from ..constants import (
    MAX_BAL_BYTES,
    MAX_BYTES_PER_EXECUTION_REQUEST,
    MAX_BYTES_PER_TX,
    MAX_EXECUTION_REQUESTS_PER_PAYLOAD,
    MAX_TXS_PER_PAYLOAD,
)
from ..containers import (
    ExecutionPayloadAmsterdam,
    ExecutionPayloadEnvelopeAmsterdam,
    Withdrawal,
)
from ..ssz_types import Address, Bloom, Bytes32, Hash32, Root


Transactions = List[ByteList[MAX_BYTES_PER_TX], MAX_TXS_PER_PAYLOAD]
BlockAccessList = ByteList[MAX_BAL_BYTES]
ExecutionRequests = List[
    ByteList[MAX_BYTES_PER_EXECUTION_REQUEST],
    MAX_EXECUTION_REQUESTS_PER_PAYLOAD,
]


TRANSACTIONS = [
    bytes.fromhex("02f86b01"),
    bytes.fromhex("01" * 21),
    bytes.fromhex("03" * 5),
]


def _withdrawal() -> Withdrawal:
    return Withdrawal(
        index=uint64(7),
        validator_index=uint64(42),
        address=Address(bytes.fromhex("11" * 20)),
        amount=uint64(32_000_000_000),
    )


def _random_payload() -> ExecutionPayloadAmsterdam:
    """A fully-populated payload carrying every field of the latest fork."""
    return ExecutionPayloadAmsterdam(
        parent_hash=Hash32(bytes.fromhex("aa" * 32)),
        fee_recipient=Address(bytes.fromhex("bb" * 20)),
        state_root=Hash32(bytes.fromhex("cc" * 32)),
        receipts_root=Hash32(bytes.fromhex("dd" * 32)),
        logs_bloom=Bloom(bytes.fromhex("00" * 256)),
        prev_randao=Bytes32(bytes.fromhex("ee" * 32)),
        block_number=uint64(21_000_000),
        gas_limit=uint64(30_000_000),
        gas_used=uint64(21_000),
        timestamp=uint64(1_700_000_000),
        extra_data=bytes.fromhex("dead"),
        base_fee_per_gas=uint256(10**18),
        block_hash=Hash32(bytes.fromhex("ff" * 32)),
        transactions=Transactions(*TRANSACTIONS),
        withdrawals=[_withdrawal()],
        blob_gas_used=uint64(131_072),
        excess_blob_gas=uint64(0),
        block_access_list=BlockAccessList(bytes.fromhex("c0de")),
        slot_number=uint64(9_999),
    )


def _max_envelope() -> ExecutionPayloadEnvelopeAmsterdam:
    """A fully-populated envelope wrapping :func:`_random_payload`."""
    return ExecutionPayloadEnvelopeAmsterdam(
        payload=_random_payload(),
        parent_beacon_block_root=Root(bytes.fromhex("12" * 32)),
        execution_requests=ExecutionRequests(
            bytes.fromhex("00aa"), bytes.fromhex("01bbcc")
        ),
    )


def test_withdrawal_round_trip() -> None:
    """A withdrawal survives encode -> decode unchanged."""
    value = _withdrawal()
    raw = encode_bytes(value)
    assert decode_bytes(Withdrawal, raw) == value


def test_payload_round_trip() -> None:
    """An execution payload survives encode -> decode unchanged."""
    value = _random_payload()
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
    value = _random_payload()
    decoded = decode_bytes(ExecutionPayloadAmsterdam, encode_bytes(value))
    assert [bytes(tx) for tx in decoded.transactions] == TRANSACTIONS

    reordered = _random_payload()
    reordered.transactions = Transactions(*reversed(TRANSACTIONS))
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
