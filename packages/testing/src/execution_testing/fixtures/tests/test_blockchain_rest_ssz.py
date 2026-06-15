"""
Tests for the REST+SSZ blockchain fixture models.

The load-bearing test here is the drift round-trip: ``FixtureRestPayload`` and
the remerkleable ``ExecutionPayloadEnvelope`` describe the same object in two
different type systems, and they must stay in step by hand. The round-trip
(pydantic -> ``to_ssz()`` -> remerkleable decode -> field comparison) fails
loudly the moment they diverge.
"""

from execution_testing.base_types import (
    Address,
    Bloom,
    Bytes,
    Hash,
    HexNumber,
)
from execution_testing.fixtures import BaseFixture
from execution_testing.fixtures.blockchain_rest_ssz import (
    BlockchainRestSszFixture,
    FixtureRestExecutionPayload,
    FixtureRestPayload,
    FixtureRestWithdrawal,
    PayloadStatusV2,
)
from execution_testing.ssz import (
    ExecutionPayloadEnvelopeAmsterdam,
    ExecutionPayloadEnvelopeCancun,
    decode_bytes,
)

# Transactions of differing lengths, on purpose: the two-level
# `List[ByteList, N]` only exercises its inner offset table when the elements
# differ in length.
TRANSACTIONS = [
    Bytes(bytes.fromhex("02f86b01")),
    Bytes(bytes.fromhex("01" * 21)),
    Bytes(bytes.fromhex("03" * 5)),
]
EXECUTION_REQUESTS = [
    Bytes(bytes.fromhex("00aa")),
    Bytes(bytes.fromhex("01bbcc")),
]


def _execution_payload() -> FixtureRestExecutionPayload:
    return FixtureRestExecutionPayload(
        fork="Amsterdam",
        parent_hash=Hash(bytes.fromhex("aa" * 32)),
        fee_recipient=Address(bytes.fromhex("bb" * 20)),
        state_root=Hash(bytes.fromhex("cc" * 32)),
        receipts_root=Hash(bytes.fromhex("dd" * 32)),
        logs_bloom=Bloom(bytes.fromhex("00" * 256)),
        prev_randao=Hash(bytes.fromhex("ee" * 32)),
        block_number=HexNumber(21_000_000),
        gas_limit=HexNumber(30_000_000),
        gas_used=HexNumber(21_000),
        timestamp=HexNumber(1_700_000_000),
        extra_data=Bytes(bytes.fromhex("dead")),
        base_fee_per_gas=HexNumber(10**18),
        block_hash=Hash(bytes.fromhex("ff" * 32)),
        transactions=list(TRANSACTIONS),
        withdrawals=[
            FixtureRestWithdrawal(
                index=HexNumber(7),
                validator_index=HexNumber(42),
                address=Address(bytes.fromhex("11" * 20)),
                amount=HexNumber(32_000_000_000),
            )
        ],
        blob_gas_used=HexNumber(131_072),
        excess_blob_gas=HexNumber(0),
        block_access_list=Bytes(bytes.fromhex("c0de")),
        slot_number=HexNumber(9_999),
        parent_beacon_block_root=Hash(bytes.fromhex("12" * 32)),
        execution_requests=list(EXECUTION_REQUESTS),
    )


def _payload_directive() -> FixtureRestPayload:
    return FixtureRestPayload(
        payload=_execution_payload(),
        expected_status=PayloadStatusV2.VALID,
    )


def test_to_ssz_round_trips_field_for_field() -> None:
    """
    Pydantic -> ``to_ssz()`` -> remerkleable decode reconstructs every field.

    This is the drift guard between ``FixtureRestPayload`` and
    ``ExecutionPayloadEnvelope``. If a fork adds a field to one type system but
    not the other, the decoded value no longer matches and this test fails.
    """
    directive = _payload_directive()
    src = directive.payload

    decoded = decode_bytes(
        ExecutionPayloadEnvelopeAmsterdam, directive.to_ssz()
    )
    payload = decoded.payload

    assert bytes(payload.parent_hash) == bytes(src.parent_hash)
    assert bytes(payload.fee_recipient) == bytes(src.fee_recipient)
    assert bytes(payload.state_root) == bytes(src.state_root)
    assert bytes(payload.receipts_root) == bytes(src.receipts_root)
    assert bytes(payload.logs_bloom) == bytes(src.logs_bloom)
    assert bytes(payload.prev_randao) == bytes(src.prev_randao)
    assert int(payload.block_number) == int(src.block_number)
    assert int(payload.gas_limit) == int(src.gas_limit)
    assert int(payload.gas_used) == int(src.gas_used)
    assert int(payload.timestamp) == int(src.timestamp)
    assert bytes(payload.extra_data) == bytes(src.extra_data)
    assert int(payload.base_fee_per_gas) == int(src.base_fee_per_gas)
    assert bytes(payload.block_hash) == bytes(src.block_hash)
    assert [bytes(tx) for tx in payload.transactions] == [
        bytes(tx) for tx in src.transactions
    ]
    # An Amsterdam payload carries every (now-optional) field; narrow them.
    assert src.withdrawals is not None
    assert src.blob_gas_used is not None
    assert src.excess_blob_gas is not None
    assert src.block_access_list is not None
    assert src.slot_number is not None
    assert src.parent_beacon_block_root is not None
    assert src.execution_requests is not None
    assert len(payload.withdrawals) == len(src.withdrawals)
    decoded_w = payload.withdrawals[0]
    src_w = src.withdrawals[0]
    assert int(decoded_w.index) == int(src_w.index)
    assert int(decoded_w.validator_index) == int(src_w.validator_index)
    assert bytes(decoded_w.address) == bytes(src_w.address)
    assert int(decoded_w.amount) == int(src_w.amount)
    assert int(payload.blob_gas_used) == int(src.blob_gas_used)
    assert int(payload.excess_blob_gas) == int(src.excess_blob_gas)
    assert bytes(payload.block_access_list) == bytes(src.block_access_list)
    assert int(payload.slot_number) == int(src.slot_number)
    assert bytes(decoded.parent_beacon_block_root) == bytes(
        src.parent_beacon_block_root
    )
    assert [bytes(r) for r in decoded.execution_requests] == [
        bytes(r) for r in src.execution_requests
    ]


def test_to_ssz_matches_stored_ssz_hex() -> None:
    """The stored ``ssz`` inspection field equals the live ``to_ssz()``."""
    directive = _payload_directive()
    assert bytes(directive.ssz) == directive.to_ssz()


def test_to_ssz_dispatches_on_fork() -> None:
    """
    A non-Amsterdam directive builds that fork's envelope.

    A ``Cancun`` payload omits the Amsterdam-only fields
    (``block_access_list``, ``slot_number``) and ``execution_requests``
    (Prague+); ``to_ssz`` must produce bytes that decode as a Cancun
    envelope, not the Amsterdam one.
    """
    payload = FixtureRestExecutionPayload(
        fork="Cancun",
        parent_hash=Hash(bytes.fromhex("aa" * 32)),
        fee_recipient=Address(bytes.fromhex("bb" * 20)),
        state_root=Hash(bytes.fromhex("cc" * 32)),
        receipts_root=Hash(bytes.fromhex("dd" * 32)),
        logs_bloom=Bloom(bytes.fromhex("00" * 256)),
        prev_randao=Hash(bytes.fromhex("ee" * 32)),
        block_number=HexNumber(21_000_000),
        gas_limit=HexNumber(30_000_000),
        gas_used=HexNumber(21_000),
        timestamp=HexNumber(1_700_000_000),
        extra_data=Bytes(bytes.fromhex("dead")),
        base_fee_per_gas=HexNumber(10**18),
        block_hash=Hash(bytes.fromhex("ff" * 32)),
        transactions=list(TRANSACTIONS),
        withdrawals=[],
        blob_gas_used=HexNumber(131_072),
        excess_blob_gas=HexNumber(0),
        parent_beacon_block_root=Hash(bytes.fromhex("12" * 32)),
        # No block_access_list / slot_number / execution_requests for Cancun.
    )
    directive = FixtureRestPayload(
        payload=payload, expected_status=PayloadStatusV2.VALID
    )
    decoded = decode_bytes(ExecutionPayloadEnvelopeCancun, directive.to_ssz())
    assert int(decoded.payload.blob_gas_used) == 131_072
    assert bytes(decoded.parent_beacon_block_root) == bytes.fromhex("12" * 32)
    assert "block_access_list" not in decoded.payload.fields()


def test_payload_status_v2_has_no_invalid_block_hash() -> None:
    """
    ``INVALID_BLOCK_HASH`` is gone from the status enum (#793).

    Its absence is an assertion about the spec change, so guard it explicitly.
    """
    members = {member.value for member in PayloadStatusV2}
    assert members == {"VALID", "INVALID", "SYNCING", "ACCEPTED"}
    assert "INVALID_BLOCK_HASH" not in members


def test_format_name_is_registered() -> None:
    """The fixture format registers itself with the BaseFixture registry."""
    assert (
        BaseFixture.formats["blockchain_test_rest_ssz"]
        is BlockchainRestSszFixture
    )
