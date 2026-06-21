"""
Generate SSZ static test vectors for this package's containers.

Generated Vectors contain
* ``value.yaml``     -- the consensus-spec canonical value, as YAML,
* ``serialized.ssz`` -- its canonical SSZ byte encoding, **uncompressed**,
* ``roots.yaml``     -- its ``hash_tree_root``, as ``{root: "0x..."}``.
"""

import inspect
from pathlib import Path
from random import Random
from typing import Any, Dict, Iterator, List, Tuple, Type

import yaml
from remerkleable.complex import Container
from remerkleable.core import View

from .. import (
    EXECUTION_PAYLOAD_BY_FORK,
    RandomizationMode,
    containers,
    deterministic_seed,
    encode_bytes,
    encode_value,
    get_random_ssz_object,
    hash_tree_root,
)

Case = Tuple[str, str, int, Dict[str, Any]]

# Caps for variable-length fields.
MAX_LIST_LENGTH = 4
MAX_BYTES_LENGTH = 48

# Cases per changing (non-deterministic) mode. Deterministic modes get one.
RANDOM_CASE_COUNT = 3


_FORKS = tuple(EXECUTION_PAYLOAD_BY_FORK)


def _container_key(name: str) -> str:
    """
    Map a container class name to its on-disk handler path.
    """
    for fork in _FORKS:
        if name != fork and name.endswith(fork):
            return f"{name[: -len(fork)]}/{fork}"
    return name


def _discover_containers() -> Dict[str, Type[View]]:
    """
    Discover every SSZ ``Container`` defined in :mod:`..containers`.
    """
    found: Dict[str, Type[View]] = {}
    for name, cls in inspect.getmembers(containers, inspect.isclass):
        if (
            issubclass(cls, Container)
            and cls is not Container
            and cls.__module__ == containers.__name__
        ):
            found[_container_key(name)] = cls
    return dict(sorted(found.items()))

CONTAINERS: Dict[str, Type[View]] = _discover_containers()

_SUITES: List[Tuple[RandomizationMode, bool, int]] = [
    (mode, False, RANDOM_CASE_COUNT if mode.is_changing() else 1)
    for mode in RandomizationMode
] + [(RandomizationMode.mode_random, True, RANDOM_CASE_COUNT)]


def _suite_name(mode: RandomizationMode, chaos: bool) -> str:
    return f"ssz_{mode.to_name()}" + ("_chaos" if chaos else "")


def generate_case(
    container_name: str,
    ssz_type: Type[View],
    mode: RandomizationMode,
    chaos: bool,
    case_index: int,
) -> Dict[str, Any]:
    """
    Build a single ``{value, serialized, root}`` vector case.
    """
    seed = deterministic_seed(
        container_name,
        _suite_name(mode, chaos),
        case_index,
    )
    value = get_random_ssz_object(
        Random(seed),
        ssz_type,
        MAX_BYTES_LENGTH,
        MAX_LIST_LENGTH,
        mode,
        chaos=chaos,
    )
    return {
        "value": encode_value(value),
        "serialized": encode_bytes(value),
        "root": "0x" + hash_tree_root(value).hex(),
    }


def iter_cases() -> Iterator[Case]:
    """Yield ``(container, suite, case_index, case)`` for every vector."""
    for container_name, ssz_type in CONTAINERS.items():
        for mode, chaos, count in _SUITES:
            suite = _suite_name(mode, chaos)
            for case_index in range(count):
                yield (
                    container_name,
                    suite,
                    case_index,
                    generate_case(
                        container_name, ssz_type, mode, chaos, case_index
                    ),
                )


def case_dir(
    output_dir: Path,
    container_name: str,
    suite: str,
    case_index: int,
) -> Path:
    """Return the per-case output directory for a given case."""
    return output_dir / container_name / suite / f"case_{case_index}"


def _dump_yaml(obj: Any) -> str:
    return yaml.safe_dump(obj, default_flow_style=False, sort_keys=False)


def write_case(directory: Path, case: Dict[str, Any]) -> None:
    """Write a case's ``value.yaml``/``serialized.ssz``/``roots.yaml``."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "value.yaml").write_text(_dump_yaml(case["value"]))
    (directory / "serialized.ssz").write_bytes(case["serialized"])
    (directory / "roots.yaml").write_text(_dump_yaml({"root": case["root"]}))


def generate_all(output_dir: Path) -> int:
    """Write every vector case under ``output_dir``; return the count."""
    count = 0
    for container_name, suite, case_index, case in iter_cases():
        write_case(
            case_dir(output_dir, container_name, suite, case_index), case
        )
        count += 1
    return count


def main() -> None:
    """Regenerate the vectors in this directory."""
    output_dir = Path(__file__).parent
    written = generate_all(output_dir)
    print(f"wrote {written} vector cases to {output_dir}")


if __name__ == "__main__":
    main()
