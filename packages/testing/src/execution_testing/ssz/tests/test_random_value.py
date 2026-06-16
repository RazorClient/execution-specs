"""Property tests for the deterministic random SSZ value generator."""

from random import Random
from typing import Any

import pytest

from .. import decode_bytes, encode_bytes
from ..containers import (
    ExecutionPayloadAmsterdam,
    ExecutionPayloadEnvelopeAmsterdam,
    Withdrawal,
)
from ..random_value import (
    RandomizationMode,
    deterministic_seed,
    get_random_ssz_object,
)

CONTAINERS = [
    Withdrawal,
    ExecutionPayloadAmsterdam,
    ExecutionPayloadEnvelopeAmsterdam,
]

MAX_BYTES_LENGTH = 48
MAX_LIST_LENGTH = 4


def _value(
    ssz_type: Any,
    mode: RandomizationMode,
    seed: int = 0,
    chaos: bool = False,
) -> Any:
    return get_random_ssz_object(
        Random(seed),
        ssz_type,
        MAX_BYTES_LENGTH,
        MAX_LIST_LENGTH,
        mode,
        chaos,
    )


def test_deterministic_seed_is_stable_and_not_pythons_hash() -> None:
    """The seed depends only on its parts, not on process-salted hashing."""
    assert deterministic_seed("a", "b", 1) == deterministic_seed("a", "b", 1)
    assert deterministic_seed("a", "b", 1) != deterministic_seed("a", "b", 2)


def test_is_changing_matches_upstream() -> None:
    """``random``/``one_count``/``max_count`` change."""
    changing = {
        RandomizationMode.mode_random,
        RandomizationMode.mode_one_count,
        RandomizationMode.mode_max_count,
    }
    for mode in RandomizationMode:
        assert mode.is_changing() == (mode in changing), mode


@pytest.mark.parametrize("ssz_type", CONTAINERS)
@pytest.mark.parametrize("mode", list(RandomizationMode))
def test_same_seed_yields_identical_value(
    ssz_type: Any, mode: RandomizationMode
) -> None:
    """A fixed seed reproduces the exact same value."""
    assert encode_bytes(_value(ssz_type, mode, seed=1234)) == encode_bytes(
        _value(ssz_type, mode, seed=1234)
    )


@pytest.mark.parametrize("ssz_type", CONTAINERS)
@pytest.mark.parametrize("mode", list(RandomizationMode))
def test_generated_value_round_trips(
    ssz_type: Any, mode: RandomizationMode
) -> None:
    """Every generated value survives encode -> decode unchanged."""
    value = _value(ssz_type, mode, seed=7)
    assert decode_bytes(ssz_type, encode_bytes(value)) == value


def test_zero_mode_zeroes_scalars_and_byte_vectors() -> None:
    """``zero`` mode zeroes scalars and byte vectors."""
    payload = _value(ExecutionPayloadAmsterdam, RandomizationMode.mode_zero)
    assert int(payload.block_number) == 0
    assert bytes(payload.parent_hash) == b"\x00" * 32
    # A zero-mode ``ByteList`` is a single zero byte (``min(1, limit)``), not
    # empty.
    assert bytes(payload.extra_data) == b"\x00"


def test_max_mode_saturates_scalars_and_byte_vectors() -> None:
    """``max`` mode maxes scalars and byte vectors."""
    payload = _value(ExecutionPayloadAmsterdam, RandomizationMode.mode_max)
    assert int(payload.block_number) == 2**64 - 1
    assert bytes(payload.parent_hash) == b"\xff" * 32
    # A max-mode ``ByteList`` is a single ``0xff`` byte (``min(1, limit)``).
    assert bytes(payload.extra_data) == b"\xff"


def test_nil_count_empties_collections() -> None:
    """``nil_count`` empties every variable-length collection."""
    payload = _value(
        ExecutionPayloadAmsterdam, RandomizationMode.mode_nil_count
    )
    assert len(payload.transactions) == 0
    assert len(payload.withdrawals) == 0
    assert bytes(payload.extra_data) == b""


def test_one_count_yields_single_element_collections() -> None:
    """``one_count`` puts exactly one element in each collection."""
    payload = _value(
        ExecutionPayloadAmsterdam, RandomizationMode.mode_one_count
    )
    assert len(payload.transactions) == 1
    assert len(payload.withdrawals) == 1
    assert len(bytes(payload.extra_data)) == 1


def test_max_count_fills_collections_to_cap() -> None:
    """``max_count`` fills collections to the cap."""
    payload = _value(
        ExecutionPayloadAmsterdam, RandomizationMode.mode_max_count
    )
    assert len(payload.transactions) == MAX_LIST_LENGTH
    assert len(payload.withdrawals) == MAX_LIST_LENGTH

    assert len(bytes(payload.extra_data)) == 32


def test_random_mode_changes_with_seed() -> None:
    """``random`` mode produces different values for different seeds."""
    a = encode_bytes(
        _value(ExecutionPayloadAmsterdam, RandomizationMode.mode_random, 1)
    )
    b = encode_bytes(
        _value(ExecutionPayloadAmsterdam, RandomizationMode.mode_random, 2)
    )
    assert a != b


def test_chaos_runs_and_round_trips() -> None:
    """``chaos`` re-rolls the mode per node; the result still round-trips."""
    value = _value(
        ExecutionPayloadAmsterdam,
        RandomizationMode.mode_random,
        seed=99,
        chaos=True,
    )
    assert (
        decode_bytes(ExecutionPayloadAmsterdam, encode_bytes(value)) == value
    )
