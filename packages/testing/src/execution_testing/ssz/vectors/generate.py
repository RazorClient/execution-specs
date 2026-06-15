"""
Generate cross-client SSZ static test vectors for this package's containers.

For every registered container, for every :class:`RandomizationMode`, this
emits one or more cases of the form ``{value, serialized, root}`` -- the same
shape the consensus-specs SSZ static tests use:

* ``value``      -- the consensus-spec canonical JSON of the object,
* ``serialized`` -- its canonical SSZ byte encoding, ``0x``-hex,
* ``root``       -- its ``hash_tree_root``, ``0x``-hex.

These are *reference* vectors: ``remerkleable`` is the producing reference,
exactly as the consensus-specs ``spec`` module is for the beacon vectors. They
are meant for independent client implementations to check their own SSZ
encoders against, and are deliberately **not** consumed by this package's own
correctness tests -- doing so would be circular (see ``README.md``).

The vectors are a generated artifact (released, not committed), mirroring the
consensus-specs SSZ static vectors and EEST's own fixtures. Run as a module to
write them to disk for a release; do not commit the output::

    python -m execution_testing.ssz.vectors.generate
"""

import json
from pathlib import Path
from random import Random
from typing import Any, Dict, Iterator, Tuple, Type

from remerkleable.core import View

from .. import (
    EXECUTION_PAYLOAD_BY_FORK,
    EXECUTION_PAYLOAD_ENVELOPE_BY_FORK,
    REFERENCE_SPEC_VERSION,
    RandomizationMode,
    deterministic_seed,
    encode_bytes,
    get_random_ssz_object,
    hash_tree_root,
    to_json,
)
from ..containers import Withdrawal

# One generated vector: ``(container, mode, case_index, case)``.
Case = Tuple[str, RandomizationMode, int, Dict[str, Any]]

# The SSZ size-limit preset. The consensus-specs ``minimal`` and ``mainnet``
# presets are byte-identical for these execution-payload limits (see
# ``constants.py``), so a single preset axis is emitted. The *fork* is a
# separate axis, encoded in the on-disk container name below.
PRESET = "mainnet"

# Caps for variable-length fields. The declared SSZ capacities (e.g. 2**30
# bytes per transaction) cannot be materialized; these keep cases small while
# still exercising offset tables and partial/empty/full collections.
MAX_LIST_LENGTH = 4
MAX_BYTES_LENGTH = 48

# Cases per changing (non-deterministic) mode. Deterministic modes get one.
RANDOM_CASE_COUNT = 3

# The containers to generate vectors for, keyed by the on-disk path. The
# payload and envelope are emitted per fork from the registries (one directory
# per fork); ``Withdrawal`` is fork-independent.
CONTAINERS: Dict[str, Type[View]] = {
    "Withdrawal": Withdrawal,
    **{
        f"ExecutionPayload/{fork}": cls
        for fork, cls in EXECUTION_PAYLOAD_BY_FORK.items()
    },
    **{
        f"ExecutionPayloadEnvelope/{fork}": cls
        for fork, cls in EXECUTION_PAYLOAD_ENVELOPE_BY_FORK.items()
    },
}


def generate_case(
    container_name: str,
    ssz_type: Type[View],
    mode: RandomizationMode,
    case_index: int,
) -> Dict[str, Any]:
    """
    Build a single ``{meta, value, serialized, root}`` vector case.

    The seed is derived from ``(spec version, preset, container, mode, case)``
    so the case is byte-for-byte reproducible. ``meta`` records the inputs so a
    consumer can regenerate and audit the case independently.
    """
    seed = deterministic_seed(
        REFERENCE_SPEC_VERSION,
        PRESET,
        container_name,
        mode.to_name(),
        case_index,
    )
    value = get_random_ssz_object(
        Random(seed),
        ssz_type,
        MAX_BYTES_LENGTH,
        MAX_LIST_LENGTH,
        mode,
        chaos=False,
    )
    return {
        "meta": {
            "container": container_name,
            "preset": PRESET,
            "spec_version": REFERENCE_SPEC_VERSION,
            "mode": mode.to_name(),
            "case": case_index,
            "max_list_length": MAX_LIST_LENGTH,
            "max_bytes_length": MAX_BYTES_LENGTH,
            "seed": f"0x{seed:064x}",
        },
        "value": to_json(value),
        "serialized": "0x" + encode_bytes(value).hex(),
        "root": "0x" + hash_tree_root(value).hex(),
    }


def iter_cases() -> Iterator[Case]:
    """Yield ``(container, mode, case_index, case)`` for every vector."""
    for container_name, ssz_type in CONTAINERS.items():
        for mode in RandomizationMode:
            count = RANDOM_CASE_COUNT if mode.is_changing() else 1
            for case_index in range(count):
                yield (
                    container_name,
                    mode,
                    case_index,
                    generate_case(container_name, ssz_type, mode, case_index),
                )


def case_path(
    output_dir: Path,
    container_name: str,
    mode: RandomizationMode,
    case_index: int,
) -> Path:
    """Return the on-disk path for a given case."""
    return (
        output_dir
        / container_name
        / mode.to_name()
        / f"case_{case_index}.json"
    )


def serialize_case(case: Dict[str, Any]) -> str:
    """Return the canonical on-disk JSON text for a case."""
    return json.dumps(case, indent=2) + "\n"


def generate_all(output_dir: Path) -> int:
    """
    Write every vector case under ``output_dir`` and return the case count.
    """
    count = 0
    for container_name, mode, case_index, case in iter_cases():
        path = case_path(output_dir, container_name, mode, case_index)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialize_case(case))
        count += 1
    return count


def main() -> None:
    """Regenerate the committed vectors in this directory."""
    output_dir = Path(__file__).parent
    written = generate_all(output_dir)
    print(f"wrote {written} vector cases to {output_dir}")


if __name__ == "__main__":
    main()
