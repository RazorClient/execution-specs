"""Tests for the consensus-spec canonical JSON mapping."""

from ..containers import ExecutionPayloadAmsterdam, Withdrawal
from ..json_mapping import from_json, to_json
from .test_containers import _payload, _withdrawal


def test_integers_serialize_as_decimal_strings() -> None:
    """
    Unsigned integers become decimal strings, not hex.

    This is the consensus-spec convention and differs from eth JSON-RPC, where
    quantities are hex.
    """
    obj = to_json(_payload())
    assert obj["block_number"] == "21000000"
    assert obj["gas_limit"] == "30000000"
    # `base_fee_per_gas` is a uint256; it must also be a plain decimal string,
    # not the little-endian hex that `remerkleable.to_obj()` would emit.
    assert obj["base_fee_per_gas"] == str(10**18)


def test_byte_fields_serialize_as_lowercase_0x_hex() -> None:
    """Byte vectors and lists become lowercase ``0x``-prefixed hex."""
    obj = to_json(_payload())
    assert obj["parent_hash"] == "0x" + "aa" * 32
    assert obj["fee_recipient"] == "0x" + "bb" * 20
    assert obj["extra_data"] == "0xdead"
    assert obj["transactions"] == [
        "0x02f86b01",
        "0x" + "01" * 21,
        "0x" + "03" * 5,
    ]


def test_field_names_are_snake_case() -> None:
    """Field names match the container definitions verbatim (snake_case)."""
    obj = to_json(_payload())
    assert "block_number" in obj
    assert "blockNumber" not in obj


def test_withdrawal_json_round_trip() -> None:
    """to_json -> from_json reconstructs an equal withdrawal."""
    value = _withdrawal()
    assert from_json(Withdrawal, to_json(value)) == value


def test_payload_json_round_trip() -> None:
    """to_json -> from_json reconstructs an equal payload."""
    value = _payload()
    assert from_json(ExecutionPayloadAmsterdam, to_json(value)) == value
