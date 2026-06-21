"""
Fixture models for the REST+SSZ blockchain test format.

These pydantic models are the on-disk contract between ``fill`` (which emits
them) and ``consume`` (which reads them) for the REST+SSZ Engine API proposed
in execution-apis PR #793. This module is *only* the data definitions: there
is no fixture-generator logic and no consumer logic here, so a reviewer can
cross-check each field against the #793 spec table in isolation.

The single point where the pydantic world touches the SSZ world is
:meth:`FixtureRestPayload.to_ssz`, which calls the ``envelope_bytes`` adapter
re-exported from :mod:`execution_testing.ssz`. ``remerkleable`` is never
imported here; the SSZ library stays quarantined behind the ``ssz`` package.
"""

from enum import Enum
from functools import cached_property
from typing import Any, ClassVar, List

from pydantic import Field, computed_field, model_validator

from execution_testing.base_types import (
    Address,
    Alloc,
    Bloom,
    Bytes,
    CamelModel,
    Hash,
    HexNumber,
)
from execution_testing.forks import Amsterdam, Fork
from execution_testing.ssz import envelope_bytes

from .base import BaseFixture
from .blockchain import FixtureHeader


class PayloadStatusV2(str, Enum):
    """
    Status returned by the REST+SSZ ``newPayload`` endpoint (#793).

    NOTE: There is deliberately no ``INVALID_BLOCK_HASH`` member. PR #793
    removes that status from the enum -- a client that previously answered
    ``INVALID_BLOCK_HASH`` now answers plain ``INVALID``. Its absence here is
    an assertion about that spec change, not an oversight: do not re-add it to
    "match" the legacy JSON-RPC ``PayloadStatusEnum`` in
    :mod:`execution_testing.rpc.rpc_types`, which still carries it for the
    pre-#793 Engine API.
    """

    VALID = "VALID"
    INVALID = "INVALID"
    SYNCING = "SYNCING"
    ACCEPTED = "ACCEPTED"


class RestPayloadMutation(str, Enum):
    """
    Wire-level mutation applied to a valid payload for a transport negative
    test.

    Each member names a way to corrupt the request *envelope* (not its
    consensus contents) so the server is expected to reject it with an HTTP
    error before any consensus validation runs. The mutation logic itself
    lives in the consume plugin (a later PR); this enum only fixes the set of
    mutations the fixtures may reference.
    """

    TRUNCATE_BODY = "TRUNCATE_BODY"
    NONMONOTONIC_OFFSET = "NONMONOTONIC_OFFSET"
    WRONG_CONTENT_TYPE = "WRONG_CONTENT_TYPE"
    FORK_MISMATCH = "FORK_MISMATCH"


class FixtureRestWithdrawal(CamelModel):
    """A validator withdrawal inside a REST+SSZ execution payload."""

    index: HexNumber
    validator_index: HexNumber
    address: Address
    amount: HexNumber


class FixtureRestExecutionPayload(CamelModel):
    """
    A REST+SSZ ``ExecutionPayloadEnvelope`` in human-readable fixture form,
    fork-parameterized.

    ``fork`` (a registry key such as ``"Amsterdam"`` / ``"Cancun"``) selects
    the per-fork SSZ shape this represents; it is fixture metadata, not an SSZ
    field. The remaining fields are the union of every fork's payload and
    envelope fields, in canonical order, so a single model serves all forks.
    Fields a fork does not carry are left ``None``:

    * base fields (``parent_hash`` .. ``transactions``) -- every fork,
    * ``withdrawals`` -- Shanghai+,
    * ``blob_gas_used`` / ``excess_blob_gas`` -- Cancun+,
    * ``block_access_list`` / ``slot_number`` -- Amsterdam+,
    * ``parent_beacon_block_root`` (envelope) -- Cancun+,
    * ``execution_requests`` (envelope) -- Prague+.

    The container actually built for ``fork`` is chosen from the registries in
    :mod:`execution_testing.ssz`, which include only the fields that fork
    declares; supplying a field a fork lacks is harmless, omitting one it needs
    raises. The drift round-trip test fails loudly if this model and the
    remerkleable container diverge for a fork.
    """

    fork: str
    parent_hash: Hash
    fee_recipient: Address
    state_root: Hash
    receipts_root: Hash
    logs_bloom: Bloom
    prev_randao: Hash
    block_number: HexNumber
    gas_limit: HexNumber
    gas_used: HexNumber
    timestamp: HexNumber
    extra_data: Bytes
    base_fee_per_gas: HexNumber
    block_hash: Hash
    transactions: List[Bytes]
    withdrawals: List[FixtureRestWithdrawal] | None = None
    blob_gas_used: HexNumber | None = None
    excess_blob_gas: HexNumber | None = None
    block_access_list: Bytes | None = Field(
        None, description="RLP-serialized EIP-7928 Block Access List"
    )
    slot_number: HexNumber | None = None
    parent_beacon_block_root: Hash | None = None
    execution_requests: List[Bytes] | None = None


class FixtureRestPayload(CamelModel):
    """
    A single ``newPayload`` directive in a REST+SSZ blockchain test.

    Carries the execution payload, the expected :class:`PayloadStatusV2`
    response, and -- for ``INVALID`` cases -- an optional ``validationError``
    string. It deliberately does *not* carry ``expectedBlobVersionedHashes``
    (removed in #793) and there is no field for an ``INVALID_BLOCK_HASH``
    verdict (removed from the status enum).
    """

    payload: FixtureRestExecutionPayload
    expected_status: PayloadStatusV2
    validation_error: str | None = Field(None)

    @model_validator(mode="before")
    @classmethod
    def _strip_ssz_computed_field(cls, data: Any) -> Any:
        """
        Drop the ``ssz`` computed field when re-reading a fixture from disk.

        ``ssz`` is emitted for human inspection but is not an input field;
        without this the ``extra="forbid"`` config rejects round-tripped
        fixtures.
        """
        if isinstance(data, dict):
            data.pop("ssz", None)
        return data

    def to_ssz(self) -> bytes:
        """
        Return the SSZ-encoded ``ExecutionPayloadEnvelope`` wire bytes.

        The one place the pydantic layer crosses into SSZ: it forwards the
        payload's field values (and its fork) to the fork-parameterized
        ``envelope_bytes`` adapter and returns the raw bytes. Keep this thin --
        no logic beyond the call-through. The consume layer uses these bytes;
        the fixture's stored ``ssz`` hex is only for inspection.
        """
        p = self.payload
        return envelope_bytes(
            p.fork,
            parent_hash=p.parent_hash,
            fee_recipient=p.fee_recipient,
            state_root=p.state_root,
            receipts_root=p.receipts_root,
            logs_bloom=p.logs_bloom,
            prev_randao=p.prev_randao,
            block_number=p.block_number,
            gas_limit=p.gas_limit,
            gas_used=p.gas_used,
            timestamp=p.timestamp,
            extra_data=p.extra_data,
            base_fee_per_gas=p.base_fee_per_gas,
            block_hash=p.block_hash,
            transactions=p.transactions,
            withdrawals=(
                None
                if p.withdrawals is None
                else [w.model_dump() for w in p.withdrawals]
            ),
            blob_gas_used=p.blob_gas_used,
            excess_blob_gas=p.excess_blob_gas,
            block_access_list=p.block_access_list,
            slot_number=p.slot_number,
            parent_beacon_block_root=p.parent_beacon_block_root,
            execution_requests=p.execution_requests,
        )

    @computed_field  # type: ignore[prop-decorator]
    @cached_property
    def ssz(self) -> Bytes:
        """SSZ wire bytes as a hex string, stored for human inspection."""
        return Bytes(self.to_ssz())


class FixtureRestNegative(CamelModel):
    """
    A transport-only negative directive: a wire-level error, not a consensus
    verdict.

    Unlike :class:`FixtureRestPayload`, whose expected outcome is a
    consensus :class:`PayloadStatusV2`, the expected outcome here is an HTTP
    error code. A valid base payload is corrupted per ``mutation`` and the
    server is expected to answer with ``expected_http_status`` before reaching
    consensus validation. That difference in outcome -- HTTP code vs. consensus
    status -- is the whole reason this is a separate model.

    Speculative until the consume plugin implements the mutation logic: the
    mutation set is sketched ahead of its consumer from the known negative
    vectors, since adding a mutation variant later is cheaper than reshaping
    the model.
    """

    payload: FixtureRestExecutionPayload
    mutation: RestPayloadMutation
    expected_http_status: int


class BlockchainRestSszFixture(BaseFixture):
    """Top-level REST+SSZ blockchain test fixture."""

    format_name: ClassVar[str] = "blockchain_test_rest_ssz"
    description: ClassVar[str] = (
        "Tests that generate a blockchain test fixture for the REST+SSZ "
        "Engine API."
    )

    fork: Fork = Field(..., alias="network")
    pre: Alloc
    genesis: FixtureHeader = Field(..., alias="genesisBlockHeader")
    payloads: List[FixtureRestPayload] = Field(..., alias="restPayloads")
    last_forkchoice_head: Hash
    """
    Head the forkchoice settles on after the final payload.

    Typed as a plain :class:`Hash` for now. Its semantics depend on the
    still-unresolved forkchoice-atomicity question in #793: if forkchoice
    stays atomic with ``newPayload`` this single hash suffices, but if it
    splits into a separate payload-attributes call this field's shape will
    need to change. Treat the shape as provisional until that settles.
    """

    def get_fork(self) -> Fork | None:
        """Return the fixture's fork."""
        return self.fork

    @classmethod
    def supports_fork(cls, fork: Fork) -> bool:
        """
        Return whether the fixture can be generated for ``fork``.

        The models and the SSZ bridge are fork-parameterized (every payload
        fork has a container), but the REST+SSZ Engine API itself is introduced
        by PR #793 at Amsterdam, so generation is gated there. Lower this bound
        if/when earlier-fork REST+SSZ endpoints become testable -- no model
        change is required.
        """
        return fork >= Amsterdam
