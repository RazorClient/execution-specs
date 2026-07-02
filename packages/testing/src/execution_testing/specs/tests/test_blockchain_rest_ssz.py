"""
Generator tests for the REST+SSZ blockchain fixture format (PR-7).

The end-to-end test runs the real ``ExecutionSpecs`` t8n at Prague (the latest
fork the bundled t8n supports on this branch) to prove the
``make_rest_ssz_fixture`` pipeline and the ``from_fixture_header`` converter
work against headers a transition tool actually produces. A second, t8n-free
test covers the Amsterdam-only fields (``block_access_list``/``slot_number``),
which the bundled t8n cannot fill.
"""

from execution_testing.base_types import (
    Account,
    Address,
    Bytes,
    Hash,
    HexNumber,
)
from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures import (
    BlockchainRestSszFixture,
    FixtureRestExecutionPayload,
    FixtureRestPayload,
    PayloadStatusV2,
)
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.forks import Amsterdam, Prague
from execution_testing.test_types import Transaction

from ..blockchain import Block, BlockchainTest

# The default transaction sender; pre funds it so the blocks are valid.
SENDER = "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b"


def _transfer(nonce: int) -> Transaction:
    return Transaction(
        to=0x1000,
        value=1,
        gas_limit=100_000,
        nonce=nonce,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=1000,
    )


def test_make_rest_ssz_fixture_prague(default_t8n: TransitionTool) -> None:
    """A Prague BlockchainTest generates a valid REST+SSZ fixture e2e."""
    result = BlockchainTest(
        fork=Prague,
        pre={SENDER: Account(balance=10**18)},
        post={},
        blocks=[Block(txs=[_transfer(0)]), Block(txs=[_transfer(1)])],
    ).generate(t8n=default_t8n, fixture_format=BlockchainRestSszFixture)

    fixture = result.fixture
    assert isinstance(fixture, BlockchainRestSszFixture)
    assert len(fixture.payloads) == 2
    for directive in fixture.payloads:
        assert directive.expected_status == PayloadStatusV2.VALID
        assert directive.validation_error is None
        assert directive.payload.fork == "Prague"
        # Full field-mapping check: building the SSZ envelope must not raise
        # (envelope_bytes errors if any fork-required field is missing).
        assert len(bytes(directive.ssz)) > 0
        # Prague carries requests but not the Amsterdam-only fields.
        assert directive.payload.execution_requests is not None
        assert directive.payload.block_access_list is None
        assert directive.payload.slot_number is None
    assert (
        fixture.last_forkchoice_head == fixture.payloads[-1].payload.block_hash
    )


def test_make_rest_ssz_fixture_amsterdam(default_t8n: TransitionTool) -> None:
    """An Amsterdam fill produces a fixture carrying every payload field."""
    result = BlockchainTest(
        fork=Amsterdam,
        pre={SENDER: Account(balance=10**18)},
        post={},
        blocks=[Block(txs=[_transfer(0)])],
    ).generate(t8n=default_t8n, fixture_format=BlockchainRestSszFixture)

    fixture = result.fixture
    assert isinstance(fixture, BlockchainRestSszFixture)
    assert len(fixture.payloads) == 1
    directive = fixture.payloads[0]
    payload = directive.payload
    assert directive.expected_status == PayloadStatusV2.VALID
    assert payload.fork == "Amsterdam"
    # Amsterdam carries every (now-optional) field; the transition tool fills
    # the block access list and slot number the SSZ envelope requires.
    assert payload.block_access_list is not None
    assert payload.slot_number is not None
    assert payload.execution_requests is not None
    assert payload.parent_beacon_block_root is not None
    # Building the Amsterdam SSZ envelope must not raise (drift guard).
    assert len(bytes(directive.ssz)) > 0


def test_from_fixture_header_amsterdam_fields() -> None:
    """The converter populates the Amsterdam-only fields and builds SSZ."""
    header = FixtureHeader(
        fork=Amsterdam,
        fee_recipient=Address(0),
        state_root=Hash(0),
        number=7,
        gas_limit=30_000_000,
        timestamp=1_700_000_000,
        extra_data=Bytes(b""),
        base_fee_per_gas=HexNumber(1000),
        withdrawals_root=Hash(0),
        blob_gas_used=HexNumber(0),
        excess_blob_gas=HexNumber(0),
        parent_beacon_block_root=Hash(0),
        requests_hash=Hash(0),
        block_access_list_hash=Hash(0),
        slot_number=HexNumber(9),
    )
    payload = FixtureRestExecutionPayload.from_fixture_header(
        fork=Amsterdam,
        header=header,
        transactions=[],
        withdrawals=[],
        requests=[Bytes(bytes.fromhex("00aa"))],
        block_access_list=Bytes(bytes.fromhex("c0de")),
    )

    assert payload.fork == "Amsterdam"
    assert payload.block_access_list == Bytes(bytes.fromhex("c0de"))
    assert payload.slot_number == HexNumber(9)  # taken from the header
    assert payload.execution_requests is not None
    assert payload.parent_beacon_block_root is not None

    # The strict model + envelope build is the drift guard: this raises if any
    # Amsterdam-required SSZ field went unmapped.
    directive = FixtureRestPayload(
        payload=payload, expected_status=PayloadStatusV2.VALID
    )
    assert len(bytes(directive.ssz)) > 0
