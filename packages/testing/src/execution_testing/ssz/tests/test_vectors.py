"""
Self-tests for the SSZ vector generator.

The vectors themselves are *not* committed -- like the consensus-specs SSZ
static vectors and EEST's own fixtures, they are generated artifacts produced
on demand (and released), not checked into the source tree. So this guards the
generator instead of any committed files: it is deterministic, and every case
it emits is internally consistent (``value``/``serialized``/``root`` agree).
To write vectors to disk for a release, run::

    python -m execution_testing.ssz.vectors.generate
"""

from .. import decode_bytes, encode_bytes, from_json, hash_tree_root
from ..vectors.generate import CONTAINERS, iter_cases, serialize_case

CASES = list(iter_cases())


def test_generator_produces_cases() -> None:
    """Sanity: the generator actually produces cases."""
    assert CASES


def test_generation_is_deterministic() -> None:
    """Two independent generations are byte-identical (seeded determinism)."""
    again = [serialize_case(case) for _, _, _, case in iter_cases()]
    assert again == [serialize_case(case) for _, _, _, case in CASES]


def test_each_case_is_internally_consistent() -> None:
    """
    Every emitted case's three views agree.

    ``serialized`` decodes and re-encodes to itself, its ``hash_tree_root``
    equals ``root``, and the canonical-JSON ``value`` parses back to the same
    bytes. This is a self-test of the generator, not a check against an
    independent oracle (that would be circular; see ``vectors/README.md``).
    """
    for container_name, _, _, case in CASES:
        ssz_type = CONTAINERS[container_name]
        serialized = bytes.fromhex(case["serialized"][2:])
        decoded = decode_bytes(ssz_type, serialized)
        assert encode_bytes(decoded) == serialized, container_name
        assert "0x" + hash_tree_root(decoded).hex() == case["root"]
        assert encode_bytes(from_json(ssz_type, case["value"])) == serialized


def test_case_has_expected_keys() -> None:
    """Each generated case carries the documented top-level keys."""
    for _, _, _, case in CASES:
        assert {"meta", "value", "serialized", "root"} <= case.keys()
