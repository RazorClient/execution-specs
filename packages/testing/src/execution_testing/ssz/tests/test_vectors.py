"""
Self-tests for the SSZ vector generator.
"""

from pathlib import Path

import yaml

from .. import decode_bytes, decode_value, encode_bytes, hash_tree_root
from ..vectors.generate import (
    CONTAINERS,
    case_dir,
    iter_cases,
    write_case,
)

CASES = list(iter_cases())


def test_generator_produces_cases() -> None:
    """Sanity: the generator actually produces cases."""
    assert CASES


def test_generation_is_deterministic() -> None:
    """Two independent generations are identical (seeded determinism)."""
    again = [case for _, _, _, case in iter_cases()]
    assert again == [case for _, _, _, case in CASES]


def test_each_case_is_internally_consistent() -> None:
    """
    ``serialized`` decodes and re-encodes to itself, its ``hash_tree_root``
    equals ``root``, and the canonical ``value`` parses back to the same
    bytes. This is a self-test of the generator, not a check against an
    independent oracle.
    """
    for container_name, _, _, case in CASES:
        ssz_type = CONTAINERS[container_name]
        serialized = case["serialized"]
        decoded = decode_bytes(ssz_type, serialized)
        assert encode_bytes(decoded) == serialized, container_name
        assert "0x" + hash_tree_root(decoded).hex() == case["root"]
        from_value = decode_value(ssz_type, case["value"])
        assert encode_bytes(from_value) == serialized


def test_case_has_expected_keys() -> None:
    """Each generated case carries exactly the documented keys."""
    for _, _, _, case in CASES:
        assert set(case) == {"value", "serialized", "root"}


def test_write_case_emits_three_files(tmp_path: Path) -> None:
    """``write_case`` writes the ssz_static three-file layout, uncompressed."""
    container_name, suite, case_index, case = CASES[0]
    directory = case_dir(tmp_path, container_name, suite, case_index)
    write_case(directory, case)

    assert (directory / "serialized.ssz").read_bytes() == case["serialized"]
    assert (
        yaml.safe_load((directory / "value.yaml").read_text())
        == (case["value"])
    )
    assert yaml.safe_load((directory / "roots.yaml").read_text()) == {
        "root": case["root"]
    }
